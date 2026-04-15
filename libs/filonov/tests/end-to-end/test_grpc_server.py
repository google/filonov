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
from filonov import filonov_pb2 as pb
from filonov import filonov_pb2_grpc
from filonov.entrypoints import grpc_server


@pytest.fixture(scope='module')
def grpc_add_to_server():
  return filonov_pb2_grpc.add_FilonovServiceServicer_to_server


@pytest.fixture(scope='module')
def grpc_servicer():
  return grpc_server.FilonovService()


@pytest.fixture(scope='module')
def grpc_stub_cls(grpc_channel):
  return filonov_pb2_grpc.FilonovServiceStub


def test_generate_creative_map(grpc_stub):
  request = pb.GenerateCreativeMapRequest(
    source='googleads',
    googleads_parameters=pb.GoogleAdsParameters(
      account='1', media_type=pb.MediaType.TEXT
    ),
  )
  response = grpc_stub.GenerateCreativeMap(request)
  assert not response.done
  assert response.id


def test_generate_tables(grpc_stub):
  request = pb.GenerateTablesRequest(
    source='googleads',
    googleads_parameters=pb.GoogleAdsParameters(
      account='1', media_type=pb.MediaType.TEXT
    ),
    writer='console',
  )
  response = grpc_stub.GenerateTables(request)
  assert not response.done
  assert response.id


def test_get_operation(grpc_stub):
  request = pb.GetOperationRequest(
    operation_id='1',
  )
  response = grpc_stub.GetOperation(request)
  assert not response.done
