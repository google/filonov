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
from typing import get_args

import media_similarity
import media_tagging
from garf_executors.entrypoints import utils as gaarf_utils

from filonov import creative_map
from filonov.entrypoints import utils
from filonov.inputs import google_ads, queries, youtube

AVAILABLE_TAGGERS = list(media_tagging.TAGGERS.keys())


def main():  # noqa: D103
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--source',
    dest='source',
    choices=['googleads', 'file', 'youtube'],
    default='googleads',
    help='Which datasources to use for generating a map',
  )
  parser.add_argument(
    '--media-type',
    dest='media_type',
    choices=['IMAGE', 'VIDEO', 'YOUTUBE_VIDEO'],
    help='Type of media',
  )
  parser.add_argument(
    '--campaign-type',
    choices=['all', 'app', 'demandgen', 'pmax', 'video', 'display'],
    default='app',
    nargs='*',
    help='Type of campaign',
  )
  parser.add_argument(
    '--size-base',
    dest='size_base',
    help='Metric to base node sizes on',
  )
  parser.add_argument(
    '--db-uri',
    dest='db_uri',
    help='Database connection string to store and retrieve results',
  )
  parser.add_argument(
    '--output-name',
    dest='output_name',
    default='creative_map',
    help='Name of creative map (without an .html extension)',
  )
  parser.add_argument(
    '--output',
    dest='output',
    choices=['json', 'html'],
    default='json',
    help='Result of map generation',
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
  extra_parameters = gaarf_utils.ParamsParser([args.source, 'tagger']).parse(
    kwargs
  )
  source_parameters = extra_parameters.get(args.source)
  tagging_service = media_tagging.MediaTaggingService(
    tagging_results_repository=(
      media_tagging.repositories.SqlAlchemyTaggingResultsRepository(args.db_uri)
    )
  )

  media_type = args.media_type
  campaign_types = args.campaign_type
  if campaign_types == ['all']:
    campaign_types = get_args(queries.SupportedCampaignTypes)
  if args.source == 'youtube':
    request = utils.YouTubeChannelInputRequest(**source_parameters)
    extra_info = youtube.ExtraInfoFetcher(
      channel=request.channel
    ).generate_extra_info()
    media_paths = [info.media_path for info in extra_info.values()]
    tagging_results = tagging_service.tag_media(
      tagger_type=request.tagger,
      media_paths=media_paths,
      tagging_parameters=extra_parameters.get('tagger'),
      parallel_threshold=args.parallel_threshold,
      persist_repository=args.db_uri,
    )
  elif args.source == 'file':
    request = utils.FileInputRequest(**source_parameters)
    tagging_results = media_tagging.tagging_result.from_file(
      path=request.tagging_results_path,
      file_column_input=request.tagging_columns,
      media_type=media_type.lower(),
    )
    extra_info = google_ads.from_file(
      path=request.performance_results_path,
      media_type=media_type.lower(),
      with_size_base=args.size_base,
    )
  elif args.source == 'googleads':
    request = utils.GoogleAdsApiInputRequest(**source_parameters)
    fetching_request = google_ads.FetchingRequest(
      media_type=media_type,
      start_date=request.start_date,
      end_date=request.end_date,
      campaign_types=campaign_types,
    )
    extra_info = google_ads.ExtraInfoFetcher(
      accounts=request.account,
      ads_config=request.ads_config_path,
    ).generate_extra_info(fetching_request, args.size_base)
    media_paths = [info.media_path for info in extra_info.values()]
    tagging_results = tagging_service.tag_media(
      tagger_type=request.tagger,
      media_paths=media_paths,
      tagging_parameters=extra_parameters.get('tagger'),
      parallel_threshold=args.parallel_threshold,
    )
  clustering_results = media_similarity.MediaSimilarityService(
    media_similarity.repositories.SqlAlchemySimilarityPairsRepository(
      args.db_uri
    )
  ).cluster_media(
    tagging_results,
    normalize=args.normalize,
    custom_threshold=args.custom_threshold,
    parallel=args.parallel_threshold > 1,
    parallel_threshold=args.parallel_threshold,
  )
  generated_map = creative_map.CreativeMap.from_clustering(
    clustering_results, tagging_results, extra_info, request.to_dict()
  )
  output_name = args.output_name
  if args.output == 'json':
    with open(f'{output_name}.json', 'w', encoding='utf-8') as f:
      json.dump(generated_map.to_json(), f)
  elif args.output == 'html':
    generated_map.export_html(f'{output_name}.html')


if __name__ == '__main__':
  main()
