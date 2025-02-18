# Copyright 2023 Google LLC
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
SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
if [ -f $SCRIPT_PATH/.env ]; then
  source $SCRIPT_PATH/.env
fi

cluster() {
  media-similarity cluster \
    $FILONOV_MEDIA_IDENTIFIER_1 \
    $FILONOV_MEDIA_IDENTIFIER_2 \
    $FILONOV_MEDIA_IDENTIFIER_3 \
    --media-type='YOUTUBE_VIDEO' \
		--tagger='gemini-youtube-video' \
		--db-uri $FILONOV_DB_URI
}

search() {
  media-similarity search $FILONOV_MEDIA_IDENTIFIER_1 \
		--db-uri $FILONOV_DB_URI
}

cluster
search
