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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-module-docstring, missing-class-docstring, missing-function-docstring

import dataclasses
import pathlib

from google.cloud import videointelligence, vision
from media_tagging import media, tagging_result
from media_tagging.taggers import api

_SCRIPT_DIR = pathlib.Path(__file__).parent


medium = media.Medium('test')


@dataclasses.dataclass
class FakeVisionAPIResponse:
  label_annotations: list[vision.EntityAnnotation]


class TestGoogleVisionAPITagger:
  def test_tag_returns_correct_tagging_result(self, mocker):
    fake_response = FakeVisionAPIResponse(
      label_annotations=[vision.EntityAnnotation(description='test', score=0.0)]
    )
    mocker.patch(
      'google.cloud.vision.ImageAnnotatorClient.label_detection',
      return_value=fake_response,
    )
    test_tagger = api.GoogleVisionAPITagger()
    result = test_tagger.tag(medium)
    expected_result = tagging_result.TaggingResult(
      identifier='test',
      type='image',
      content=[tagging_result.Tag(name='test', score=0.0)],
    )

    assert result == expected_result


class FakeVideoIntelligenceAPIOperation:
  def result(
    self, timeout: int | None = None
  ) -> videointelligence.AnnotateVideoResponse:
    del timeout
    annotation_results = videointelligence.VideoAnnotationResults(
      frame_label_annotations=[
        videointelligence.LabelAnnotation(
          entity=videointelligence.Entity(description='test'),
          frames=[videointelligence.LabelFrame(confidence=0.0)],
        )
      ]
    )

    return videointelligence.AnnotateVideoResponse(
      annotation_results=[annotation_results]
    )


class TestGoogleVideoIntelligenceAPITagger:
  def test_tag_returns_correct_tagging_result(self, mocker):
    fake_response = FakeVideoIntelligenceAPIOperation()
    mocker.patch(
      'google.cloud.videointelligence.VideoIntelligenceServiceClient.annotate_video',
      return_value=fake_response,
    )
    test_tagger = api.GoogleVideoIntelligenceAPITagger()
    result = test_tagger.tag(medium)
    expected_result = tagging_result.TaggingResult(
      identifier='test',
      type='video',
      content=[tagging_result.Tag(name='test', score=0.0)],
    )

    assert result == expected_result
