{{- define "zeroTouch.name" -}}
zero-touch-telemetry
{{- end -}}

{{- define "zeroTouch.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "zeroTouch.name" .) -}}
{{- end -}}

{{- define "zeroTouch.labels" -}}
app.kubernetes.io/name: {{ include "zeroTouch.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "zeroTouch.processors" -}}
{{- $processors := list "memory_limiter" "batch" -}}
{{- if lt .Values.collector.samplingRate 1.0 -}}
{{- $processors = prepend $processors "probabilistic_sampler" -}}
{{- end -}}
{{- join ", " $processors -}}
{{- end -}}
