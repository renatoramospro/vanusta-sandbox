#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujivqjw-xjfggi====="
(
  set -e
  python 'service_discovery.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujivqjw-xjfggi exit=${code}====="
exit "$code"
