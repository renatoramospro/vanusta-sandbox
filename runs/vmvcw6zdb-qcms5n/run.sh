#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcw6zdb-qcms5n====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcw6zdb-qcms5n exit=${code}====="
exit "$code"
