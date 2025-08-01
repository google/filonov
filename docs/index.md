# Filonov

> I don't like this

When dealing with huge amounts of creatives (video and images) it might be hard
to identify which creative approaches work the best since actual performance is
usually evaluated on a single creative.

## Key features

* Extracting media from a source (i.e. Google Ads)
* Tagging media
* Clustering media
* Combining into JSON
* Visualization

<div class="grid cards" markdown>

-   :material-console-line: **Installation**

    ----

    Install `garf-executors` to run queries against APIs.

    [:octicons-arrow-right-24: More information](installation.md)

-   :simple-python: **Library**

    ----

    Integrate `garf` into your libraries.

    [:octicons-arrow-right-24: More information](library.md)

-   :material-console-line: **CLI**

    ----

    Execute queries in your terminal.

    [:octicons-arrow-right-24: More information](cli.md)

-   :simple-fastapi: **Server**

    ----

    Run `garf` as FastAPI endpoint.

    [:octicons-arrow-right-24: More information](server.md)
</div>

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
```python
filonov
```
///

/// tab | UI
```python
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

*  Build the app for production
```bash
quasar build
```
