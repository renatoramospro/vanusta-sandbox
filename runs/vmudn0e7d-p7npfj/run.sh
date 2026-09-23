#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudn0e7d-p7npfj====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'sqlglot==20.11.0'
  python 'data_lineage_extractor.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudn0e7d-p7npfj exit=${code}====="
exit "$code"
