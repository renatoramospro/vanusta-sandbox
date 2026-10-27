#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvr4zhk6-gvvdfh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvr4zhk6-gvvdfh exit=${code}====="
exit "$code"
