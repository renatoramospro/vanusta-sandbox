#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf3mree-j884ir====="
(
  set -e
  python 'activemq_doc_generator_v2.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf3mree-j884ir exit=${code}====="
exit "$code"
