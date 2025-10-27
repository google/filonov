# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

"""CLI utility for loading tagging results to DB."""

import enum

import typer
from garf_executors.entrypoints import utils as garf_utils
from typing_extensions import Annotated

import media_tagging
from media_tagging import media, repositories
from media_tagging.entrypoints import utils
from media_tagging.loaders import media_loader_service

typer_app = typer.Typer()

MediaType = Annotated[
  media.MediaTypeEnum,
  typer.Option(
    help='Type of media',
    case_sensitive=False,
  ),
]
Input = Annotated[
  list[str],
  typer.Argument(
    help='Paths to local/remove files or URLs',
  ),
]

Logger = Annotated[
  garf_utils.LoggerEnum,
  typer.Option(
    help='Type of logger',
  ),
]
LogLevel = Annotated[
  str,
  typer.Option(
    help='Level of logging',
  ),
]
LogName = Annotated[
  str,
  typer.Option(
    help='Name of logger',
  ),
]


class Action(str, enum.Enum):
  tag = 'tag'
  describe = 'describe'


def _version_callback(show_version: bool) -> None:
  if show_version:
    print(f'media-loader version: {media_tagging.__version__}')
    raise typer.Exit()


@typer_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True},
)
@utils.log_shutdown
def main(
  location: Input,
  media_type: MediaType,
  db_uri: Annotated[
    str,
    typer.Option(
      help='Database connection string to store and retrieve results',
    ),
  ],
  action: Action = Action.tag,
  loader: Annotated[
    str,
    typer.Option(
      help='Type of loader',
      case_sensitive=False,
    ),
  ] = 'file',
  logger: Logger = 'rich',
  loglevel: LogLevel = 'INFO',
  log_name: LogName = 'media-loader',
  version: Annotated[
    bool,
    typer.Option(
      help='Display library version',
      callback=_version_callback,
      is_eager=True,
      expose_value=False,
    ),
  ] = False,
):
  file_locations, parameters = utils.parse_typer_arguments(location)
  loader_service = media_loader_service.MediaLoaderService(
    repositories.SqlAlchemyTaggingResultsRepository(db_uri)
  )
  extra_parameters = garf_utils.ParamsParser(['loader']).parse(parameters)

  logger = garf_utils.init_logging(
    loglevel=loglevel, logger_type=logger, name=log_name
  )

  for loc in file_locations:
    logger.info('Getting tagging results from %s', loc)
    parameters = {
      'loader_type': loader,
      'media_type': media_type,
      'location': loc,
      'loader_parameters': extra_parameters.get('loader'),
    }
    if action == 'tag':
      loader_service.load_media_tags(**parameters)
    else:
      loader_service.load_media_descriptions(**parameters)


if __name__ == '__main__':
  typer_app()
