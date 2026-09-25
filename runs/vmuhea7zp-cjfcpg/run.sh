#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhea7zp-cjfcpg====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhea7zp-cjfcpg exit=${code}====="
exit "$code"
