SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
if [ -f $SCRIPT_PATH/.env ]; then
  source $SCRIPT_PATH/.env
fi

run_file() {
  echo "Running in file mode"
  filonov --source file --media-type YOUTUBE_VIDEO \
    --db-uri=$FILONOV_DB_URI \
    --file.tagging_results_path=$FILONOV_TAGGING_RESULTS \
    --file.performance_results_path=$FILONOV_PERFORMANCE_RESULTS \
    --parallel-threshold 10
}
run_googleads() {
  filonov --source googleads --media-type IMAGE \
    --campaign-type $campaign_type \
    --db-uri=$FILONOV_DB_URI \
    --googleads.account=$FILONOV_ACCOUNT_ID \
    --googleads.start-date=$FILONOV_START_DATE --googleads.end-date=$FILONOV_END_DATE \
    --googleads.tagger=vision-api \
    --googleads.ads-config_path=$FILONOV_ADS_CONFIG \
    --parallel-threshold 10 \
    --output-name $output_name
}
run_youtube() {
  echo "Running in youtube mode"
  filonov --source youtube --media-type YOUTUBE_VIDEO \
    --db-uri=$FILONOV_DB_URI \
    --youtube.channel=$FILONOV_YOUTUBE_CHANNEL_ID \
    --parallel-threshold 10 \
    --no-normalize
}
mode=${1:-api}
output_name=${2:-filonov}
campaign_type=${3:-app}
if [[ $mode == 'file' ]]; then
  run_file
elif [[ $mode == 'youtube' ]]; then
  run_youtube
else
  run_googleads
fi
