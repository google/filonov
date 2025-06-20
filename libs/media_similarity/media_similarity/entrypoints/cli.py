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
"""CLI entrypoint for media clustering."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import argparse
import functools
import operator
import sys

import media_tagging
from garf_executors.entrypoints import utils as garf_utils
from garf_io import writer as garf_writer
from media_tagging import media
from media_tagging.entrypoints import utils as tagging_utils

import media_similarity


def main():  # noqa: D103
  parser = argparse.ArgumentParser()
  parser.add_argument(
    'action',
    nargs='?',
    choices=['cluster', 'search', 'compare'],
    help='Action to perform',
  )
  parser.add_argument(
    'media_paths', nargs='*', help='Paths to local/remote files or URLs'
  )
  parser.add_argument(
    '--input', dest='input', default=None, help='File with media_paths'
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
    default=None,
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
    help='Number of parallel processes to perform media similarity calculation',
  )
  parser.add_argument('--no-normalize', dest='normalize', action='store_false')
  parser.add_argument('-v', '--version', dest='version', action='store_true')
  parser.set_defaults(normalize=True)
  args, kwargs = parser.parse_known_args()

  if args.version:
    print(f'media-similarity version: {media_similarity.__version__}')
    sys.exit()
  garf_utils.init_logging(logger_type='rich')
  extra_parameters = garf_utils.ParamsParser([args.writer, 'input']).parse(
    kwargs
  )
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
  media_paths = args.media_paths or tagging_utils.get_media_paths_from_file(
    tagging_utils.InputConfig(path=args.input, **extra_parameters.get('input'))
  )
  writer_parameters = extra_parameters.get(args.writer) or {}
  writer = garf_writer.create_writer(args.writer, **writer_parameters)
  if args.action == 'cluster':
    request = media_similarity.MediaClusteringRequest(
      media_paths=media_paths,
      media_type=args.media_type,
      tagger_type=args.tagger,
      normalize=args.normalize,
    )
    if not request.tagger_type:
      tagging_results = tagging_service.get_media(
        media_type=request.tagger_type,
        media_paths=request.media_paths,
        output='tag',
      )
    else:
      tagging_results = tagging_service.tag_media(
        media_tagging.MediaTaggingRequest(
          tagger_type=request.tagger_type,
          media_type=request.media_type,
          media_paths=request.media_paths,
          deduplicate=True,
        )
      )
    clustering_results = similarity_service.cluster_media(
      tagging_results.results,
      normalize=args.normalize,
      parallel_threshold=args.parallel_threshold,
    )
    report = clustering_results.to_garf_report()

  elif args.action == 'compare':
    media_comparison_results = similarity_service.compare_media(
      media_similarity.MediaSimilarityComparisonRequest(
        media_paths=media_paths,
        media_type=args.media_type,
      )
    )
    report = functools.reduce(
      operator.add,
      [result.to_garf_report() for result in media_comparison_results],
    )
  elif args.action == 'search':
    similarity_search_results = similarity_service.find_similar_media(
      media_similarity.MediaSimilaritySearchRequest(
        media_paths=media_paths,
        media_type=args.media_type,
      )
    )
    report = functools.reduce(
      operator.add,
      [result.to_garf_report() for result in similarity_search_results],
    )
  writer.write(report, args.output)


if __name__ == '__main__':
  main()
