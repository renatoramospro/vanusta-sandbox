#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9pn9tf-o8bay0====="
(
  set -e
  python 'pipeline_tracker.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9pn9tf-o8bay0 exit=${code}====="
exit "$code"
