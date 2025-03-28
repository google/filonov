SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
if [ -f $SCRIPT_PATH/.env ]; then
  source $SCRIPT_PATH/.env
fi

tag() {
  local tagger=$1
  http --print b POST localhost:8000/media_tagging/tag \
    media_paths[]=$IMAGE \
    tagger_type=$1 \
    media_type="IMAGE"

}

describe() {
  local tagger=$1
  http --print b POST localhost:8000/media_tagging/describe \
    media_paths[]=$IMAGE \
    tagger_type=$1 \
    media_type="IMAGE"

}

for tagger in 'gemini' 'langchain' 'google-cloud'; do
  tag $tagger
  describe $tagger
done
