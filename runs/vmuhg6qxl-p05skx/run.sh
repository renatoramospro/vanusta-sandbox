#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhg6qxl-p05skx====="
(
  set -e
  python 'regex_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhg6qxl-p05skx exit=${code}====="
exit "$code"
