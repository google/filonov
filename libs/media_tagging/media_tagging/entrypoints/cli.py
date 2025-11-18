# Copyright 2024 Google LLC
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
"""Provides CLI for media tagging."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from typing import Optional

import typer
from garf_executors.entrypoints import utils as garf_utils
from garf_io import writer as garf_writer
from typing_extensions import Annotated

import media_tagging
from media_tagging import media, media_tagging_service, repositories
from media_tagging.entrypoints import utils
from media_tagging.entrypoints.tracer import initialize_tracer
from media_tagging.telemetry import tracer

initialize_tracer()
typer_app = typer.Typer()

MediaPaths = Annotated[
  Optional[list[str]],
  typer.Argument(
    help='Media paths',
  ),
]
Input = Annotated[
  Optional[str],
  typer.Option(
    help='File with media_paths',
    case_sensitive=False,
  ),
]
MediaType = Annotated[
  media.MediaTypeEnum,
  typer.Option(
    help='Type of media',
    case_sensitive=False,
  ),
]
Tagger = Annotated[
  Optional[str],
  typer.Option(
    help='Type of tagger',
  ),
]
DbUri = Annotated[
  Optional[str],
  typer.Option(
    help='Database connection string to store and retrieve results',
  ),
]

Writer = Annotated[
  garf_writer.WriterOption,
  typer.Option(
    help='Type of writer used to write resulting report',
  ),
]

Output = Annotated[
  Optional[str],
  typer.Option(
    help='Name of output file',
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

Deduplicate = Annotated[
  bool,
  typer.Option(
    help='Whether cached results of tagging should be deduplicated',
  ),
]

ParallelTreshold = Annotated[
  int,
  typer.Option(
    help='Number of parallel processes to perform media tagging',
  ),
]


def _version_callback(show_version: bool) -> None:
  if show_version:
    print(f'media-tagging version: {media_tagging.__version__}')
    raise typer.Exit()


@typer_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}
)
@tracer.start_as_current_span('media_tagger.cli.tag')
@utils.log_shutdown
def tag(
  media_type: MediaType,
  media_paths: MediaPaths = None,
  input: Input = None,
  tagger: Tagger = 'gemini',
  db_uri: DbUri = None,
  writer: Writer = 'json',
  output: Output = 'tagging_results',
  deduplicate: Deduplicate = False,
  logger: Logger = 'rich',
  loglevel: LogLevel = 'INFO',
  log_name: LogName = 'media-tagger',
  parallel_threshold: ParallelTreshold = 10,
) -> None:
  tagging_service = media_tagging_service.MediaTaggingService(
    repositories.SqlAlchemyTaggingResultsRepository(db_uri)
  )
  media_paths, parameters = utils.parse_typer_arguments(media_paths)
  extra_parameters = garf_utils.ParamsParser(['tagger', writer, 'input']).parse(
    parameters
  )

  logger = garf_utils.init_logging(
    loglevel=loglevel, logger_type=logger, name=log_name
  )

  media_paths = media_paths or media.get_media_paths_from_file(
    utils.InputConfig(path=input, **extra_parameters.get('input'))
  )
  request = media_tagging_service.MediaTaggingRequest(
    tagger_type=tagger,
    media_type=media_type,
    media_paths=media_paths,
    tagging_options=extra_parameters.get('tagger'),
    parallel_threshold=parallel_threshold,
    deduplicate=deduplicate,
  )
  logger.info(request)
  path_processor = extra_parameters.get('tagger', {}).get('path_processor')
  tagging_results = tagging_service.tag_media(request, path_processor)
  if output is None:
    raise typer.Exit()
  if not tagging_results:
    logger.error('No tagging tagging results found.')
    raise typer.Exit(1)

  writer_parameters = extra_parameters.get(writer) or {}
  tagging_results.save(output, writer, **writer_parameters)


@typer_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}
)
@utils.log_shutdown
@tracer.start_as_current_span('media_tagger.cli.describe')
def describe(
  media_type: MediaType,
  media_paths: MediaPaths = None,
  input: Input = None,
  tagger: Tagger = 'gemini',
  db_uri: DbUri = None,
  writer: Writer = 'json',
  output: Output = 'tagging_results',
  deduplicate: Deduplicate = False,
  logger: Logger = 'rich',
  loglevel: LogLevel = 'INFO',
  log_name: LogName = 'media-tagger',
  parallel_threshold: ParallelTreshold = 10,
):
  tagging_service = media_tagging_service.MediaTaggingService(
    repositories.SqlAlchemyTaggingResultsRepository(db_uri)
  )
  media_paths, parameters = utils.parse_typer_arguments(media_paths)
  extra_parameters = garf_utils.ParamsParser(['tagger', writer, 'input']).parse(
    parameters
  )

  logger = garf_utils.init_logging(
    loglevel=loglevel, logger_type=logger, name=log_name
  )

  media_paths = media_paths or media.get_media_paths_from_file(
    utils.InputConfig(path=input, **extra_parameters.get('input'))
  )
  request = media_tagging_service.MediaTaggingRequest(
    tagger_type=tagger,
    media_type=media_type,
    media_paths=media_paths,
    tagging_options=extra_parameters.get('tagger'),
    parallel_threshold=parallel_threshold,
    deduplicate=deduplicate,
  )
  logger.info(request)
  path_processor = extra_parameters.get('tagger', {}).get('path_processor')
  tagging_results = tagging_service.describe_media(request, path_processor)
  if output is None:
    raise typer.Exit()
  if not tagging_results:
    logger.error('No tagging tagging results found.')
    raise typer.Exit(1)

  writer_parameters = extra_parameters.get(writer) or {}
  tagging_results.save(output, writer, **writer_parameters)


@typer_app.callback(invoke_without_command=True)
def main(
  ctx: typer.Context,
  version: Annotated[
    bool,
    typer.Option(
      help='Display library version',
      callback=_version_callback,
      is_eager=True,
      expose_value=False,
    ),
  ] = False,
): ...


if __name__ == '__main__':
  typer_app()
