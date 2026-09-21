#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmube4fdt-1l9srk====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmube4fdt-1l9srk exit=${code}====="
exit "$code"
