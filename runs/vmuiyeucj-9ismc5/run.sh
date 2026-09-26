#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiyeucj-9ismc5====="
(
  set -e
  python 'myers_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiyeucj-9ismc5 exit=${code}====="
exit "$code"
