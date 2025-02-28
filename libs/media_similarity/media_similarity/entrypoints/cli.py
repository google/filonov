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
"""CLI entrypoint for media clustering."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import argparse
import functools
import operator
import pprint
import sys

import media_tagging
from garf_executors.entrypoints import utils as garf_utils
from garf_io import writer as garf_writer
from media_tagging import media

import media_similarity

AVAILABLE_TAGGERS = list(media_tagging.TAGGERS.keys())


def main():  # noqa: D103
  parser = argparse.ArgumentParser()
  parser.add_argument(
    'action', nargs='?', choices=['cluster', 'search'], help='Action to perform'
  )
  parser.add_argument(
    'media_paths', nargs='*', help='Paths to local/remote files or URLs'
  )
  parser.add_argument(
    '--media-type',
    dest='media_type',
    choices=media.MediaTypeEnum.options(),
    default='UNKNOWN',
    help='Type of media.',
  )
  parser.add_argument(
    '--tagger',
    dest='tagger',
    choices=AVAILABLE_TAGGERS,
    help='Type of tagger',
  )
  parser.add_argument(
    '--db-uri',
    dest='db_uri',
    help='Database connection string to store and retrieve tagging results',
  )
  parser.add_argument('--writer', dest='writer', default='json')
  parser.add_argument('--output', dest='output', default='similarity_results')
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
    print(f'media-similarity version: {media_similarity.__version__}')
    sys.exit()
  garf_utils.init_logging(logger_type='rich')
  extra_parameters = garf_utils.ParamsParser([args.writer]).parse(kwargs)
  tagging_service = media_tagging.MediaTaggingService(
    tagging_results_repository=(
      media_tagging.repositories.SqlAlchemyTaggingResultsRepository(args.db_uri)
    ),
  )
  similarity_service = media_similarity.MediaSimilarityService(
    media_similarity_repository=(
      media_similarity.repositories.SqlAlchemySimilarityPairsRepository(
        args.db_uri
      )
    ),
  )
  if args.action == 'cluster':
    tagging_results = tagging_service.tag_media(
      tagger_type=args.tagger,
      media_type=args.media_type,
      media_paths=args.media_paths,
    )
    clustering_results = similarity_service.cluster_media(
      tagging_results, normalize=args.normalize
    )
    pprint.pprint(clustering_results.clusters)
  elif args.action == 'search':
    seed_media_identifiers = [
      media_tagging.media.convert_path_to_media_name(
        media_path,
        args.media_type,
      )
      for media_path in args.media_paths
    ]
    similarity_search_results = similarity_service.find_similar_media(
      seed_media_identifiers
    )
    report = functools.reduce(
      operator.add,
      [result.to_garf_report() for result in similarity_search_results],
    )
    writer_parameters = extra_parameters.get(args.writer) or {}
    garf_writer.create_writer(args.writer, **writer_parameters).write(
      report, args.output
    )


if __name__ == '__main__':
  main()
