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
import smart_open
from garf_executors.entrypoints import utils as gaarf_utils
from media_tagging import media

import filonov
from filonov.entrypoints import utils

AVAILABLE_TAGGERS = list(media_tagging.taggers.TAGGERS.keys())


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
    choices=media.MediaTypeEnum.options(),
    help='Type of media.',
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
    help='Name of output file',
  )
  parser.add_argument(
    '--custom-threshold',
    dest='custom_threshold',
    default=None,
    type=float,
    help='Custom threshold of identifying similar media',
  )
  parser.add_argument(
    '--trim-tags-threshold',
    dest='trim_tags_threshold',
    default=None,
    type=float,
    help='Min allowed score for tags',
  )
  parser.add_argument(
    '--parallel-threshold',
    dest='parallel_threshold',
    default=10,
    type=int,
    help='Number of parallel processes to perform media tagging',
  )
  parser.add_argument(
    '--loglevel',
    dest='loglevel',
    default='INFO',
    help='Log level',
  )
  parser.add_argument(
    '--logger',
    dest='logger',
    default='rich',
    choices=['local', 'rich'],
    help='Type of logger',
  )
  parser.add_argument('--normalize', dest='normalize', action='store_true')
  parser.add_argument('--no-normalize', dest='normalize', action='store_false')
  parser.add_argument('-v', '--version', dest='version', action='store_true')
  parser.set_defaults(normalize=False)
  args, kwargs = parser.parse_known_args()

  if args.version:
    print(f'filonov version: {filonov.__version__}')
    sys.exit()

  _ = gaarf_utils.init_logging(loglevel=args.loglevel, logger_type=args.logger)
  extra_parameters = gaarf_utils.ParamsParser([args.source, 'tagger']).parse(
    kwargs
  )
  tagging_service = media_tagging.MediaTaggingService(
    tagging_results_repository=(
      media_tagging.repositories.SqlAlchemyTaggingResultsRepository(args.db_uri)
    )
  )
  similarity_service = media_similarity.MediaSimilarityService(
    media_similarity.repositories.SqlAlchemySimilarityPairsRepository(
      args.db_uri
    )
  )
  tagger = args.tagger
  media_type = args.media_type
  if args.source == 'youtube':
    media_type = 'YOUTUBE_VIDEO'
    tagger = 'gemini'
  request = filonov.CreativeMapGenerateRequest(
    source=args.source,
    media_type=media_type,
    tagger=tagger,
    tagger_parameters=extra_parameters.get('tagger'),
    similarity_parameters={
      'normalize': args.normalize,
      'custom_threshold': args.custom_threshold,
    },
    input_parameters=extra_parameters.get(args.source),
    output_parameters=filonov.filonov_service.OutputParameters(
      output_name=args.output_name
    ),
    parallel_threshold=args.parallel_threshold,
    trim_tags_threshold=args.trim_tags_threshold,
  )
  generated_map = filonov.FilonovService(
    tagging_service, similarity_service
  ).generate_creative_map(args.source, request)
  destination = utils.build_creative_map_destination(
    request.output_parameters.output_name
  )
  with smart_open.open(destination, 'w', encoding='utf-8') as f:
    json.dump(generated_map.to_json(), f)


if __name__ == '__main__':
  main()
