#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxfq744-oa59dq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxfq744-oa59dq exit=${code}====="
exit "$code"
