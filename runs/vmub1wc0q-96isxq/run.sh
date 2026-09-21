#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub1wc0q-96isxq====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub1wc0q-96isxq exit=${code}====="
exit "$code"
