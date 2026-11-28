#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0gmn78-dz2jec====="
(
  set -e
  python 'gitops_sync.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0gmn78-dz2jec exit=${code}====="
exit "$code"
