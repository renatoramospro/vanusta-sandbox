#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh42psy-2dfi7o====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh42psy-2dfi7o exit=${code}====="
exit "$code"
