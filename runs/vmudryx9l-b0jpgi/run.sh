#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudryx9l-b0jpgi====="
(
  set -e
  python 'pipeline_asyncapi.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudryx9l-b0jpgi exit=${code}====="
exit "$code"
