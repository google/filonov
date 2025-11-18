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

from typing import Optional

import media_fetching
import media_similarity
import media_tagging
import typer
from garf_executors.entrypoints import utils as garf_utils
from media_fetching.sources import models
from media_tagging import media
from media_tagging.entrypoints import utils as tagging_utils
from typing_extensions import Annotated

import filonov
from filonov.entrypoints import utils
from filonov.entrypoints.tracer import initialize_tracer
from filonov.telemetry import tracer

initialize_tracer()
typer_app = typer.Typer()


def _version_callback(show_version: bool) -> None:
  if show_version:
    print(f'filonov version: {filonov.__version__}')
    raise typer.Exit()


@typer_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}
)
@tracer.start_as_current_span('filonov.cli.main')
@tagging_utils.log_shutdown
def main(
  ctx: typer.Context,
  source: Annotated[
    models.InputSource,
    typer.Option(
      help='Source to get data from',
      case_sensitive=False,
    ),
  ] = 'googleads',
  media_type: Annotated[
    media.MediaTypeEnum,
    typer.Option(
      help='Type of media',
      case_sensitive=False,
    ),
  ] = 'IMAGE',
  tagger: Annotated[
    Optional[str],
    typer.Option(
      help='Type of tagger',
      case_sensitive=False,
    ),
  ] = None,
  output_name: Annotated[
    str,
    typer.Option(
      help='Name of output file',
    ),
  ] = 'creative_map',
  db_uri: Annotated[
    Optional[str],
    typer.Option(
      help='Database connection string to store and retrieve results',
    ),
  ] = None,
  trim_tags_threshold: Annotated[
    Optional[float],
    typer.Option(
      help='Min allowed score for tags',
    ),
  ] = None,
  embed_previews: Annotated[
    bool,
    typer.Option(
      help='Whether media previews should be embedded into a creative map',
    ),
  ] = False,
  omit_series: Annotated[
    bool,
    typer.Option(
      help='Whether omit time series data from creative map',
    ),
  ] = False,
  parallel_threshold: Annotated[
    int,
    typer.Option(
      help='Number of parallel processes to perform media tagging',
    ),
  ] = 10,
  logger: Annotated[
    garf_utils.LoggerEnum,
    typer.Option(
      help='Type of logger',
    ),
  ] = 'rich',
  loglevel: Annotated[
    str,
    typer.Option(
      help='Level of logging',
    ),
  ] = 'INFO',
  log_name: Annotated[
    str,
    typer.Option(
      help='Name of logger',
    ),
  ] = 'filonov',
  version: Annotated[
    bool,
    typer.Option(
      help='Display library version',
      callback=_version_callback,
      is_eager=True,
      expose_value=False,
    ),
  ] = False,
):  # noqa: D103
  garf_utils.init_logging(
    loglevel=loglevel.upper(), logger_type=logger, name=log_name
  )
  supported_enrichers = (
    media_fetching.enrichers.enricher.AVAILABLE_MODULES.keys()
  )
  parsed_param_keys = set(
    [source, 'tagger', 'similarity'] + list(supported_enrichers)
  )
  extra_parameters = garf_utils.ParamsParser(parsed_param_keys).parse(ctx.args)
  fetching_service = media_fetching.MediaFetchingService.from_source_alias(
    source
  )

  if extra_parameters.get('tagger', {}).get('db_uri'):
    tagging_db_uri = extra_parameters.get('tagger').pop('db_uri')
  else:
    tagging_db_uri = db_uri
  tagging_service = media_tagging.MediaTaggingService(
    tagging_results_repository=(
      media_tagging.repositories.SqlAlchemyTaggingResultsRepository(
        tagging_db_uri
      )
    )
  )
  if extra_parameters.get('similarity', {}).get('db_uri'):
    similarity_db_uri = extra_parameters.get('similarity').pop('db_uri')
  else:
    similarity_db_uri = db_uri
  similarity_service = media_similarity.MediaSimilarityService(
    media_similarity_repository=media_similarity.repositories.SqlAlchemySimilarityPairsRepository(
      similarity_db_uri
    ),
    tagging_service=media_tagging.MediaTaggingService(
      media_tagging.repositories.SqlAlchemyTaggingResultsRepository(
        tagging_db_uri
      )
    ),
  )
  if source == 'youtube':
    media_type = 'YOUTUBE_VIDEO'
    tagger = 'gemini'
  request = filonov.CreativeMapGenerateRequest(
    source=source,
    media_type=media_type,
    tagger=tagger,
    tagger_parameters=extra_parameters.get('tagger'),
    similarity_parameters=extra_parameters.get('similarity'),
    source_parameters=extra_parameters.get(source),
    output_parameters=filonov.filonov_service.OutputParameters(
      output_name=output_name
    ),
    parallel_threshold=parallel_threshold,
    trim_tags_threshold=trim_tags_threshold,
    embed_previews=embed_previews,
    omit_series=omit_series,
    context=extra_parameters,
  )
  filonov_service = filonov.FilonovService(
    fetching_service, tagging_service, similarity_service
  )
  generated_map = filonov_service.generate_creative_map(request)
  destination = utils.build_creative_map_destination(
    request.output_parameters.output_name
  )
  generated_map.save(destination)


if __name__ == '__main__':
  typer_app()
