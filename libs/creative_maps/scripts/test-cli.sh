SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
if [ -f $SCRIPT_PATH/.env ]; then
  source $SCRIPT_PATH/.env
fi

run_file() {
  echo "Running in file mode"
  filonov --mode file --media-type YOUTUBE_VIDEO \
    --db-uri=$FILONOV_DB_URI \
    --file.tagging_results_path=$FILONOV_TAGGING_RESULTS \
    --file.performance_results_path=$FILONOV_PERFORMANCE_RESULTS \
    --parallel-threshold 10
}
run_googleads() {
  echo "Running in googleads mode"
  filonov --mode googleads --media-type IMAGE \
    --campaign-type pmax \
    --db-uri=$FILONOV_DB_URI \
    --api.account=$FILONOV_ACCOUNT_ID \
    --api.start-date=$FILONOV_START_DATE --api.end-date=$FILONOV_END_DATE \
    --api.tagger=vision-api \
    --api.ads-config_path=$FILONOV_ADS_CONFIG \
    --parallel-threshold 10 \
    --no-normalize
}
run_youtube() {
  echo "Running in youtube mode"
  filonov --mode youtube --media-type YOUTUBE_VIDEO \
    --db-uri=$FILONOV_DB_URI \
    --youtube.channel=$FILONOV_YOUTUBE_CHANNEL_ID \
    --parallel-threshold 10 \
    --no-normalize
}
mode=${1:api}
if [[ $mode == 'file' ]]; then
  run_file
elif [[ $mode == 'youtube' ]]; then
  run_youtube
else
  run_googleads
fi
