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
"""Module for performing media tagging via Google APIs.

Media tagging sends API requests to tagging engine (i.e. Google Vision API)
and returns tagging results that can be easily written.
"""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from collections import defaultdict

from google.cloud import videointelligence, vision
from typing_extensions import override

from media_tagging import media, tagging_result
from media_tagging.taggers import base


class GoogleVisionAPITagger(base.BaseTagger):
  """Tagger responsible for getting image tags from Cloud Vision API.

  Attributes:
    client: Vision API client responsible to tagging.
  """

  def __init__(self, project: str | None = None) -> None:
    """Initializes GoogleVisionAPITagger with a given project.

    Args:
      project: Google Cloud project id.
    """
    self._project = project

  @property
  def client(self) -> vision.ImageAnnotatorClient:
    """Creates ImageAnnotatorClient."""
    return vision.ImageAnnotatorClient()

  @override
  def tag(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    image = vision.Image(content=medium.content)
    response = self.client.label_detection(image=image)
    tags = [
      tagging_result.Tag(name=r.description, score=r.score)
      for r in response.label_annotations
    ]
    if n_tags := tagging_options.n_tags:
      tags = self._limit_number_of_tags(tags, n_tags)
    return tagging_result.TaggingResult(
      identifier=medium.name, type='image', content=tags
    )


class GoogleVideoIntelligenceAPITagger(base.BaseTagger):
  """Tagger responsible for getting image tags from Video Intelligence API.

  Attributes:
    client: Video Intelligence API client responsible to tagging.
  """

  def __init__(self, project: str | None = None) -> None:
    """Initializes GoogleVideoIntelligenceAPITagger with a given project.

    Args:
      project: Google Cloud project id.
    """
    self._project = project

  @property
  def client(self) -> videointelligence.VideoIntelligenceServiceClient:
    """Creates VideoIntelligenceServiceClient."""
    return videointelligence.VideoIntelligenceServiceClient()

  @override
  def tag(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
  ) -> tagging_result.TaggingResult:
    request = videointelligence.AnnotateVideoRequest(
      input_content=medium.content,
      video_context=videointelligence.VideoContext(
        label_detection_config=videointelligence.LabelDetectionConfig(
          frame_confidence_threshold=0.11,
          label_detection_mode=(
            videointelligence.LabelDetectionMode.SHOT_AND_FRAME_MODE
          ),
        )
      ),
      features=[videointelligence.Feature.LABEL_DETECTION],
    )
    operation = self.client.annotate_video(request)
    response = operation.result(timeout=180)
    tags_scores: dict[str, float] = defaultdict(float)
    for frame_label in response.annotation_results[0].frame_label_annotations:
      tags_scores[frame_label.entity.description] += sum(
        c.confidence for c in frame_label.frames
      )

    tags = [
      tagging_result.Tag(name=name, score=score)
      for name, score in tags_scores.items()
    ]
    if n_tags := tagging_options.n_tags:
      tags = self._limit_number_of_tags(tags, n_tags)
    return tagging_result.TaggingResult(
      identifier=medium.name, type='video', content=tags
    )
