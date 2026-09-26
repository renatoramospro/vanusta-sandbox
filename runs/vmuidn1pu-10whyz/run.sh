#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuidn1pu-10whyz====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuidn1pu-10whyz exit=${code}====="
exit "$code"
