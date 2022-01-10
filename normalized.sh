#!/bin/bash

set -e

filename=$1
tempfile=$(mktemp)

trap 'rm -rf $tempfile' EXIT

# 1. reverse file - when you copy messages from tiktok they are reversed
# 2. remove data - remove data lines, that are between messages

tac $filename | awk '!/[0-9][0-9]:[0-9][0-9]/' > $tempfile
mv $tempfile $filename
