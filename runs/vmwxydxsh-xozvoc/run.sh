#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxydxsh-xozvoc====="
(
  set -e
  python 'fsm_protocol.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxydxsh-xozvoc exit=${code}====="
exit "$code"
