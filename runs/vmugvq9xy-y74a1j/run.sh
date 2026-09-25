#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmugvq9xy-y74a1j====="
(
  set -e
  python 'crdt.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmugvq9xy-y74a1j exit=${code}====="
exit "$code"
