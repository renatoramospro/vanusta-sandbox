#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvpu9ebu-nvc3qh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvpu9ebu-nvc3qh exit=${code}====="
exit "$code"
