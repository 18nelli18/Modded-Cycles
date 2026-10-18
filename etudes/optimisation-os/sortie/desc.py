import struct,sys
img=open('/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/os/sec3.bin','rb').read()
B=0x40000400
def u32(a): return struct.unpack_from('>I',img,a-B)[0]
def s32(a): return struct.unpack_from('>i',img,a-B)[0]
def cstr(a):
    if not (B<=a<B+len(img)): return '?%x'%a
    o=a-B; e=img.index(b'\0',o); return img[o:e].decode('latin1')
a=0x4010dce0
for i in range(200):
    e=a+0x38*i
    m,slot,mn,mx,df=[s32(e+4*k) for k in range(5)]
    ln,gr,sn=u32(e+0x2c),u32(e+0x30),u32(e+0x34)
    if not (B<=ln<B+len(img)): break
    print(i,hex(e),'mach',m,'slot',slot,'min',mn/256,'max',mx/256,'def',df/256,'cc',s32(e+0x18),repr(cstr(ln)),repr(cstr(gr)),repr(cstr(sn)))
