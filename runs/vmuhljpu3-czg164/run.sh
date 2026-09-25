#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhljpu3-czg164====="
(
  set -e
  python 'dns_iterative_server.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhljpu3-czg164 exit=${code}====="
exit "$code"
