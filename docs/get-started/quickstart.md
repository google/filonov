[![PyPI](https://img.shields.io/pypi/v/filonov?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/filonov)
[![Downloads PyPI](https://img.shields.io/pypi/dw/filonov?logo=pypi)](https://pypi.org/project/filonov/)

Let's use `filonov` to analyze images in Google Ads App campaigns.

## Installation

/// tab | pip
```python
pip install filonov
```
///

/// tab | uv
```python
uv pip install filonov
```
///

## Run filonov

In order to analyze images we need to provide an account to get data from (replace `GOOGLE_ADS_ACCOUNT_ID` in the command below with an actual Google Ads account number).


/// tab | cli

```bash
filonov --source googleads --media-type IMAGE \
  --tagger gemini \
  --googleads.account=GOOGLE_ADS_ACCOUNT_ID
```
///

/// tab | python

```python
import filonov

service = filonov.FilonovService()

request = filonov.GenerateCreativeMapRequest(
  source='googleads',
  media_type='IMAGE',
  tagger='gemini',
  source_parameters={'account': 'GOOGLE_ADS_ACCOUNT_ID'}
)

creative_map = service.generate_creative_map(request)
creative_map.save('creative_map')

```
///

/// tab | curl
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/filonov/creative_map/googleads' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "media_type": "IMAGE",
  "tagger": "gemini",
  "source_parameters": {
    "account": "GOOGLE_ADS_ACCOUNT_ID"
  }
}'
```
///

This command will do the following:

* Find all unique images in Google Ads App campaigns for the last 30 days with non-zero impressions.
* Tag each images with Gemini tagger.
* Find similarity between images and assign unique cluster number of each one of them.
* Save result into `creative_map.json` file.


## Visualize results

Once `creative_map.json` file is generated it can be used at
[http://filonov-ai.web.app](http://filonov-ai.web.app).

![Load data](load.png){ loading=lazy }


## Next steps

Congratulations, you just created your first creative map with `filonov`!

Now you can explore what you can do:

* [Customize](customization.md) `filonov`: work with different [sources](customization.md#source) and [media types](customization.md#media-types).
* Use components of `filonov` - [`media-tagging`](../tagging/overview.md), [`media-fetching`](../fetching/overview.md) and [`media-similarity`](../similarity/overview.md) in your own applications.
