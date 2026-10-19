#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvfjkhc3-x8t1fv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvfjkhc3-x8t1fv exit=${code}====="
exit "$code"
