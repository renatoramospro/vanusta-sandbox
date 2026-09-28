#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukmussz-rizpv6====="
(
  set -e
  python 'secure_cqrs_experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukmussz-rizpv6 exit=${code}====="
exit "$code"
