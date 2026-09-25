#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh1vkz7-pz66gh====="
(
  set -e
  python 'alocador.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh1vkz7-pz66gh exit=${code}====="
exit "$code"
