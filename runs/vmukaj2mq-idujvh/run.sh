#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukaj2mq-idujvh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukaj2mq-idujvh exit=${code}====="
exit "$code"
