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

mode=${1:-"both"}
section=${2:-"all"}

echo "mode: $mode, section $section"

run_tests() {
  if [[ $mode = "both" ]]; then
    echo "running all tests"
    pytest -n auto test_cli.py
    pytest -n auto test_server.py
  elif [[ $mode = "server" ]]; then
    echo "running server tests"
    pytest -n auto test_server.py
  elif [[ $mode = "cli" ]]; then
    echo "running cli tests"
    pytest -n auto test_cli.py
  else
    echo "unknown mode: $mode"
  fi
}

tagging() {
  pushd `pwd`
  cd libs/media_tagging/tests/end-to-end
  run_tests
  popd
}

similarity() {
  pushd `pwd`
  cd libs/media_similarity/tests/end-to-end
  run_tests
  popd
}

filonov() {
  pushd `pwd`
  cd libs/filonov/tests/end-to-end
  run_tests
  popd
}


if [[ $section = "all" ]]; then
  echo "running all tests"
  tagging
  similarity
  filonov
fi

if [[ $section = "tagging" ]]; then
  echo "running tagging tests"
  tagging
elif [[ $section = "similarity" ]]; then
  echo "running similarity tests"
  similarity
elif [[ $section = "filonov" ]]; then
  echo "running filonov tests"
  filonov
else
  echo "unknown section of tests" $section
fi
