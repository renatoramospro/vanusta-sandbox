#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuetzj1w-zg9fx5====="
(
  set -e
  python 'kafka_doc_generator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuetzj1w-zg9fx5 exit=${code}====="
exit "$code"
