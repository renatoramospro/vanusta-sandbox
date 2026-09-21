#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubt6jc6-ft2xko====="
(
  set -e
  python 'orchestrator_secure.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubt6jc6-ft2xko exit=${code}====="
exit "$code"
