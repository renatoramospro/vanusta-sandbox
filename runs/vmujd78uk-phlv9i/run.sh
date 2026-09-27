#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujd78uk-phlv9i====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujd78uk-phlv9i exit=${code}====="
exit "$code"
