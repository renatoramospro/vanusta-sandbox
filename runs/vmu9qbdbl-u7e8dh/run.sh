#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9qbdbl-u7e8dh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9qbdbl-u7e8dh exit=${code}====="
exit "$code"
