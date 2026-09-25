#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhijizu-q76clp====="
(
  set -e
  python 'router_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhijizu-q76clp exit=${code}====="
exit "$code"
