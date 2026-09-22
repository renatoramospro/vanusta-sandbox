#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuch7t1a-kdhung====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuch7t1a-kdhung exit=${code}====="
exit "$code"
