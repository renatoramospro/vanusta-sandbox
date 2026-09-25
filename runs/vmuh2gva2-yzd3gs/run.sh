#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh2gva2-yzd3gs====="
(
  set -e
  python 'alocador.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh2gva2-yzd3gs exit=${code}====="
exit "$code"
