#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwy1x81s-e5t5ef====="
(
  set -e
  python 'protocol_module.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwy1x81s-e5t5ef exit=${code}====="
exit "$code"
