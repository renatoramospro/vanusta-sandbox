#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcs85tw-wq2ugb====="
(
  set -e
  python 'motor_avro.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcs85tw-wq2ugb exit=${code}====="
exit "$code"
