#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua88bpk-54agjb====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua88bpk-54agjb exit=${code}====="
exit "$code"
