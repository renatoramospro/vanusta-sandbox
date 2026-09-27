#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk3ghk6-gzj6xd====="
(
  set -e
  python 'mvcc_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk3ghk6-gzj6xd exit=${code}====="
exit "$code"
