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

import csv
import subprocess


def test_load_tags(tmp_path):
  db_uri = f'sqlite:///{tmp_path}/test.db'
  tags_file_path = tmp_path / 'tags.csv'

  header = ['media_url', 'tag', 'score']
  values = ['example.com', 'test', 1.0]

  with open(tags_file_path, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerow(values)

  command = (
    f'media-loader {str(tags_file_path)} --action tag '
    f'--loader file --media-type WEBPAGE --db-uri {db_uri}'
  )
  result = subprocess.run(command, shell=True, check=False)
  assert result.returncode == 0
