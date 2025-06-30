tagging() {
  pushd `pwd`
  cd libs/media_tagging/tests/end-to-end
  pytest -n auto test_cli.py
  popd
}

similarity() {
  pushd `pwd`
  cd libs/media_similarity/tests/end-to-end
  pytest -n auto test_cli.py
  popd
}

filonov() {
  pushd `pwd`
  cd libs/filonov/tests/end-to-end
  pytest -n auto test_cli.py
  popd
}


tagging
similarity
filonov
