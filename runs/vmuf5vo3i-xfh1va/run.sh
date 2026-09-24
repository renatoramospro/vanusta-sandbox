#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf5vo3i-xfh1va====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf5vo3i-xfh1va exit=${code}====="
exit "$code"
