#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyhk5go-lof03d====="
(
  set -e
  python 'gpu_manager.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyhk5go-lof03d exit=${code}====="
exit "$code"
