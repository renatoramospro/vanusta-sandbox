#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub4kc72-2kxi59====="
(
  set -e
  python 'pcg_pipeline.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub4kc72-2kxi59 exit=${code}====="
exit "$code"
