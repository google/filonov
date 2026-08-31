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
import media_fetching.version as fetching_version
import media_similarity.version as similarity_version
import media_tagging.version as tagging_version

__version__ = '0.11.4'
tagging_version = tagging_version.__version__
fetching_version = fetching_version.__version__
similarity_version = similarity_version.__version__
