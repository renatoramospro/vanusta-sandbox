#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucs9baz-86wew2====="
(
  set -e
  python 'usability_risk_framework.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucs9baz-86wew2 exit=${code}====="
exit "$code"
