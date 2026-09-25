#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh7ahk5-dk9sv0====="
(
  set -e
  python 'merkle_tree.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh7ahk5-dk9sv0 exit=${code}====="
exit "$code"
