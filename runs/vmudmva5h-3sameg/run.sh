#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudmva5h-3sameg====="
(
  set -e
  python 'data_lineage_extractor.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudmva5h-3sameg exit=${code}====="
exit "$code"
