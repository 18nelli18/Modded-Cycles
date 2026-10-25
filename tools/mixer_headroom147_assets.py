"""147 : mixeur stationnaire et SPEAK -O3, note177. Pas de nouvel etat."""
import struct,subprocess,hashlib
CODE=0x468a8000;LIMIT=0x468a8400
def apply(root,build,prefix,rt,tail,meta,patch):
 from gen_governor_recovery_test import BASE,TAIL
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');rows=[]
 assert meta['audio_headroom']['hall']['end']<=CODE and LIMIT<0x468ae000
 for index,(entry,end,lo,hi,branch,n,prologue) in enumerate([(0x40056698,0x40056716,0x400566e0,0x400566fa,0x40056702,7,'4fefffd848d73cfc'),(0x40056716,0x4005678a,0x40056758,0x4005676e,0x40056776,6,'4fefffe048d70cfc')]):
  old=bytes(prefix[entry-BASE:end-BASE]);assert old[:8].hex()==prologue
  assert old[lo-entry:lo-entry+2]==bytes.fromhex('d095' if n==7 else 'd093')
  flat=bytearray(old[:lo-entry]+old[hi-entry:]);offset=branch-entry-(hi-lo);assert flat[offset]==0x6e and flat[offset+1]>=128;flat[offset+1]=(flat[offset+1]-256+hi-lo)&255
  at=CODE+index*0x200
  text='.text\n.globl wrapper\nwrapper:\n movea.l 16(%sp),%a0\n move.l (%a0),%d0\n'+''.join(f' or.l {4*i}(%a0),%d0\n' for i in range(1,n))+f' tst.l %d0\n beq flat\n'+'.byte '+','.join(str(x) for x in old[:8])+f'\n jmp {entry+8:#x}\n .org 128\nflat:\n'+'.byte '+','.join(str(x) for x in flat)+'\n'
  src=build/f'mixer147-{n}.S';obj=src.with_suffix('.o');elf=src.with_suffix('.elf');binary=src.with_suffix('.bin');src.write_text(text)
  subprocess.run([cross+'as.exe','-mcpu=54418',str(src),'-o',str(obj)],check=True);subprocess.run([cross+'ld.exe','-e','wrapper','-Ttext',hex(at),'-o',str(elf),str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
  code=binary.read_bytes();assert at+len(code)<=LIMIT
  tail.extend(bytes(max(0,at+len(code)-TAIL-len(tail))));patch(at,bytes(len(code)),code,tail);patch(entry,old[:8],b'\x4e\xf9'+struct.pack('>I',at)+b'\x4e\x71',prefix)
  rows.append(dict(entry=entry,code=at,size=len(code),sha256=hashlib.sha256(code).hexdigest(),original_sha256=hashlib.sha256(old).hexdigest(),gains=n))
 return dict(code=CODE,end=TAIL+len(tail),kernels=rows,speech_compiler='-O3',new_state_bytes=0,status='experimental',hardware_tested=False)
