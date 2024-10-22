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
import pathlib

import gaarf.cli.utils as gaarf_utils
from media_similarity import media_similarity_service
from media_tagging import repository as media_tagging_repository
from media_tagging import tagger

from creative_maps import creative_map
from creative_maps.inputs import google_ads

AVAILABLE_TAGGERS = list(tagger.TAGGERS.keys())


def main():  # noqa: D103
  parser = argparse.ArgumentParser()
  parser.add_argument(
    'media_paths', nargs='*', help='Paths to local/remote files or URLs'
  )
  parser.add_argument(
    '--map-name',
    dest='map_name',
    default='creative_map',
    help='Name of creative map (without .html extension)',
  )
  parser.add_argument(
    '--account',
    dest='account',
    default=None,
    help='Google Ads Account / MCC',
  )
  parser.add_argument(
    '--start-date',
    dest='start_date',
    default=None,
    help='First date of fetching',
  )
  parser.add_argument(
    '--end-date',
    dest='end_date',
    default=None,
    help='Last date of fetching',
  )
  parser.add_argument(
    '--ads-config',
    dest='ads_config',
    default=str(pathlib.Path.home() / 'google-ads.yaml'),
    help='Path to google-ads.yaml',
  )
  parser.add_argument(
    '--output',
    dest='output',
    default='json',
    help='Result of map generation, one of "json", "file", "html"',
  )
  parser.add_argument(
    '--tagger',
    dest='tagger_type',
    help=f'Tagger type, on of the following: {AVAILABLE_TAGGERS}',
  )
  parser.add_argument(
    '--custom-threshold',
    dest='custom_threshold',
    default=None,
    type=float,
    help='Custom threshold of identifying similar media',
  )
  parser.add_argument(
    '--db-uri',
    dest='db_uri',
    help='Database connection string to store and retrieve tagging results',
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
  args = parser.parse_args()

  gaarf_utils.init_logging(loglevel='INFO', logger_type='rich')
  media_type = 'IMAGE' if 'vision-api' in args.tagger_type else 'YOUTUBE_VIDEO'
  extra_info = google_ads.ExtraInfoFetcher(
    accounts=args.account, ads_config=args.ads_config
  ).generate_extra_info(
    google_ads.FetchingRequest(
      media_type=media_type,
      start_date=args.start_date,
      end_date=args.end_date,
    )
  )
  media_tagger = tagger.create_tagger(args.tagger_type)
  media_paths = [info.media_path for info in extra_info.values()]
  tagging_repository = (
    media_tagging_repository.SqlAlchemyTaggingResultsRepository(args.db_uri)
  )
  tagging_results = media_tagger.tag_media(
    media_paths=media_paths,
    parallel_threshold=args.parallel_threshold,
    persist_repository=tagging_repository,
  )
  clustering_results = media_similarity_service.cluster_media(
    tagging_results,
    normalize=args.normalize,
    custom_threshold=args.custom_threshold,
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
