#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujp7csw-1bweyc====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujp7csw-1bweyc exit=${code}====="
exit "$code"
