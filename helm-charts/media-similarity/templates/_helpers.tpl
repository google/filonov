{{/*
Expand the name of the chart.
*/}}
{{- define "media-similarity.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "media-similarity.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "media-similarity.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "media-similarity.labels" -}}
helm.sh/chart: {{ include "media-similarity.chart" . }}
{{ include "media-similarity.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "media-similarity.selectorLabels" -}}
app.kubernetes.io/name: {{ include "media-similarity.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "media-similarity.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "media-similarity.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create postgresql connection string for media tagging Db
*/}}
{{- define "media-similarity.mediaTaggingDb" -}}
{{- if .Values.mediaSimilarity.taggingDb.connectionString }}
{{- .Values.mediaSimilarity.taggingDb.connectionString }}
{{- else }}
{{- printf "postgresql+psycopg2://%s:%s@%s-postgresql:%v/%s"
.Values.postgresql.auth.username
.Values.postgresql.auth.postgresPassword
.Release.Name
.Values.postgresql.containerPorts.postgresql
.Values.mediaSimilarity.taggingDb.name }}
{{- end }}
{{- end }}

{{/*
Create postgresql connection string for media similarity Db
*/}}
{{- define "media-similarity.mediaSimilarityDb" -}}
{{- if .Values.mediaSimilarity.similarityDb.connectionString }}
{{- .Values.mediaSimilarity.similarityDb.connectionString }}
{{- else }}
{{- printf "postgresql+psycopg2://%s:%s@%s-postgresql:%v/%s"
.Values.postgresql.auth.username
.Values.postgresql.auth.postgresPassword
.Release.Name
.Values.postgresql.containerPorts.postgresql
.Values.mediaSimilarity.similarityDb.name }}
{{- end }}
{{- end }}


{{/*
Render env variables
*/}}
{{- define "media-similarity.renderEnv" -}}
{{- range $key, $val := . }}
- name: {{ $key }}
  {{- if kindIs "map" $val }}
{{ toYaml $val | indent 2 }}
  {{- else }}
  value: {{ $val | quote }}
  {{- end }}
{{- end }}
{{- end -}}
