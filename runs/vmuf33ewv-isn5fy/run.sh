#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf33ewv-isn5fy====="
(
  set -e
  python 'activemq_doc_generator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf33ewv-isn5fy exit=${code}====="
exit "$code"
