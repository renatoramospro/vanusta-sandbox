#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9pui04-01ad07====="
(
  set -e
  python 'pipeline_tracker_v2.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9pui04-01ad07 exit=${code}====="
exit "$code"
