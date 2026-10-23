#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvl5d744-gjd9mq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvl5d744-gjd9mq exit=${code}====="
exit "$code"
