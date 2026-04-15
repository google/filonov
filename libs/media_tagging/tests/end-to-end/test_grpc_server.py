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
import pytest
from media_tagging import tagging_pb2 as pb
from media_tagging import tagging_pb2_grpc
from media_tagging.entrypoints import grpc_server


@pytest.fixture(scope='module')
def grpc_add_to_server():
  return tagging_pb2_grpc.add_MediaTaggingServiceServicer_to_server


@pytest.fixture(scope='module')
def grpc_servicer():
  return grpc_server.MediaTaggingService()


@pytest.fixture(scope='module')
def grpc_stub_cls(grpc_channel):
  return tagging_pb2_grpc.MediaTaggingServiceStub


def test_tag(grpc_stub):
  media = ['One fish', 'One cat']
  request = pb.TagRequest(
    tagger_type='fake',
    media_paths=media,
    media_type='TEXT',
    tagging_options=pb.TaggingOptions(n_tags=5),
  )
  response = grpc_stub.Tag(request)
  assert len(response.results) == len(media)


def test_describe(grpc_stub):
  media = ['One fish', 'One cat']
  request = pb.DescribeRequest(
    tagger_type='fake',
    media_paths=media,
    media_type='TEXT',
  )
  response = grpc_stub.Describe(request)
  assert len(response.results) == len(media)
