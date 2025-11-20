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

from typing import Optional

import typer
from garf_executors.entrypoints import utils as garf_utils
from garf_io import writer as garf_writer
from media_tagging import media
from media_tagging.entrypoints import utils as tagging_utils
from typing_extensions import Annotated

import media_fetching
from media_fetching.sources import fetcher, models

typer_app = typer.Typer()


def _version_callback(show_version: bool) -> None:
  if show_version:
    print(f'media-fetcher version: {media_fetching.__version__}')
    raise typer.Exit()


@typer_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}
)
@tagging_utils.log_shutdown
def main(
  ctx: typer.Context,
  media_type: Annotated[
    media.MediaTypeEnum,
    typer.Option(
      help='Type of media',
      case_sensitive=False,
    ),
  ] = 'IMAGE',
  source: Annotated[
    models.InputSource,
    typer.Option(
      help='Type of media',
      case_sensitive=False,
    ),
  ] = 'googleads',
  extra_info: Annotated[
    Optional[str],
    typer.Option(
      help=(
        'Comma separated modules to add extra information to fetched data '
        'specified in "module.method" format'
      )
    ),
  ] = None,
  writer: Annotated[
    garf_writer.WriterOption,
    typer.Option(
      help='Type of writer used to write resulting report',
    ),
  ] = 'json',
  output: Annotated[
    str,
    typer.Option(
      help='Destination of written report',
    ),
  ] = 'media_results',
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
  ] = 'media-fetcher',
  enable_cache: Annotated[
    bool,
    typer.Option(
      help='Whether to use cached version of reports if possible',
    ),
  ] = False,
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
  parsed_param_keys = set([source, writer] + list(supported_enrichers))
  extra_parameters = garf_utils.ParamsParser(parsed_param_keys).parse(ctx.args)
  fetching_service = media_fetching.MediaFetchingService.from_source_alias(
    source=source, enable_cache=enable_cache
  )
  request_class, _ = fetcher.FETCHERS.get(source)
  request = request_class(
    **extra_parameters.get(source),
    extra_info=extra_info,
    media_type=media_type,
  )

  report = fetching_service.fetch(
    request=request,
    extra_parameters=extra_parameters,
  )
  garf_writer.create_writer(
    writer, **(extra_parameters.get(writer) or {})
  ).write(report, output)


if __name__ == '__main__':
  typer_app()
