# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

"""UI for generating creative map files."""

import datetime
import json
import os
import tempfile
from collections.abc import Sequence

import media_fetching
import media_similarity
import media_tagging
import smart_open
import streamlit as st
from pydantic_settings import BaseSettings

import filonov
from filonov import exceptions
from filonov.entrypoints import utils


class FilonovSettings(BaseSettings):
  """Specifies environmental variables for filonov.

  Ensure that mandatory variables are exposed via
  export ENV_VARIABLE_NAME=VALUE.

  Attributes:
    media_tagging_db_url: Connection string to DB with tagging results.
  """

  media_tagging_db_url: str | None = None


settings = FilonovSettings()


def streamlit_app():
  media_to_campaign_mapping = {
    'IMAGE': ['app', 'demandgen', 'pmax', 'display', 'search'],
    'TEXT': ['app', 'demandgen', 'pmax', 'display', 'search'],
    'YOUTUBE_VIDEO': ['app', 'demandgen', 'pmax'],
  }

  st.title('Creative Map Generator')

  source = st.selectbox(
    'Source', ['youtube', 'googleads', 'file', 'bq', 'sqldb', 'dbm']
  )

  with st.form('creative_map_form'):
    name = st.text_input('Name', 'creative_map')
    if source == 'googleads':
      tagger_type = st.selectbox('Tagger Type', ['gemini', 'google-cloud'])
      media_type = st.selectbox(
        'Media Type', ['IMAGE', 'YOUTUBE_VIDEO', 'TEXT']
      )
      account = st.text_input('Account', '')

      campaign_type = st.multiselect(
        'Campaign type', media_to_campaign_mapping.get(media_type)
      )

      col1, col2 = st.columns(2)
      with col1:
        start_date = st.date_input(
          'Start date: ',
          value=datetime.datetime.today() - datetime.timedelta(days=30),
        )
      with col2:
        end_date = st.date_input(
          'End date: ',
          value=datetime.datetime.today() - datetime.timedelta(days=1),
        )
        if end_date < start_date:
          st.error('End date cannot be less than start_date')
      extra_info = st.multiselect(
        'Extra info',
        [
          'googleads.main_geo',
          'googleads.approval_status',
          'tagging.language',
          'youtube.language',
        ],
      )
      input_parameters = {
        'account': account,
        'campaign_types': campaign_type,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'extra_info': extra_info,
      }
      if not os.getenv('GOOGLE_ADS_CONFIGURATION_FILE_PATH'):
        st.error(
          'Path to google-ads.yaml is not found in '
          'GOOGLE_ADS_CONFIGURATION_FILE_PATH environmental variable. '
          'Please expose it or add manually.'
        )
        ads_config_path = st.text_input('Path to google-ads.yaml', '')
        input_parameters.update({'ads_config': ads_config_path})

    elif source in ('bq', 'file', 'sqldb'):
      input_parameters = {}
      if source == 'bq':
        table = st.text_input('bq_table', '')
        input_parameters['table'] = table
      elif source == 'sqldb':
        table = st.text_input('sql_table', '')
        connection_string = st.text_input('connection_string', '')
        input_parameters['table'] = table
        input_parameters['connection_string'] = connection_string
      elif source == 'file':
        file_data = st.file_uploader(label='Path to file', type='csv')
        tmp_file_path = None
        if file_data:
          with tempfile.NamedTemporaryFile(
            delete=False, mode='w', suffix='.csv', encoding='utf-8'
          ) as f:
            f.write(file_data.getvalue().decode('utf-8'))
            tmp_file_path = f.name
        input_parameters['path'] = tmp_file_path
      tagger_type = st.selectbox('Tagger Type', ['gemini', 'google-cloud'])
      media_type = st.selectbox(
        'Media Type', ['IMAGE', 'YOUTUBE_VIDEO', 'TEXT']
      )

      media_path_column = st.text_input('Media path column name', 'media_url')
      media_name = st.text_input('Media column name', 'media_name')
      metrics = st.text_input('Metric columns', 'clicks,impressions')
      segments = st.text_input('Segment columns', '')
      input_parameters.update(
        {
          'media_identifier': media_path_column,
          'media_name': media_name,
          'metrics': metrics.split(','),
          'segments': segments.split(','),
        }
      )
    elif source == 'youtube':
      media_type = 'YOUTUBE_VIDEO'
      tagger_type = 'gemini'
      channel = st.text_input('YouTube Channel ID', '')
      input_parameters = {'channel': channel}
      if not os.getenv('GARF_YOUTUBE_DATA_API_KEY'):
        st.error(
          'Add GARF_YOUTUBE_DATA_API_KEY environmental variable '
          'to work with YouTube.'
        )
    elif source == 'dbm':
      media_type = 'YOUTUBE_VIDEO'
      tagger_type = 'gemini'
      advertiser = st.text_input('DV 360 Advertiser ID', '')
      input_parameters = {'advertiser': advertiser}
      if not os.getenv('GARF_BID_MANAGER_CREDENTIALS_FILE'):
        st.error(
          'Add GARF_BID_MANAGER_CREDENTIALS_FILE environmental variable '
          'to work with Bid Manager.'
        )
    else:
      raise exceptions.FilonovError(f'Unsupported source: {source}')
    if not settings.media_tagging_db_url:
      st.warning(
        'No tagging data is saved between runs. '
        'Add MEDIA_TAGGING_DB_URL environmental variable to save data.'
      )

    col1, col2 = st.columns(2)
    with col1:
      submitted = st.form_submit_button('Generate Creative Map')
    with col2:
      cli_command_submitted = st.form_submit_button('Generate CLI command')

    if cli_command_submitted:
      request = filonov.CreativeMapGenerateRequest(
        source=source,
        media_type=media_type,
        tagger=tagger_type,
        source_parameters=input_parameters,
        output_parameters=filonov.filonov_service.OutputParameters(
          output_name=name
        ),
      )
      cli_command = build_cli_command(request, settings.media_tagging_db_url)
      st.code(cli_command, language='bash', wrap_lines=True)

    if submitted:
      request = filonov.CreativeMapGenerateRequest(
        source=source,
        media_type=media_type,
        tagger=tagger_type,
        source_parameters=input_parameters,
        output_parameters=filonov.filonov_service.OutputParameters(
          output_name=name
        ),
      )
      with st.expander('Show CLI command'):
        cli_command = build_cli_command(request, settings.media_tagging_db_url)
        st.code(cli_command, language='bash', wrap_lines=True)
      if 'fetching_service' not in st.session_state:
        st.session_state['fetching_service'] = (
          media_fetching.MediaFetchingService(source)
        )
      if 'tagging_service' not in st.session_state:
        st.session_state['tagging_service'] = media_tagging.MediaTaggingService(
          media_tagging.repositories.SqlAlchemyTaggingResultsRepository(
            settings.media_tagging_db_url
          )
        )
      if 'similarity_service' not in st.session_state:
        st.session_state['similarity_service'] = (
          media_similarity.MediaSimilarityService(
            media_similarity_repository=(
              media_similarity.repositories.SqlAlchemySimilarityPairsRepository(
                settings.media_tagging_db_url
              )
            )
          )
        )
      generated_map = filonov.FilonovService(
        st.session_state['fetching_service'],
        st.session_state['tagging_service'],
        st.session_state['similarity_service'],
      ).generate_creative_map(request)
      destination = utils.build_creative_map_destination(
        request.output_parameters.output_name
      )
      with smart_open.open(destination, 'w', encoding='utf-8') as f:
        json.dump(generated_map.to_json(), f)

      st.success(f'Creative Map saved to {destination}!')


def build_cli_command(
  request: filonov.CreativeMapGenerateRequest, db: str | None
) -> str:
  command_template = (
    'filonov --source {source} \\\n'
    '\t--media-type {media_type} \\\n'
    '\t--tagger {tagger} \\\n'
    '{source_parameters} \\\n'
    '\t--output-name {output}'
  )
  source = request.source.value
  source_parameters = []
  for name, value in request.source_parameters.model_dump().items():
    if not value or name == 'media_type':
      continue
    if isinstance(value, str):
      source_parameters.append(f'\t--{source}.{name}={value}')
    elif isinstance(value, Sequence):
      value_concat = ','.join(value)
      source_parameters.append(f'\t--{source}.{name}={value_concat}')

  source_parameters = ' \\\n'.join(source_parameters)
  params = {
    'source': source,
    'media_type': request.media_type,
    'tagger': request.tagger,
    'output': request.output_parameters.output_name,
    'source_parameters': source_parameters,
  }
  non_db_command = command_template.format(**params).strip()
  if db:
    return f'{non_db_command} \\\n\t--db-uri {db}'
  return non_db_command


streamlit_app()
