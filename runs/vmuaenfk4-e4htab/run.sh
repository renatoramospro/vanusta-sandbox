#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaenfk4-e4htab====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaenfk4-e4htab exit=${code}====="
exit "$code"
