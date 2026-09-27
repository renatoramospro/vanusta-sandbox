#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujfk3mn-z1etd1====="
(
  set -e
  python 'vector_clock.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujfk3mn-z1etd1 exit=${code}====="
exit "$code"
