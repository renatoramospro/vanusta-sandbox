#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhiyzou-dtd85g====="
(
  set -e
  python 'router_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhiyzou-dtd85g exit=${code}====="
exit "$code"
