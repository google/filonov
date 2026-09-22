{{/*
Expand the name of the chart.
*/}}
{{- define "filonov.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 56 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 56 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "filonov.fullname" -}}
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
{{- define "filonov.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 56 | trimSuffix "-" }}
{{- end }}

{{/*
Worker name.
*/}}
{{- define "filonov.workerName" -}}
{{ printf "%s-worker" (include "filonov.fullname" .) }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "filonov.labels" -}}
helm.sh/chart: {{ include "filonov.chart" . }}
{{ include "filonov.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "filonov.selectorLabels" -}}
app.kubernetes.io/name: {{ include "filonov.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common worker labels
*/}}
{{- define "filonov.workerLabels" -}}
helm.sh/chart: {{ include "filonov.chart" . }}
{{ include "filonov.workerSelectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Worker selector labels
*/}}
{{- define "filonov.workerSelectorLabels" -}}
app.kubernetes.io/name: {{ include "filonov.workerName" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "filonov.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "filonov.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create postgresql connection string for media tagging Db
*/}}
{{- define "filonov.mediaTaggingDb" -}}
{{- if .Values.filonov.taggingDb.connectionString }}
{{- .Values.filonov.taggingDb.connectionString }}
{{- else }}
{{- printf "postgresql+psycopg2://%s:%s@%s-postgresql:%v/%s"
.Values.postgresql.auth.username
.Values.postgresql.auth.postgresPassword
.Release.Name
.Values.postgresql.containerPorts.postgresql
.Values.filonov.taggingDb.name }}
{{- end }}
{{- end }}

{{/*
Create postgresql connection string for media similarity Db
*/}}
{{- define "filonov.mediaSimilarityDb" -}}
{{- if .Values.filonov.similarityDb.connectionString }}
{{- .Values.filonov.similarityDb.connectionString }}
{{- else }}
{{- printf "postgresql+psycopg2://%s:%s@%s-postgresql:%v/%s"
.Values.postgresql.auth.username
.Values.postgresql.auth.postgresPassword
.Release.Name
.Values.postgresql.containerPorts.postgresql
.Values.filonov.similarityDb.name }}
{{- end }}
{{- end }}

{{/*
Create redis connection string
*/}}
{{- define "filonov.redisUrl" -}}
{{- printf "redis://:%s@%s-redis-master:%v/0" .Values.redis.auth.password .Release.Name .Values.redis.master.containerPorts.redis }}
{{- end }}


{{/*
Render env variables
*/}}
{{- define "filonov.renderEnv" -}}
{{- range $key, $val := . }}
- name: {{ $key }}
  {{- if kindIs "map" $val }}
{{ toYaml $val | indent 2 }}
  {{- else }}
  value: {{ $val | quote }}
  {{- end }}
{{- end }}
{{- end -}}
