{{/*
Expand the name of the chart.
*/}}
{{- define "harvester.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this
(by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "harvester.fullname" -}}
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
Create chart label value: <chart-name>-<chart-version>
*/}}
{{- define "harvester.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels applied to every resource.
*/}}
{{- define "harvester.labels" -}}
helm.sh/chart: {{ include "harvester.chart" . }}
{{ include "harvester.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels — stable subset used for Service/pod selectors.
*/}}
{{- define "harvester.selectorLabels" -}}
app.kubernetes.io/name: {{ include "harvester.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Name of the ServiceAccount to use.
*/}}
{{- define "harvester.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "harvester.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Full image reference: registry/repository:tag
Uses values.image.tag when set; falls back to Chart.AppVersion.
*/}}
{{- define "harvester.image" -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion }}
{{- printf "%s/%s:%s" .Values.image.registry .Values.image.repository $tag }}
{{- end }}

{{/*
Name of the ConfigMap holding config.yaml.
*/}}
{{- define "harvester.configMapName" -}}
{{- printf "%s-config" (include "harvester.fullname" .) }}
{{- end }}

{{/*
Name of the Secret holding mTLS client certificates.
*/}}
{{- define "harvester.tlsSecretName" -}}
{{- printf "%s-tls" (include "harvester.fullname" .) }}
{{- end }}
