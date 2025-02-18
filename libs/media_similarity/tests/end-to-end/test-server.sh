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

SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
if [ -f $SCRIPT_PATH/.env ]; then
  source $SCRIPT_PATH/.env
fi

cluster() {
  http --print b POST localhost:8000/media_similarity/cluster \
    media_paths[]=$FILONOV_MEDIA_IDENTIFIER_1 \
    media_paths[]=$FILONOV_MEDIA_IDENTIFIER_2 \
    media_paths[]=$FILONOV_MEDIA_IDENTIFIER_3 \
    media_type="YOUTUBE_VIDEO" \
    tagger_type='gemini-youtube-video'
}

search() {
  http --print b \
    localhost:8000/media_similarity/search?seed_media_identifier=$FILONOV_MEDIA_IDENTIFIER_1
}

cluster
search
