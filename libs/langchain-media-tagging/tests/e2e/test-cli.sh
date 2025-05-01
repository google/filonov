SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
if [ -f $SCRIPT_PATH/.env ]; then
  source $SCRIPT_PATH/.env
fi

tag() {
  local tagger=$1
  local media_type=$2
  local media_url=$3
  echo "[Tagger $tagger] Tagging $media_type: $media_url..."
  media-tagger tag \
    $media_url \
    --tagger $tagger \
    --media-type $media_type \
    --writer console "$@"

}

describe() {
  local tagger=$1
  local media_type=$2
  local media_url=$3
  echo "[Tagger $tagger] Describing $media_type: $media_url..."
  media-tagger describe \
    $media_url \
    --tagger $tagger \
    --media-type $media_type \
    --writer console "$@"
}
media_type="IMAGE"

tag "langchain" $media_type "${!media_type}" \
  --tagger.llm_class_name=langchain_google_genai.ChatGoogleGenerativeAI \
  --tagger.model=gemini-2.0-flash
describe  "langchain" $media_type "${!media_type}" \
  --tagger.llm_class_name=langchain_google_genai.ChatGoogleGenerativeAI \
  --tagger.model=gemini-2.0-flash
