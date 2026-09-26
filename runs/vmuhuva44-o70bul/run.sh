#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhuva44-o70bul====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhuva44-o70bul exit=${code}====="
exit "$code"
