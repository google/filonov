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

import argparse

import gaarf.cli.utils as gaarf_utils
from media_tagging import repository as media_tagging_repository
from media_tagging import tagger

from media_similarity import media_similarity_service

AVAILABLE_TAGGERS = list(tagger.TAGGERS.keys())


def main():  # noqa: D103
  parser = argparse.ArgumentParser()
  parser.add_argument(
    'media_paths', nargs='*', help='Paths to local/remote files or URLs'
  )
  parser.add_argument(
    '--tagger',
    dest='tagger_type',
    help=f'Tagger type, on of the following: {AVAILABLE_TAGGERS}',
  )
  args, kwargs = parser.parse_known_args()

  gaarf_utils.init_logging(logger_type='rich')
  media_tagger = tagger.create_tagger(args.tagger_type)
  tagging_repository = media_tagging_repository.PickleTaggingResultsRepository()
  tagging_results = media_tagger.tag_media(
    media_paths=args.media_paths,
    parallel_threshold=0,
    persist_repository=tagging_repository,
  )
  clustering_results = media_similarity_service.cluster_media(tagging_results)
  print(clustering_results.clusters)


if __name__ == '__main__':
  main()
