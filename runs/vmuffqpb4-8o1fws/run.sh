#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuffqpb4-8o1fws====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuffqpb4-8o1fws exit=${code}====="
exit "$code"
