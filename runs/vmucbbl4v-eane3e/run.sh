#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucbbl4v-eane3e====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucbbl4v-eane3e exit=${code}====="
exit "$code"
