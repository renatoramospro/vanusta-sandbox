#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhbwxjk-oszgqs====="
(
  set -e
  python 'protocolo_confiavel.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhbwxjk-oszgqs exit=${code}====="
exit "$code"
