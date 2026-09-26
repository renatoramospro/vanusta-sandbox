#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhubzc7-ykrc94====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhubzc7-ykrc94 exit=${code}====="
exit "$code"
