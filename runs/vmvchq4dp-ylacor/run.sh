#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvchq4dp-ylacor====="
(
  set -e
  python 'jemalloc_sim.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvchq4dp-ylacor exit=${code}====="
exit "$code"
