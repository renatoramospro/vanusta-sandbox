#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxjt16l-3u4dtk====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'opentelemetry-api' 'opentelemetry-sdk' 'opentelemetry-exporter-otlp'
  python 'tracing_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxjt16l-3u4dtk exit=${code}====="
exit "$code"
