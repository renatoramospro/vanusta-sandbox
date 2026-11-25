#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwh0ucg-xjmakp====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwh0ucg-xjmakp exit=${code}====="
exit "$code"
