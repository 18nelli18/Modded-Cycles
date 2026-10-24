/* Prologues remplaces entiers, arguments/pile natifs rejoues exactement. */
.text
.globl dx7_din_original,dx7_usb_original
dx7_din_original:
 pea 0x40f1bf24
 jmp 0x4007f69a
dx7_usb_original:
 lea -40(%sp),%sp
 movem.l %d2-%d6/%a2-%fp,(%sp)
 jmp 0x4007f6b0
