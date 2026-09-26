#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuikl5zx-mp1r7p====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuikl5zx-mp1r7p exit=${code}====="
exit "$code"
