#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0gb0mv-bsnmp2====="
(
  set -e
  python 'gitops_sync.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0gb0mv-bsnmp2 exit=${code}====="
exit "$code"
