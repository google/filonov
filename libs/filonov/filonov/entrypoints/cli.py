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
import sys

import media_similarity
import media_tagging
from garf_executors.entrypoints import utils as gaarf_utils

import filonov

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
    '--tagger',
    dest='tagger',
    choices=AVAILABLE_TAGGERS,
    default=None,
    help='Type of tagger',
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
  parser.add_argument('-v', '--version', dest='version', action='store_true')
  parser.set_defaults(normalize=True)
  args, kwargs = parser.parse_known_args()

  if args.version:
    print(f'filonov version: {filonov.__version__}')
    sys.exit()

  logger = gaarf_utils.init_logging(loglevel='INFO', logger_type='rich')
  extra_parameters = gaarf_utils.ParamsParser([args.source, 'tagger']).parse(
    kwargs
  )
  input_parameters = extra_parameters.get(args.source)
  media_type = args.media_type
  media_info, context = filonov.MediaInputService(
    args.source
  ).generate_media_info(media_type, input_parameters)
  if not media_info:
    logger.error('No performance data found')
    sys.exit()

  tagging_service = media_tagging.MediaTaggingService(
    tagging_results_repository=(
      media_tagging.repositories.SqlAlchemyTaggingResultsRepository(args.db_uri)
    )
  )
  if args.tagger is None:
    tagger = f'gemini-{media_type.lower()}'
  else:
    tagger = args.tagger

  tagging_results = tagging_service.tag_media(
    tagger_type=tagger,
    media_paths=media_info.keys(),
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
  generated_map = filonov.CreativeMap.from_clustering(
    clustering_results, tagging_results, media_info, context
  )
  with open(f'{args.output_name}.json', 'w', encoding='utf-8') as f:
    json.dump(generated_map.to_json(), f)


if __name__ == '__main__':
  main()
