#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwhcg7p-zs49jq====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwhcg7p-zs49jq exit=${code}====="
exit "$code"
