#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx6b4ki-r5kcs3====="
(
  set -e
  python 'thread_pool_corrected.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx6b4ki-r5kcs3 exit=${code}====="
exit "$code"
