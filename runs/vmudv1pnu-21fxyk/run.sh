#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudv1pnu-21fxyk====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'PyYAML==6.0.1'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudv1pnu-21fxyk exit=${code}====="
exit "$code"
