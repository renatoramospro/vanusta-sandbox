#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucoea04-qt1c9k====="
(
  set -e
  python 'legacy_risk_model.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucoea04-qt1c9k exit=${code}====="
exit "$code"
