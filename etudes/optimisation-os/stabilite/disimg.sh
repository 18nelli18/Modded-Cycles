#!/bin/sh
m68k-linux-gnu-objdump -D -b binary -m m68k:cfv4e --adjust-vma=0x40000400 --start-address=$2 --stop-address=$3 $1 | tail -n +8
