#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucce5lh-jmur9g====="
(
  set -e
  python 'maso_model.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucce5lh-jmur9g exit=${code}====="
exit "$code"
