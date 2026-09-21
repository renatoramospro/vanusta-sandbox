#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubmkubt-o07tdc====="
(
  set -e
  python 'tracing_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubmkubt-o07tdc exit=${code}====="
exit "$code"
