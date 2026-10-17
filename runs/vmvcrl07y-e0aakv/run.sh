#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcrl07y-e0aakv====="
(
  set -e
  python 'motor_avro.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcrl07y-e0aakv exit=${code}====="
exit "$code"
