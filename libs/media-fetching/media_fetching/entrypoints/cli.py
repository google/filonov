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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

"""CLI entrypoint for fetching media data."""

import argparse
import sys
from typing import get_args

from garf_executors.entrypoints import utils as garf_utils
from garf_io import writer
from media_tagging import media

import media_fetching
from media_fetching.sources import fetcher


def main():  # noqa: D103
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--source',
    dest='source',
    choices=get_args(media_fetching.sources.models.InputSource),
    default='googleads',
    help='Which datasources to use for fetching media data',
  )
  parser.add_argument(
    '--media-type',
    dest='media_type',
    choices=media.MediaTypeEnum.options(),
    help='Type of media.',
  )
  parser.add_argument(
    '--extra-info',
    dest='extra_info',
    default=None,
    help=(
      'Comma separated modules to add extra information to fetched data '
      'specified in "module.method" format'
    ),
  )
  parser.add_argument(
    '--writer',
    dest='writer',
    default='json',
    help='Type of writer used to write resulting report.',
  )
  parser.add_argument(
    '--output',
    dest='output',
    default='media_results',
    help='Destination of written report.',
  )
  parser.add_argument('-v', '--version', dest='version', action='store_true')
  args, kwargs = parser.parse_known_args()

  if args.version:
    print(f'media-fetcher version: {media_fetching.__version__}')
    sys.exit()

  supported_enrichers = (
    media_fetching.enrichers.enricher.AVAILABLE_MODULES.keys()
  )
  parsed_param_keys = set(
    [args.source, args.writer] + list(supported_enrichers)
  )
  extra_parameters = garf_utils.ParamsParser(parsed_param_keys).parse(kwargs)
  fetching_service = media_fetching.MediaFetchingService(args.source)
  request_class, _ = fetcher.FETCHERS.get(args.source)

  report = fetching_service.fetch(
    request=request_class(
      **extra_parameters.get(args.source),
      extra_info=args.extra_info,
      media_type=args.media_type,
    ),
    extra_parameters=extra_parameters,
  )
  writer.create_writer(
    args.writer, **(extra_parameters.get(args.writer) or {})
  ).write(report, args.output)


if __name__ == '__main__':
  main()
