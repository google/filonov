SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
if [ -f $SCRIPT_PATH/.env ]; then
  source $SCRIPT_PATH/.env
fi

run_vision_api_image() {
  media-tagger \
    --media-path $IMAGE \
    --tagger vision-api \
    --media-type IMAGE \
    --db-uri $FILONOV_DB_URI
}
run_gemini_unstructured_image() {
  media-tagger \
    --media-path $IMAGE \
    --media-type IMAGE \
    --tagger gemini-image \
    --writer json --output output_unstructured \
    --db-uri $FILONOV_DB_URI \
    --tagger.n_tags=10
}

run_gemini_structured_image() {
  media-tagger \
    --media-path $IMAGE \
    --media-type IMAGE \
    --tagger gemini-structured-image \
    --writer json --output output_structured \
    --db-uri $FILONOV_DB_URI \
    --tagger.tags='fitness, dog, yoga'
}

run_gemini_description_image() {
  media-tagger \
    --media-path $IMAGE \
    --media-type IMAGE \
    --tagger gemini-description-image \
    --db-uri $FILONOV_DB_URI \
    --writer json --output output_description
}

run_gemini_unstructured_video() {
  media-tagger \
    --media-path $VIDEO \
    --media-type VIDEO \
    --tagger gemini-video \
    --writer json --output output_video_unstructured \
    --db-uri $FILONOV_DB_URI \
    --tagger.n_tags=10
}

run_gemini_structured_video() {
  media-tagger \
    --media-path $VIDEO \
    --media-type VIDEO \
    --tagger gemini-structured-video \
    --writer json --output output_video_structured \
    --db-uri $FILONOV_DB_URI \
    --tagger.tags='fitness, dog, yoga'
}

run_gemini_description_video() {
  media-tagger \
    --media-path $VIDEO \
    --media-type VIDEO \
    --tagger gemini-description-video \
    --db-uri $FILONOV_DB_URI \
    --writer json --output output_video_description
    }
run_gemini_unstructured_youtube_video() {
  media-tagger \
    --media-path $YOUTUBE_LINK \
    --media-type YOUTUBE_VIDEO \
    --tagger gemini-youtube-video \
    --writer json --output output_youtube_video_unstructured \
    --db-uri $FILONOV_DB_URI \
    --tagger.n_tags=10
}

run_gemini_structured_youtube_video() {
  media-tagger \
    --media-path $YOUTUBE_LINK \
    --media-type YOUTUBE_VIDEO \
    --tagger gemini-structured-youtube-video \
    --writer json --output output_youtube_video_structured \
    --db-uri $FILONOV_DB_URI \
    --tagger.tags='fitness, dog, yoga'
}

run_gemini_description_youtube_video() {
  media-tagger \
    --media-path $YOUTUBE_LINK \
    --media-type YOUTUBE_VIDEO \
    --tagger gemini-description-youtube-video \
    --db-uri $FILONOV_DB_URI \
    --writer json --output output_youtube_video_description
    }

run_vision_api_image
run_gemini_unstructured_image
run_gemini_structured_image
run_gemini_description_image
run_gemini_unstructured_video
run_gemini_structured_video
run_gemini_description_video
run_gemini_unstructured_youtube_video
run_gemini_structured_youtube_video
run_gemini_description_youtube_video
