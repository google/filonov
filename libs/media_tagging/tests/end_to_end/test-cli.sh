SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
if [ -f $SCRIPT_PATH/.env ]; then
  source $SCRIPT_PATH/.env
fi

tag() {
  local tagger=$1
  local media_type=$2
  media-tagger tag \
    $IMAGE \
    --tagger $1 \
    --media-type $media_type
}

describe() {
  local tagger=$1
  local media_type=$2
  media-tagger tag \
    $IMAGE \
    --tagger $1 \
    --media-type $media_type
}

for tagger in 'gemini' 'langchain' 'google-cloud'; do
  tag $tagger IMAGE
  describe $tagger IMAGE
done
