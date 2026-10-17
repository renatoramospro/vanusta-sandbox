#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcrwnrj-i2e1nl====="
(
  set -e
  python 'motor_avro.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcrwnrj-i2e1nl exit=${code}====="
exit "$code"
