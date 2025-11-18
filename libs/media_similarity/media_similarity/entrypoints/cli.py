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

import functools
import operator
from typing import Optional

import media_tagging
import typer
from garf_executors.entrypoints import utils as garf_utils
from garf_io import writer as garf_writer
from media_tagging import media
from media_tagging.entrypoints import utils as tagging_utils
from typing_extensions import Annotated

import media_similarity
from media_similarity.entrypoints.tracer import initialize_tracer
from media_similarity.telemetry import tracer

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

Writer = Annotated[
  garf_writer.WriterOption,
  typer.Option(
    help='Type of writer used to write resulting report',
  ),
]

Output = Annotated[
  str,
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


def _version_callback(show_version: bool) -> None:
  if show_version:
    print(f'media-similarity version: {media_similarity.__version__}')
    raise typer.Exit()


def _build_similarity_service(
  db_uri: str, extra_parameters: dict[str, dict[str, str]]
) -> media_similarity.MediaSimilarityService:
  if extra_parameters.get('tagger', {}).get('db_uri'):
    tagging_db_uri = extra_parameters.get('tagger').pop('db_uri')
    tagging_service = media_tagging.MediaTaggingService(
      media_tagging.repositories.SqlAlchemyTaggingResultsRepository(
        tagging_db_uri
      )
    )
  else:
    tagging_service = None
  return media_similarity.MediaSimilarityService(
    media_similarity_repository=(
      media_similarity.repositories.SqlAlchemySimilarityPairsRepository(db_uri)
    ),
    tagging_service=tagging_service,
  )


@typer_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}
)
@tagging_utils.log_shutdown
@tracer.start_as_current_span('media_similarity.cli.cluster')
def cluster(
  media_paths: MediaPaths = None,
  input: Input = None,
  media_type: MediaType = 'IMAGE',
  tagger: Annotated[
    Optional[str],
    typer.Option(
      help='Type of tagger',
      case_sensitive=False,
    ),
  ] = 'gemini',
  db_uri: Annotated[
    Optional[str],
    typer.Option(
      help='Database connection string to store and retrieve results',
    ),
  ] = None,
  writer: Writer = 'json',
  output: Output = 'similarity_results',
  normalize: Annotated[
    bool,
    typer.Option(
      help='Whether to normalize similarity results',
    ),
  ] = False,
  custom_threshold: Annotated[
    Optional[float],
    typer.Option(
      help='Custom threshold to identify similar pairs',
    ),
  ] = None,
  logger: Logger = 'rich',
  loglevel: LogLevel = 'INFO',
  log_name: LogName = 'media-similarity',
  parallel_threshold: Annotated[
    int,
    typer.Option(
      help='Number of parallel processes to perform media tagging',
    ),
  ] = 10,
):
  garf_utils.init_logging(logger_type=logger, loglevel=loglevel, name=log_name)
  media_paths, parameters = tagging_utils.parse_typer_arguments(media_paths)
  extra_parameters = garf_utils.ParamsParser([writer, 'input', 'tagger']).parse(
    parameters
  )
  media_paths = media_paths or media.get_media_paths_from_file(
    media.InputConfig(path=input, **extra_parameters.get('input'))
  )
  similarity_service = _build_similarity_service(db_uri, extra_parameters)
  request = media_similarity.MediaClusteringRequest(
    media_paths=media_paths,
    media_type=media_type,
    tagger_type=tagger,
    normalize=normalize,
    custom_threshold=custom_threshold,
    parallel_threshold=parallel_threshold,
  )
  clustering_results = similarity_service.cluster_media(request)
  report = clustering_results.to_garf_report()
  writer_parameters = extra_parameters.get(writer) or {}
  garf_writer.create_writer(writer, **writer_parameters).write(report, output)


@typer_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}
)
@tagging_utils.log_shutdown
@tracer.start_as_current_span('media_similarity.cli.compare')
def compare(
  media_type: MediaType,
  db_uri: Annotated[
    str,
    typer.Option(
      help='Database connection string to store and retrieve results',
    ),
  ],
  media_paths: MediaPaths = None,
  input: Input = None,
  writer: Writer = 'json',
  output: Output = 'comparison_results',
  logger: Logger = 'rich',
  loglevel: LogLevel = 'INFO',
  log_name: LogName = 'media-similarity',
):
  garf_utils.init_logging(logger_type=logger, loglevel=loglevel, name=log_name)
  media_paths, parameters = tagging_utils.parse_typer_arguments(media_paths)
  extra_parameters = garf_utils.ParamsParser([writer, 'input', 'tagger']).parse(
    parameters
  )
  media_paths = media_paths or media.get_media_paths_from_file(
    media.InputConfig(path=input, **extra_parameters.get('input'))
  )
  similarity_service = _build_similarity_service(db_uri, extra_parameters)
  media_comparison_results = similarity_service.compare_media(
    media_similarity.MediaSimilarityComparisonRequest(
      media_paths=media_paths,
      media_type=media_type,
    )
  )
  report = functools.reduce(
    operator.add,
    [result.to_garf_report() for result in media_comparison_results],
  )
  writer_parameters = extra_parameters.get(writer) or {}
  garf_writer.create_writer(writer, **writer_parameters).write(report, output)


@typer_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}
)
@tagging_utils.log_shutdown
@tracer.start_as_current_span('media_similarity.cli.search')
def search(
  media_type: MediaType,
  db_uri: Annotated[
    str,
    typer.Option(
      help='Database connection string to store and retrieve results',
    ),
  ],
  media_paths: MediaPaths = None,
  input: Input = None,
  writer: Writer = 'json',
  output: Output = 'comparison_results',
  logger: Logger = 'rich',
  loglevel: LogLevel = 'INFO',
  log_name: LogName = 'media-similarity',
):
  garf_utils.init_logging(logger_type=logger, loglevel=loglevel, name=log_name)
  media_paths, parameters = tagging_utils.parse_typer_arguments(media_paths)
  extra_parameters = garf_utils.ParamsParser([writer, 'input', 'tagger']).parse(
    parameters
  )
  media_paths = media_paths or media.get_media_paths_from_file(
    media.InputConfig(path=input, **extra_parameters.get('input'))
  )
  similarity_service = _build_similarity_service(db_uri, extra_parameters)
  similarity_search_results = similarity_service.find_similar_media(
    media_similarity.MediaSimilaritySearchRequest(
      media_paths=media_paths,
      media_type=media_type,
    )
  )
  report = functools.reduce(
    operator.add,
    [result.to_garf_report() for result in similarity_search_results],
  )
  writer_parameters = extra_parameters.get(writer) or {}
  garf_writer.create_writer(writer, **writer_parameters).write(report, output)


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
