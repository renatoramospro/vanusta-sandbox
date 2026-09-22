#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucladei-7xqf7v====="
(
  set -e
  python 'modelo_risco_corrigido.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucladei-7xqf7v exit=${code}====="
exit "$code"
