#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucolztr-dto5mz====="
(
  set -e
  python 'legacy_risk_model.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucolztr-dto5mz exit=${code}====="
exit "$code"
