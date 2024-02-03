#!/bin/bash

# Get a list of all running Python processes
processes=$(pgrep python)

# Loop over all found processes and kill each one
for pid in $processes
do
  kill -9 $pid
done