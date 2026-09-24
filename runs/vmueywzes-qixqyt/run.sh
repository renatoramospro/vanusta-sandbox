#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmueywzes-qixqyt====="
(
  set -e
  python 'websocket_doc_generator_v2.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmueywzes-qixqyt exit=${code}====="
exit "$code"
