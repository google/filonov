{{/*
Expand the name of the chart.
*/}}
{{- define "media-tagging.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 56 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 56 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "media-tagging.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 56 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 56 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 56 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "media-tagging.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 56 | trimSuffix "-" }}
{{- end }}

{{/*
Worker name.
*/}}
{{- define "media-tagging.workerName" -}}
{{ printf "%s-worker" (include "media-tagging.fullname" .) }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "media-tagging.labels" -}}
helm.sh/chart: {{ include "media-tagging.chart" . }}
{{ include "media-tagging.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "media-tagging.selectorLabels" -}}
app.kubernetes.io/name: {{ include "media-tagging.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common worker labels
*/}}
{{- define "media-tagging.workerLabels" -}}
helm.sh/chart: {{ include "media-tagging.chart" . }}
{{ include "media-tagging.workerSelectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Worker selector labels
*/}}
{{- define "media-tagging.workerSelectorLabels" -}}
app.kubernetes.io/name: {{ include "media-tagging.workerName" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "media-tagging.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "media-tagging.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create redis connection string
*/}}
{{- define "media-tagging.redisUrl" -}}
{{- printf "redis://:%s@%s-redis-master:%v/0" .Values.redis.auth.password .Release.Name .Values.redis.master.containerPorts.redis }}
{{- end }}

{{/*
Create postgresql connection string for media tagging Db
*/}}
{{- define "media-tagging.mediaTaggingDb" -}}
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
Render env variables
*/}}
{{- define "media-tagging.renderEnv" -}}
{{- range $key, $val := . }}
- name: {{ $key }}
  {{- if kindIs "map" $val }}
{{ toYaml $val | indent 2 }}
  {{- else }}
  value: {{ $val | quote }}
  {{- end }}
{{- end }}
{{- end -}}
