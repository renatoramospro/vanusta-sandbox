#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujyf4a8-adg5es====="
(
  set -e
  python 'bplus_tree.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujyf4a8-adg5es exit=${code}====="
exit "$code"
