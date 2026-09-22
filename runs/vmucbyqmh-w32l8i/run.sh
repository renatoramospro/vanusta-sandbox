#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucbyqmh-w32l8i====="
(
  set -e
  python 'maso_model.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucbyqmh-w32l8i exit=${code}====="
exit "$code"
