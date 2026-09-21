#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubjgais-3wc4hi====="
(
  set -e
  python 'rbac_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubjgais-3wc4hi exit=${code}====="
exit "$code"
