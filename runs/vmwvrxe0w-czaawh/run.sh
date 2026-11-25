#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwvrxe0w-czaawh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwvrxe0w-czaawh exit=${code}====="
exit "$code"
