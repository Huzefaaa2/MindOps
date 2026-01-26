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

{{- define "zeroTouch.collectorConfig" -}}
receivers:
  otlp:
    protocols:
      grpc:
      http:

processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 400
  batch:
    timeout: 1s
    send_batch_size: 1024
{{- if lt .Values.collector.samplingRate 1.0 }}
  probabilistic_sampler:
    sampling_percentage: {{ printf "%.1f" (mul .Values.collector.samplingRate 100) }}
{{- end }}

exporters:
{{- if has "logging" .Values.collector.exporters }}
  logging:
    loglevel: info
{{- end }}
{{- if has "otlp" .Values.collector.exporters }}
  otlp:
    endpoint: {{ .Values.collector.otlpExporterEndpoint | quote }}
    tls:
      insecure: true
{{- end }}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [{{ include "zeroTouch.processors" . }}]
      exporters: [{{ join ", " .Values.collector.exporters }}]
    metrics:
      receivers: [otlp]
      processors: [{{ include "zeroTouch.processors" . }}]
      exporters: [{{ join ", " .Values.collector.exporters }}]
    logs:
      receivers: [otlp]
      processors: [{{ include "zeroTouch.processors" . }}]
      exporters: [{{ join ", " .Values.collector.exporters }}]
{{- end -}}
