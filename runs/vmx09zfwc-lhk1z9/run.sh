#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx09zfwc-lhk1z9====="
(
  set -e
  python 'simulator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx09zfwc-lhk1z9 exit=${code}====="
exit "$code"
