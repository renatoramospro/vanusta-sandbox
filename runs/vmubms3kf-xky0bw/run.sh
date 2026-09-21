#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubms3kf-xky0bw====="
(
  set -e
  python 'tracing_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubms3kf-xky0bw exit=${code}====="
exit "$code"
