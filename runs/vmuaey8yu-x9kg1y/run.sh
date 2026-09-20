#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaey8yu-x9kg1y====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaey8yu-x9kg1y exit=${code}====="
exit "$code"
