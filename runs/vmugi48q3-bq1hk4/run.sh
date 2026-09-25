#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugi48q3-bq1hk4====="
(
  set -e
  python 'saga_coreografada.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugi48q3-bq1hk4 exit=${code}====="
exit "$code"
