#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujepbca-6dqouh====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujepbca-6dqouh exit=${code}====="
exit "$code"
