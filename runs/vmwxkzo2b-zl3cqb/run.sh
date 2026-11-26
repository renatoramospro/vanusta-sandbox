#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxkzo2b-zl3cqb====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'opentelemetry-api' 'opentelemetry-sdk' 'opentelemetry-exporter-otlp'
  python 'tracing_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxkzo2b-zl3cqb exit=${code}====="
exit "$code"
