#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx5rswy-vemurs====="
(
  set -e
  python 'thread_pool.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx5rswy-vemurs exit=${code}====="
exit "$code"
