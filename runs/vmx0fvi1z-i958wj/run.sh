#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0fvi1z-i958wj====="
(
  set -e
  python 'gitops_sync.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0fvi1z-i958wj exit=${code}====="
exit "$code"
