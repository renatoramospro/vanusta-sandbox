#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhyetpq-vponb9====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhyetpq-vponb9 exit=${code}====="
exit "$code"
