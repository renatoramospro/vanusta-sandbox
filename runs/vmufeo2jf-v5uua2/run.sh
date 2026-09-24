#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufeo2jf-v5uua2====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufeo2jf-v5uua2 exit=${code}====="
exit "$code"
