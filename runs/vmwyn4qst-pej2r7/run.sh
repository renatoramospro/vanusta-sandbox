#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyn4qst-pej2r7====="
(
  set -e
  python 'nvme_io_optimizer.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyn4qst-pej2r7 exit=${code}====="
exit "$code"
