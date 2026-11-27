#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyfqmqe-qrbduh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyfqmqe-qrbduh exit=${code}====="
exit "$code"
