#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucoyyvr-w5wvo5====="
(
  set -e
  python 'legacy_risk_model.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucoyyvr-w5wvo5 exit=${code}====="
exit "$code"
