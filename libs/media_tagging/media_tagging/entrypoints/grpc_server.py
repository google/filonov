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

"""gRPC endpoint for media_tagging."""

import argparse
import logging
import os
from concurrent import futures

import grpc
from google.protobuf.json_format import MessageToDict, ParseDict
from grpc_reflection.v1alpha import reflection

import media_tagging
from media_tagging import repositories, tagging_pb2, tagging_pb2_grpc
from media_tagging.entrypoints.tracer import initialize_tracer


class MediaTaggingService(tagging_pb2_grpc.MediaTaggingService):
  def Tag(self, request: tagging_pb2.TagRequest, context):
    tagging_service = media_tagging.MediaTaggingService(
      repositories.SqlAlchemyTaggingResultsRepository(
        os.getenv('MEDIA_TAGGING_DB_URL')
      )
    )
    tagging_request = media_tagging.MediaTaggingRequest(
      **MessageToDict(request, preserving_proto_field_name=True)
    )
    result = tagging_service.tag_media(tagging_request)
    response = tagging_pb2.TagResponse()
    ParseDict(result.model_dump(), response)
    return response

  def Describe(self, request: tagging_pb2.DescribeRequest, context):
    tagging_service = media_tagging.MediaTaggingService(
      repositories.SqlAlchemyTaggingResultsRepository(
        os.getenv('MEDIA_TAGGING_DB_URL')
      )
    )
    tagging_request = media_tagging.MediaTaggingRequest(
      **MessageToDict(request, preserving_proto_field_name=True)
    )
    result = tagging_service.describe_media(tagging_request)
    response = tagging_pb2.DescribeResponse()
    ParseDict(result.model_dump(), response)
    return response


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--port', dest='port', default=50051, type=int)
  parser.add_argument(
    '--parallel-threshold', dest='parallel_threshold', default=10, type=int
  )
  args, _ = parser.parse_known_args()
  initialize_tracer()
  server = grpc.server(
    futures.ThreadPoolExecutor(max_workers=args.parallel_threshold)
  )

  service = MediaTaggingService()
  tagging_pb2_grpc.add_MediaTaggingServiceServicer_to_server(service, server)
  service_names = (
    tagging_pb2.DESCRIPTOR.services_by_name['MediaTaggingService'].full_name,
    reflection.SERVICE_NAME,
  )
  reflection.enable_server_reflection(service_names, server)
  server.add_insecure_port(f'[::]:{args.port}')
  server.start()
  logging.info('MediaTagging service started, listening on port %d', 50051)
  server.wait_for_termination()
