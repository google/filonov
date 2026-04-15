# Copyright 2026 Google LLC
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


"""gRPC endpoint for filonov."""

import logging
from concurrent import futures

import grpc
import typer
from google.protobuf.json_format import MessageToDict
from grpc_reflection.v1alpha import reflection
from typing_extensions import Annotated

import filonov
from filonov import filonov_pb2, filonov_pb2_grpc
from filonov.entrypoints import tasks

typer_app = typer.Typer()


class FilonovService(filonov_pb2_grpc.FilonovService):
  def GenerateCreativeMap(
    self, request: filonov_pb2.GenerateCreativeMapRequest, context
  ):
    request_dict = MessageToDict(request, preserving_proto_field_name=True)
    request_source = request.source
    source_parameters = {}
    for key, value in request_dict.items():
      if key == f'{request_source}_parameters':
        source_parameters = value
    request_dict['source_parameters'] = source_parameters
    filonov_request = filonov.GenerateCreativeMapRequest(**request_dict)
    task = tasks.create_map.delay(filonov_request.model_dump())
    return filonov_pb2.Operation(id=task.id, done=False)

  def GenerateTables(self, request: filonov_pb2.GenerateTablesRequest, context):
    request_dict = MessageToDict(request, preserving_proto_field_name=True)
    request_source = request.source
    source_parameters = {}
    for key, value in request_dict.items():
      if key == f'{request_source}_parameters':
        source_parameters = value
    request_dict['source_parameters'] = source_parameters
    filonov_request = filonov.GenerateTablesRequest(**request_dict)
    task = tasks.create_tables.delay(filonov_request.model_dump())
    return filonov_pb2.Operation(id=task.id, done=False)

  def GetOperation(self, request: filonov_pb2.GetOperationRequest, context):
    operation = tasks.app.AsyncResult(request.operation_id)
    done = operation.status in ('SUCCESS', 'FAILURE')
    return filonov_pb2.Operation(id=request.operation_id, done=done)


@typer_app.command()
def main(
  ctx: typer.Context,
  port: Annotated[int, typer.Option('--port', '-p')] = 50051,
  parallel_threshold: Annotated[int, typer.Option()] = 10,
) -> None:
  server = grpc.server(
    futures.ThreadPoolExecutor(max_workers=parallel_threshold)
  )
  service = FilonovService()
  filonov_pb2_grpc.add_FilonovServiceServicer_to_server(service, server)
  service_names = (
    filonov_pb2.DESCRIPTOR.services_by_name['FilonovService'].full_name,
    reflection.SERVICE_NAME,
  )
  reflection.enable_server_reflection(service_names, server)
  server.add_insecure_port(f'[::]:{port}')
  server.start()
  logging.info('FilonovService started, listening on port %d', port)
  server.wait_for_termination()


if __name__ == '__main__':
  typer_app()
