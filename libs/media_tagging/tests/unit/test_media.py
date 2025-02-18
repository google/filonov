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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import pytest
from media_tagging import media


class TestMedium:
  @pytest.mark.parametrize(
    'prefix',
    [
      'https://www.youtube.com/watch?v=',
      'https://youtube.com/watch?v=',
      'www.youtu.be/shorts/',
      'www.youtu.be/',
      ' http://www.youtube.com/embed/',
    ],
  )
  def test_media_path_normalized_for_youtube_video(self, prefix):
    youtube_video_id = '12345789000'
    test_link = f'{prefix}{youtube_video_id}&rel=0'
    test_medium = media.Medium(
      media_path=test_link, media_type=media.MediaTypeEnum.YOUTUBE_VIDEO
    )
    assert (
      test_medium.media_path
      == f'https://www.youtube.com/watch?v={youtube_video_id}'
    )

  def test_media_path_raises_error_on_youtube_video_link(self):
    incorrect_test_link = 'https://youtube.com/watch?v=1'
    test_medium = media.Medium(
      media_path=incorrect_test_link,
      media_type=media.MediaTypeEnum.YOUTUBE_VIDEO,
    )
    with pytest.raises(media.InvalidMediaPathError):
      assert test_medium.media_path

  def test_media_name_inferred_correctly_from_path(self):
    test_media_path = '/tmp/test_image.png'
    test_medium = media.Medium(
      media_path=test_media_path, media_type=media.MediaTypeEnum.UNKNOWN
    )
    assert test_medium.name == 'test_image'
