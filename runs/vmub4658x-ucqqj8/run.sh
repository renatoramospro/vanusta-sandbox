#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub4658x-ucqqj8====="
(
  set -e
  python 'pcg_pipeline.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub4658x-ucqqj8 exit=${code}====="
exit "$code"
