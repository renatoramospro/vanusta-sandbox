#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxgt69l-qgx8uk====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxgt69l-qgx8uk exit=${code}====="
exit "$code"
