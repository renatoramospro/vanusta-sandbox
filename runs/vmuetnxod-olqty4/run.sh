#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuetnxod-olqty4====="
(
  set -e
  python 'kafka_doc_generator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuetnxod-olqty4 exit=${code}====="
exit "$code"
