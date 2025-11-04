# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Cloud Function 'media_tagging'."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, g-importing-member
import base64
import io
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import functions_framework
import google.cloud.logging
import smart_open
from google.cloud import storage
from google.cloud.logging.handlers import CloudLoggingHandler
from media_tagging import MediaTaggingRequest, MediaTaggingService
from media_tagging.taggers.base import TaggingOptions

LOGGER_NAME = 'media_tagger'
_cloud_logging_configured = False


class GCSLoggingHandler(logging.Handler):
  """A logging handler that buffers logs and writes them to a GCS on close."""

  def __init__(self, gcs_path: str):
    super().__init__()
    self.gcs_path = gcs_path
    self.log_stream = io.StringIO()

  def emit(self, record):
    msg = self.format(record)
    self.log_stream.write(msg + '\n')

  def close(self):
    # When the handler is closed, write the buffer to GCS
    log_content = self.log_stream.getvalue()
    self.log_stream.close()
    if log_content:
      with smart_open.open(self.gcs_path, 'w') as f:
        f.write(log_content)
    super().close()


def _setup_cloud_logging():
  """Initializes Cloud Logging if it hasn't been already."""
  global _cloud_logging_configured
  if _cloud_logging_configured:
    return

  client = google.cloud.logging.Client()
  handler = CloudLoggingHandler(client, name=LOGGER_NAME)
  # The log level will be set overwritten in the main function.
  logging.getLogger().setLevel(logging.INFO)
  logging.getLogger().addHandler(handler)
  _cloud_logging_configured = True


def _update_status(output_gcs_folder: str, job_id: str, status: str):
  """Updates the status file on GCS."""
  status_file_path = f"{output_gcs_folder.rstrip('/')}/{job_id}.status"
  with smart_open.open(status_file_path, 'w') as f:
    f.write(status)
  logging.info("Updated status for job '%s' to '%s'", job_id, status)


def _validate_gcs_path(path: str, param_name: str):
  """Raises ValueError if the path is not a valid GCS path."""
  if not path or not path.startswith('gs://'):
    raise ValueError(f"Invalid GCS path for {param_name}: '{path}'. "
                     "Path must be a non-empty string starting with 'gs://'.")


def _get_request_param(request_json: Dict[str, Any],
                       param_name: str,
                       is_optional: bool = False) -> Any:
  """Extracts a parameter from the request."""
  param_value = request_json.get(param_name)
  if not param_value and not is_optional:
    raise ValueError(f'Missing mandatory parameter: {param_name}')
  return param_value


def _get_asset_paths(asset_ids: List[str], assets_gcs_folder: str) -> List[str]:
  """Constructs full GCS paths from a list of asset IDs.

  It constructs full GCS paths, and filters for existing files in the given GCS
  folder (non-recursive). It supports asset_ids with and without file
  extensions.

  Returns:
    list of GCS file paths
  """
  logging.info('Getting asset paths from %s', assets_gcs_folder)
  if not asset_ids:
    return []

  storage_client = storage.Client()
  bucket_name, prefix = assets_gcs_folder.replace('gs://', '').split('/', 1)
  if not prefix.endswith('/'):
    prefix += '/'

  bucket = storage_client.bucket(bucket_name)

  # List blobs non-recursively to avoid picking up files from subdirectories.
  # The original implementation was recursive and could lead to incorrect
  # matches if multiple files with the same name exist in different subfolders.
  blobs = bucket.list_blobs(prefix=prefix, delimiter='/')

  # Create lookups for both full filenames and stems
  gcs_blobs_by_name = {}
  gcs_blobs_by_stem = {}
  for blob in blobs:
    blob_path = Path(blob.name)
    # blob_path.name is the filename with extension, e.g. 'video.mp4'
    gcs_blobs_by_name[blob_path.name] = blob.name
    # blob_path.stem is the filename without extension, e.g. 'video'
    gcs_blobs_by_stem[blob_path.stem] = blob.name

  asset_paths = []
  for asset_id in asset_ids:
    blob_name = None
    # Give precedence to full name match
    if asset_id in gcs_blobs_by_name:
      blob_name = gcs_blobs_by_name[asset_id]
    elif asset_id in gcs_blobs_by_stem:
      blob_name = gcs_blobs_by_stem[asset_id]

    if blob_name:
      asset_paths.append(f'gs://{bucket_name}/{blob_name}')
    else:
      logging.warning(
          "Asset ID '%s' not found in GCS folder '%s'",
          asset_id,
          assets_gcs_folder,
      )

  return asset_paths


@functions_framework.http
def main(request):
  """A Cloud Function for wrapping the media_tagging library.

  It supports both HTTP and Pub/Sub triggers with the single entrypoint.
  """
  _setup_cloud_logging()

  if request.data and 'message' in (request_json :=
                                    request.get_json(silent=True) or {}):
    logging.info('Processing Pub/Sub message')
    # Pub/Sub call
    data = base64.b64decode(request_json['message']['data']).decode('utf-8')
    logging.info('Decoded payload: %s', data)
    payload = json.loads(data)
  else:
    logging.info('Processing HTTP request')
    # HTTP call
    payload = request.get_json(silent=True)

  # Determine log level from request payload, then environment variable,
  # then default to INFO.
  log_level_name = None
  if payload and isinstance(payload, dict):
    log_level_name = payload.get('log_level')

  if not log_level_name:
    log_level_name = os.environ.get('LOG_LEVEL')

  if not isinstance(log_level_name, str) or not log_level_name:
    log_level_name = 'INFO'

  # Set the log level.
  log_level = getattr(logging, log_level_name.upper(), logging.INFO)
  logging.getLogger().setLevel(log_level)

  if not payload:
    logging.error('Invalid request: No payload')
    return 'Invalid request: No payload', 400

  logging.info('Payload: %s', payload)

  job_id = None
  gcs_log_handler = None
  output_gcs_folder = None

  try:
    asset_ids = _get_request_param(payload, 'asset_ids')
    assets_gcs_folder = _get_request_param(payload, 'assets_gcs_folder')
    tagging_mode = _get_request_param(payload, 'tagging_mode')
    output_gcs_folder = _get_request_param(payload, 'output_gcs_folder')
    job_id = _get_request_param(payload, 'job_id', is_optional=True)
    custom_prompt_gcs_path = payload.get('custom_prompt_gcs_path')
    custom_prompt = payload.get('custom_prompt')
    custom_schema = payload.get('custom_schema')
    n_runs = payload.get('n_runs')
    media_type = (
        _get_request_param(payload, 'media_type', is_optional=True) or 'VIDEO')

    # Validate GCS paths before use
    _validate_gcs_path(assets_gcs_folder, 'assets_gcs_folder')
    _validate_gcs_path(output_gcs_folder, 'output_gcs_folder')
    if custom_prompt_gcs_path:
      _validate_gcs_path(custom_prompt_gcs_path, 'custom_prompt_gcs_path')

    if job_id:
      # Set up GCS logging and initial status
      log_file_path = f"{output_gcs_folder.rstrip(' / ')}/{job_id}.log"
      gcs_log_handler = GCSLoggingHandler(log_file_path)
      # Add a formatter to include timestamps in the GCS log file.
      formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
      gcs_log_handler.setFormatter(formatter)
      logging.getLogger().addHandler(gcs_log_handler)
      _update_status(output_gcs_folder, job_id, 'running')

    if tagging_mode not in ['describe', 'tag']:
      raise ValueError("Invalid tagging_mode. Must be 'describe' or 'tag'")

    # if no Gemini API key provided, we'll use Vertex AI backend
    use_vertexai = 'GEMINI_API_KEY' not in os.environ

    asset_paths = _get_asset_paths(asset_ids, assets_gcs_folder)
    logging.info('Found %d asset paths: %s', len(asset_paths), asset_paths)
    if not asset_paths:
      logging.warning('No valid assets found. Exiting.')
      if job_id:
        _update_status(output_gcs_folder, job_id, 'completed')
      return 'No valid assets found.', 200

    media_tagger = MediaTaggingService()

    if not custom_prompt and custom_prompt_gcs_path:
      with smart_open.open(custom_prompt_gcs_path, 'r') as f:
        custom_prompt = f.read()

    tagging_options = TaggingOptions(
        custom_prompt=custom_prompt,
        custom_schema=custom_schema,
        n_runs=n_runs,
        vertexai=use_vertexai)

    tagging_request = MediaTaggingRequest(
        media_paths=asset_paths,
        tagger_type='gemini',
        media_type=media_type,
        tagging_options=tagging_options,
    )

    logging.info('Running media_tagger with %d files: %s', len(asset_paths),
                 asset_paths)

    if tagging_mode == 'describe':
      result = media_tagger.describe_media(tagging_request)
    else:  # tagging_mode == 'tag'
      result = media_tagger.tag_media(tagging_request)

    logging.info('Media tagging completed.')
    output_file_name = f'{job_id}.json' if job_id else 'output.json'
    output_file_path = f"{output_gcs_folder.rstrip('/')}/{output_file_name}"

    logging.info('Saving result to %s', output_file_path)
    result.save(
        output_file_path, writer='json', destination_folder=output_gcs_folder)

    if job_id:
      _update_status(output_gcs_folder, job_id, 'completed')

    logging.info('Processing complete.')
    return f'Processing complete. Output saved to {output_file_path}', 200

  except Exception as e:
    logging.error('Error during processing: %s', e, exc_info=True)
    if job_id and output_gcs_folder:
      try:
        _update_status(output_gcs_folder, job_id, 'failed')
      except Exception as status_update_e:
        # Log the failure to update status, but don't crash the error handler
        logging.error(
            "CRITICAL: Failed to update job status to 'failed': %s",
            status_update_e,
        )
    return 'Internal Server Error', 500

  finally:
    if gcs_log_handler:
      gcs_log_handler.close()
      logging.getLogger().removeHandler(gcs_log_handler)
