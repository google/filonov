# Filonov

When dealing with huge amounts of media (video, images, texts) it might be hard
to identify which creative approaches work the best since actual performance is
usually evaluated on a single medium.

## Key features

* **[Fetching media](fetching/overview.md)**: Downloading media info from various sources (i.e. Google Ads)
* **[Tagging media](tagging/overview.md)**: Getting content of each media as a tag.
* **[Finding similar media](similarity/overview.md)**: Find similar media and group them into clusters.
* **[Visualizing media](http://filonov-ai.web.app)**: Ready to use dashboard for understanding media performance on tag, media, and cluster levels.


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

## Usage

`filonov` consists of two major parts:

- Data Pipeline
- Data Visualization

### Generating files

/// tab | cli
```bash
filonov \
  --source googleads \
  --googleads.account=ACCOUNT_ID \
  --media-type IMAGE
```
///

/// tab | UI

```bash
filonov-ui
```
///

### Visualizing data

#### Serveless

Data Visualization is a web application uniformly accessible for all users from [http://filonov-ai.web.app](http://filonov-ai.web.app).

It's deployed to Firebase Static Hosting and implemented as serverless web application where users
can open data files generated with the Data Pipeline.


#### Self-hosted

Filonov UI can be run locally.

* Install the dependencies

```bash
npm install
```

* Start the app in development mode (hot-code reloading, error reporting, etc.)

```bash
quasar dev
```

* Build the app for production

```bash
quasar build
```
