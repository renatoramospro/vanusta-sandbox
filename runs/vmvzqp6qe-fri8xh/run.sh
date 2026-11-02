#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvzqp6qe-fri8xh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvzqp6qe-fri8xh exit=${code}====="
exit "$code"
