#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwz3yf3v-qe8rxh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwz3yf3v-qe8rxh exit=${code}====="
exit "$code"
