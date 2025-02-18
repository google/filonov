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
    --parallel-threshold 10 \
    --output-name TEST_JSON_DATA_GOOGLE_FILE
}
run_googleads() {
  filonov --source googleads --media-type IMAGE \
    --db-uri=$FILONOV_DB_URI \
    --tagger=gemini-image \
    --googleads.account=$FILONOV_ACCOUNT_ID \
    --googleads.start-date=$FILONOV_START_DATE --googleads.end-date=$FILONOV_END_DATE \
    --googleads.campaign_types=$FILONOV_CAMPAIGN_TYPE \
    --googleads.ads-config_path=$FILONOV_ADS_CONFIG \
    --parallel-threshold 10 \
    --output-name TEST_JSON_DATA_GOOGLE_ADS
}
run_youtube() {
  echo "Running in youtube mode"
  filonov --source youtube --media-type YOUTUBE_VIDEO \
    --db-uri=$FILONOV_DB_URI \
    --youtube.channel=$FILONOV_YOUTUBE_CHANNEL_ID \
    --parallel-threshold 10 \
    --no-normalize \
    --output-name TEST_JSON_DATA_YOUTUBE
}
run_file
run_googleads
run_youtube
