#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiic9dc-5a5o0z====="
(
  set -e
  python 'smtp_experiment_v2.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiic9dc-5a5o0z exit=${code}====="
exit "$code"
