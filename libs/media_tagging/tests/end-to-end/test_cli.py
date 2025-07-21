# Copyright 2025 Google LLC
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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-class-docstring, missing-module-docstring, missing-function-docstring

import os
import subprocess

import dotenv
import pytest

dotenv.load_dotenv()

filonov_test_text = '"To be or not to be this is the question."'


@pytest.mark.tagger
class TestMediaTagger:
  @pytest.mark.gemini
  class TestGeminiTagger:
    tagger = 'gemini'

    @pytest.mark.parametrize(
      ('media_type', 'media_location'),
      [
        ('TEXT', filonov_test_text),
        ('IMAGE', os.getenv('FILONOV_IMAGE_PATH')),
        ('VIDEO', os.getenv('FILONOV_VIDEO_PATH')),
        ('YOUTUBE_VIDEO', os.getenv('FILONOV_YOUTUBE_LINK')),
      ],
    )
    def test_tag(self, media_type, media_location):
      command = (
        f'media-tagger tag {media_location} '
        f'--tagger {self.tagger} --media-type {media_type} --writer console'
      )
      result = subprocess.run(command, shell=True, check=False)
      assert result.returncode == 0

    @pytest.mark.parametrize(
      ('media_type', 'media_location'),
      [
        ('TEXT', filonov_test_text),
        ('IMAGE', os.getenv('FILONOV_IMAGE_PATH')),
        ('VIDEO', os.getenv('FILONOV_VIDEO_PATH')),
        ('YOUTUBE_VIDEO', os.getenv('FILONOV_YOUTUBE_LINK')),
      ],
    )
    def test_describe(self, media_type, media_location):
      command = (
        f'media-tagger describe {media_location} '
        f'--tagger {self.tagger} --media-type {media_type} --writer console'
      )
      result = subprocess.run(command, shell=True, check=False)
      assert result.returncode == 0

  @pytest.mark.google_cloud
  class TestGoogleCloudTagger:
    tagger = 'google-cloud'

    @pytest.mark.parametrize(
      ('media_type', 'media_location', 'expected_return_code'),
      [
        ('TEXT', filonov_test_text, 1),
        ('IMAGE', os.getenv('FILONOV_IMAGE_PATH'), 0),
        ('VIDEO', os.getenv('FILONOV_VIDEO_PATH'), 0),
        ('YOUTUBE_VIDEO', os.getenv('FILONOV_YOUTUBE_LINK'), 1),
      ],
    )
    def test_tag(self, media_type, media_location, expected_return_code):
      command = (
        f'media-tagger tag {media_location} '
        f'--tagger {self.tagger} --media-type {media_type} --writer console'
      )
      result = subprocess.run(command, shell=True, check=False)
      assert result.returncode == expected_return_code

    @pytest.mark.parametrize(
      ('media_type', 'media_location'),
      [
        ('TEXT', filonov_test_text),
        ('IMAGE', os.getenv('FILONOV_IMAGE_PATH')),
        ('VIDEO', os.getenv('FILONOV_VIDEO_PATH')),
        ('YOUTUBE_VIDEO', os.getenv('FILONOV_YOUTUBE_LINK')),
      ],
    )
    def test_describe(self, media_type, media_location):
      command = (
        f'media-tagger describe {media_location} '
        f'--tagger {self.tagger} --media-type {media_type} --writer console'
      )
      result = subprocess.run(command, shell=True, check=False)
      assert result.returncode == 1
