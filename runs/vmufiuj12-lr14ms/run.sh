#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufiuj12-lr14ms====="
(
  set -e
  python 'feature_flags_corrected.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufiuj12-lr14ms exit=${code}====="
exit "$code"
