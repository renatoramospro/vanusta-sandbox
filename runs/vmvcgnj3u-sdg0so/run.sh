#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcgnj3u-sdg0so====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcgnj3u-sdg0so exit=${code}====="
exit "$code"
