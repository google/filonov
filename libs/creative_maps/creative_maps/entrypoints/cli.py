# Copyright 2024 Google LLC
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
"""CLI entrypoint for generating creative map."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import argparse
import json

import gaarf.cli.utils as gaarf_utils
from media_similarity import media_similarity_service
from media_tagging import tagger, tagging_result

from creative_maps import creative_map
from creative_maps.entrypoints import utils
from creative_maps.inputs import google_ads

AVAILABLE_TAGGERS = list(tagger.TAGGERS.keys())


def main():  # noqa: D103
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--mode',
    dest='mode',
    choices=['api', 'file'],
    default='api',
    help='Which datasources to use for generating a map',
  )
  parser.add_argument(
    '--media-type',
    dest='media_type',
    choices=['IMAGE', 'VIDEO', 'YOUTUBE_VIDEO'],
    help='Type of media',
  )
  parser.add_argument(
    '--db-uri',
    dest='db_uri',
    help='Database connection string to store and retrieve results',
  )
  parser.add_argument(
    '--map-name',
    dest='map_name',
    default='creative_map',
    help='Name of creative map (without .html extension)',
  )
  parser.add_argument(
    '--output',
    dest='output',
    default='json',
    help='Result of map generation, one of "json", "file", "html"',
  )
  parser.add_argument(
    '--custom-threshold',
    dest='custom_threshold',
    default=None,
    type=float,
    help='Custom threshold of identifying similar media',
  )
  parser.add_argument(
    '--parallel-threshold',
    dest='parallel_threshold',
    default=10,
    type=int,
    help='Number of parallel processes to perform media tagging',
  )
  parser.add_argument('--no-normalize', dest='normalize', action='store_false')
  parser.set_defaults(normalize=True)
  args, kwargs = parser.parse_known_args()

  gaarf_utils.init_logging(loglevel='INFO', logger_type='rich')
  mode_parameters = (
    gaarf_utils.ParamsParser([args.mode]).parse(kwargs).get(args.mode)
  )

  media_type = args.media_type
  if args.mode == 'file':
    request = utils.FileInputRequest(**mode_parameters)
    tagging_results = tagging_result.from_file(
      path=request.tagging_results_path,
      file_column_input=request.tagging_columns,
      media_type=media_type.lower(),
    )
    extra_info = google_ads.from_file(
      path=request.performance_results_path,
      file_column_input=request.performance_columns,
      media_type=media_type.lower(),
    )
  elif args.mode == 'api':
    request = utils.ApiInputRequest(**mode_parameters)
    extra_info = google_ads.ExtraInfoFetcher(
      accounts=request.account,
      ads_config=request.ads_config_path,
    ).generate_extra_info(
      google_ads.FetchingRequest(
        media_type=media_type,
        start_date=request.start_date,
        end_date=request.end_date,
      )
    )
    media_tagger = tagger.create_tagger(request.tagger)
    media_paths = [info.media_path for info in extra_info.values()]
    tagging_results = media_tagger.tag_media(
      media_paths=media_paths,
      parallel_threshold=args.parallel_threshold,
      persist_repository=args.db_uri,
    )
  clustering_results = media_similarity_service.cluster_media(
    tagging_results,
    normalize=args.normalize,
    custom_threshold=args.custom_threshold,
    parallel=args.parallel_threshold > 1,
    parallel_threshold=args.parallel_threshold,
    persist_repository=args.db_uri,
  )
  generated_map = creative_map.CreativeMap.from_clustering(
    clustering_results, tagging_results, extra_info
  )
  map_name = args.map_name
  if args.output == 'file':
    generated_map.save(f'{map_name}.pickle')
  elif args.output == 'json':
    with open(f'{map_name}.json', 'w', encoding='utf-8') as f:
      json.dump(generated_map.to_json(), f)
  elif args.output == 'html':
    generated_map.export_html(f'{map_name}.html')


if __name__ == '__main__':
  main()
