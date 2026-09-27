#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk3s0wj-cgftkr====="
(
  set -e
  python 'mvcc_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk3s0wj-cgftkr exit=${code}====="
exit "$code"
