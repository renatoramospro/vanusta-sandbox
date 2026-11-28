#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0fnxlr-awczon====="
(
  set -e
  python 'gitops_sync.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0fnxlr-awczon exit=${code}====="
exit "$code"
