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
"""CLI entrypoint for generating creative map."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import argparse

from filonov.inputs import input_service
from garf_core import report as garf_report
from garf_executors.entrypoints import utils as gaarf_utils
from garf_io import writer as garf_writer
from media_tagging import media


def main():  # noqa: D103
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--source',
    dest='source',
    choices=['googleads', 'youtube'],
    default='googleads',
    help='Which datasources to use for generating a map',
  )
  parser.add_argument(
    '--media-type',
    dest='media_type',
    choices=media.MediaTypeEnum.options(),
    help='Type of media.',
  )
  parser.add_argument('--writer', dest='writer', default='json')
  parser.add_argument('--output', dest='output', default='tagging_results')
  parser.add_argument(
    '--media-urls-only', dest='media_urls_only', action='store_true'
  )
  parser.set_defaults(media_urls_only=False)
  args, kwargs = parser.parse_known_args()

  extra_parameters = gaarf_utils.ParamsParser([args.source]).parse(kwargs)
  report = input_service.MediaInputService(args.source).fetch_input(
    args.media_type, extra_parameters.get(args.source)
  )
  if args.media_urls_only:
    results = report['media_url'].to_list(row_type='scalar', distinct=True)
    report = garf_report.GarfReport(
      results=[[r] for r in results], column_names=['media_url']
    )
  writer_parameters = extra_parameters.get(args.writer) or {}
  garf_writer.create_writer(args.writer, **writer_parameters).write(
    report, args.output
  )


if __name__ == '__main__':
  main()
