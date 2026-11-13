# Filonov Helm charts

## Quick start

```bash
helm repo add filonov https://google.github.io/filonov/
helm repo update
helm install RELEASE_NAME filonov/CHART_NAME -n filonov --create-namespace
```
## Charts


* `media-tagging` - performs tagging of various media (image, text, webpage, video) via LLMs.
* `media-fetching` - extract media performance information from various sources (Google Ads, YouTube, File, DBs, etc.)
* `media-similarity` - performs similarity detection and clustering of various media.
* `filonov` - combines all functionality above into AI concept analysis toolkit.

## Customization

### media-tagging

You can customize Helm chart by overwriting default values:

* `mediaTagging.server.type` - choose between http or grpc (http is default one).
* `mediaTagging.worker.enabled` - whether to enable celery worker (enabled by default).
* `mediaTagging.otel.enabled` - whether to sending data to OpenTelemetry collector (disabled by default).
* `mediaTagging.taggingDb.enabled` - whether to create Postgres DB for storing tagging results.
* `mediaTagging.taggingDb.connectionString` - connection string to existing Postgres DB.

```yaml
mediaTagging:
  server:
    type: http
    replicaCount: 1
  worker:
    enabled: false
    replicaCount: 1
  otel:
    enabled: false
    serviceName: media-tagging
    otelExporterOtlpEndpoint: ""
  taggingDb:
    enabled: false
    name: media_tagging
    connectionString: ""
```

### media-similarity

You can customize Helm chart by overwriting default values:

* `mediaSimilarity.taggingDb.enabled` - whether to create / use existing Postgres DB for storing tagging results.
* `mediaSimilarity.taggingDb.connectionString` - connection string to existing Postgres DB.
* `mediaSimilarity.similarityDb.enabled` - whether to create / use existing Postgres DB for storing similarity results.
* `mediaSimilarity.similarityDb.connectionString` - connection string to existing Postgres DB.

```yaml
mediaSimilarity:
  taggingDb:
    enabled: false
    name: media_tagging
    connectionString: ""
  similarityDb:
    enabled: false
    name: media_similarity
    connectionString: ""
```
### filonov

You can customize Helm chart by overwriting default values:

* `filonov.server.type` - choose between http or grpc (http is default one).
* `filonov.worker.enabled` - whether to enable celery worker (enabled by default).
* `filonov.otel.enabled` - whether to sending data to OpenTelemetry collector (disabled by default).
* `filonov.taggingDb.enabled` - whether to create Postgres DB for storing tagging results.
* `filonov.taggingDb.connectionString` - connection string to existing Postgres DB.
* `filonov.similarityDb.enabled` - whether to create / use existing Postgres DB for storing similarity results.
* `filonov.similarityDb.connectionString` - connection string to existing Postgres DB.


```yaml
filonov:
  server:
    type: http
    replicaCount: 1
  worker:
    enabled: false
    replicaCount: 1
  otel:
    enabled: false
    serviceName: filonov
    otelExporterOtlpEndpoint: ""
  taggingDb:
    enabled: false
    name: media_tagging
    connectionString: ""
  similarityDb:
    enabled: false
    name: media_similarity
    connectionString: ""
```


### Postgres

If you enable DBs, you might want to override some default Postgres values.

```yaml
postgresql:
  image:
    tag: latest
  auth:
    enabled: true
    username: "postgres"
    postgresPassword: "postgres_admin123"
    password: "postgres_admin123"
  architecture: "standalone"
  primary:
    persistence:
      enabled: true
      size: "8Gi"

```
### Redis

If you enable worker, you might want to override some default redis values.

```yaml
redis:
  enabled: true

  auth:
    enabled: true
    password: "redisadmin123"
  architecture: "standalone"
  master:
    persistence:
      enabled: true
      size: "1Gi"
```

To explore the full values that can be customized dump them to `values.yaml`:


```bash
helm show values filonov/CHART_NAME > values.yaml
```

Once you set necessary configuration options, you can apply them:

```bash
helm upgrade RELEASE_NAME filonov/CHART_NAME -n filonov -f values.yaml
```

## Uninstall

```bash
helm uninstall RELEASE_NAME -n filonov
```
