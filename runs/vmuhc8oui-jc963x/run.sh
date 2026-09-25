#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhc8oui-jc963x====="
(
  set -e
  python 'protocolo_confiavel.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhc8oui-jc963x exit=${code}====="
exit "$code"
