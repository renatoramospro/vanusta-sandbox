#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxe117b-23ific====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxe117b-23ific exit=${code}====="
exit "$code"
