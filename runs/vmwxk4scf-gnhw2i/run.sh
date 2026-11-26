#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxk4scf-gnhw2i====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'opentelemetry-api' 'opentelemetry-sdk' 'opentelemetry-exporter-otlp'
  python 'tracing_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxk4scf-gnhw2i exit=${code}====="
exit "$code"
