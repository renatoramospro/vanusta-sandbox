#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuixvkw0-01qf9c====="
(
  set -e
  python 'myers_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuixvkw0-01qf9c exit=${code}====="
exit "$code"
