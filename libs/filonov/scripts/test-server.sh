SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
if [ -f $SCRIPT_PATH/.env ]; then
  source $SCRIPT_PATH/.env
fi

tag() {
  http --print b POST localhost:8000/creative_map \
    source='googleads' \
    tagger='vision-api' \
    media_type='IMAGE' \
    input_parameters[account]=$FILONOV_ACCOUNT_ID \
    input_parameters[campaign_types]='demandgen' \
    input_parameters[ads_config_path]=$FILONOV_ADS_CONFIG
}

tag
