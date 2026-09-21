#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaup8x2-38ac0t====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaup8x2-38ac0t exit=${code}====="
exit "$code"
