/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_native_startup_join.S; lines 1-26.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Fixture startup interposition. The original JSR pushes 40005780.
 * Preserve its live GPRs, SR and residual caller arguments before the
 * original source63 installer. No installer/MMIO instruction runs in proof.
 */
.text
.globl startup,startup_factory,startup_getter,startup_setup,startup_installer
startup:
 lea %sp@(-64),%sp
 moveml %d0-%d7/%a0-%a6,%sp@
 movew %sr,%d0
 movew %d0,%sp@(60)
startup_factory:
 jsr 0x400cf866
 movel %d0,%sp@-
startup_getter:
 jsr 0x4000eb9c
 movel %d0,%sp@
startup_setup:
 jsr SETUP
 addql #4,%sp
 movew %sp@(60),%d0
 movew %d0,%sr
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(64),%sp
startup_installer:
 jmp 0x40059632
