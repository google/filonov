SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
if [ -f $SCRIPT_PATH/.env ]; then
  source $SCRIPT_PATH/.env
fi

tag() {
  http --print b POST localhost:8000/media_tagging/tag \
    media_paths[]=$YOUTUBE_LINK \
    tagger_type="gemini-youtube-video" \
    media_type="YOUTUBE_VIDEO"

}

tag
