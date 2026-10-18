#!/bin/sh
# usage: dis.sh start stop
m68k-linux-gnu-objdump -D -b binary -m m68k:cfv4e --adjust-vma=0x40000400 --start-address=$1 --stop-address=$2 /tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/os/sec3.bin | tail -n +8 | cut -c1-110
