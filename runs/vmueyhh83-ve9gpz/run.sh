#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmueyhh83-ve9gpz====="
(
  set -e
  python 'websocket_doc_generator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmueyhh83-ve9gpz exit=${code}====="
exit "$code"
