#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmw22lztc-j534xf====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmw22lztc-j534xf exit=${code}====="
exit "$code"
