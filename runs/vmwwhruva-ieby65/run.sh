#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwhruva-ieby65====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwhruva-ieby65 exit=${code}====="
exit "$code"
