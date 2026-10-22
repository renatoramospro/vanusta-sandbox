#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvjypoij-2mpstv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvjypoij-2mpstv exit=${code}====="
exit "$code"
