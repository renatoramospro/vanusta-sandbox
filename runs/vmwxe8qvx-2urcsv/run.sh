#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxe8qvx-2urcsv====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxe8qvx-2urcsv exit=${code}====="
exit "$code"
