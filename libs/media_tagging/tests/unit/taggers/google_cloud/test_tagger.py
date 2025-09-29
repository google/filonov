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

import pytest
from google.cloud import videointelligence, vision
from media_tagging import media, tagging_result
from media_tagging.taggers import base
from media_tagging.taggers.google_cloud import tagger

_SCRIPT_DIR = pathlib.Path(__file__).parent


@dataclasses.dataclass
class FakeVisionAPIResponse:
  label_annotations: list[vision.EntityAnnotation]


@pytest.mark.cloud
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


@pytest.mark.cloud
class TestGoogleCloudTagger:
  def test_tag_returns_correct_tagging_result_for_image(self, mocker):
    media_type = media.MediaTypeEnum.IMAGE
    fake_response = FakeVisionAPIResponse(
      label_annotations=[vision.EntityAnnotation(description='test', score=0.0)]
    )
    mocker.patch(
      'media_tagging.media.Medium.content',
      new_callable=mocker.PropertyMock,
      return_value=bytes(),
    )
    mocker.patch(
      'google.cloud.vision.ImageAnnotatorClient.label_detection',
      return_value=fake_response,
    )
    test_tagger = tagger.GoogleCloudTagger(project='test')
    result = test_tagger.tag(media.Medium('test', media_type))
    expected_result = tagging_result.TaggingResult(
      identifier='test',
      type='image',
      tagger='google-cloud',
      output='tag',
      content=[tagging_result.Tag(name='test', score=0.0)],
      tagging_details={},
    )

    assert result == expected_result

  def test_tag_returns_correct_tagging_result_for_video(self, mocker):
    media_type = media.MediaTypeEnum.VIDEO
    fake_response = FakeVideoIntelligenceAPIOperation()
    mocker.patch(
      'media_tagging.media.Medium.content',
      new_callable=mocker.PropertyMock,
      return_value=bytes(),
    )
    mocker.patch(
      'google.cloud.videointelligence.VideoIntelligenceServiceClient.annotate_video',
      return_value=fake_response,
    )
    test_tagger = tagger.GoogleCloudTagger(project='test')
    result = test_tagger.tag(media.Medium('test', media_type))
    expected_result = tagging_result.TaggingResult(
      identifier='test',
      type='video',
      tagger='google-cloud',
      output='tag',
      content=[tagging_result.Tag(name='test', score=0.0)],
      tagging_details={},
    )

    assert result == expected_result

  def test_tag_raises_tagger_error_on_unsupported_media_type(self):
    media_type = media.MediaTypeEnum.YOUTUBE_VIDEO
    test_tagger = tagger.GoogleCloudTagger(project='test')
    with pytest.raises(base.TaggerError):
      test_tagger.tag(media.Medium('test', media_type))

  def test_init_raises_unsupported_method_error_on_describe(self):
    test_tagger = tagger.GoogleCloudTagger(project='test')
    with pytest.raises(base.UnsupportedMethodError):
      test_tagger.describe(media.Medium('test', media.MediaTypeEnum.IMAGE))
