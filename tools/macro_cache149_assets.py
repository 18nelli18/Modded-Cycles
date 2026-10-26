"""Cache exact Harmonics149 : cibles derivees des parametres, note181. Braids MIT."""
from pathlib import Path
import subprocess,os,struct,hashlib
def prepare(root,build):
 repo=root.parent/'retrosyn-integration/build/macro-vendor/eurorack';build.mkdir(exist_ok=True)
 original=(repo/'braids/digital_oscillator.cc').read_text();assert hashlib.sha256(original.encode()).hexdigest()=='2b46fd3d702c4570af7fadc6e187a931d0f40d69532c3bf0a46ef4d1454bad84';start=original.index('void DigitalOscillator::RenderHarmonics(');end=original.index('\nvoid DigitalOscillator::RenderStruckDrum(',start);body=original[start:end]
 cache='''struct TargetCache {const void*owner;uint32_t valid,inc;int32_t a,b;int32_t target[12];};
 static TargetCache target_cache[6];
 static TargetCache* cache_for(const void*owner) {
  for(unsigned i=0;i<6;i++)if(target_cache[i].owner==owner)return &target_cache[i];
  for(unsigned i=0;i<6;i++)if(!target_cache[i].owner){target_cache[i].owner=owner;return &target_cache[i];}
  target_cache[0].owner=owner;target_cache[0].valid=0;return &target_cache[0];
 }
 '''
 body=body.replace('int32_t target_amplitude[kNumAdditiveHarmonics];','TargetCache* cache=cache_for(this);\n  int32_t* target_amplitude=cache->target;')
 lo=body.index('  int32_t peak =');hi=body.index('  while (size) {');calc=body[lo:hi].replace('    amplitude[i] = state_.hrm.amplitude[i];','')
 body=body[:lo]+'''  if(!cache->valid || cache->inc!=phase_increment_ || cache->a!=parameter_[0] || cache->b!=parameter_[1]) {
 '''+calc+'''    cache->inc=phase_increment_;cache->a=parameter_[0];cache->b=parameter_[1];cache->valid=1;
   }
   for(size_t i=0;i<kNumAdditiveHarmonics;i++)amplitude[i]=state_.hrm.amplitude[i];
 '''+body[hi:]
 text=original[:original.index('#include')]+'''#include "braids/digital_oscillator.h"
 #include "stmlib/utils/dsp.h"
 #include "braids/resources.h"
 namespace braids { using namespace stmlib;
 '''+cache+body+'\n}\n'
 src=build/'harmonics.cc';src.write_text(text);cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 flags=['-mcpu=54418','-O2','-fno-exceptions','-fno-rtti','-fno-threadsafe-statics','-fno-use-cxa-atexit','-fno-pic','-fno-common','-ffunction-sections','-fdata-sections','-fomit-frame-pointer']
 objs=[]
 for name,path in [('harmonics',src),('resources',repo/'braids/resources.cc')]:
  obj=build/(name+'.o');subprocess.run([cross+'g++.exe',*flags,'-I'+str(repo),'-c',str(path),'-o',str(obj)],check=True);objs.append(obj)
 entry=next(line.split()[2] for line in subprocess.check_output([cross+'nm.exe',str(objs[0])],text=True).splitlines() if ' T ' in line and 'RenderHarmonics' in line);link=build/'harmonics.ld';link.write_text('SECTIONS { .text 0x468a8000 : { *(.text*) *(.rodata*) } . = ALIGN(4); cache_code_end = .; .bss 0x468ad000 (NOLOAD) : { *(.bss*) *(COMMON) } . = ALIGN(4); cache_end = .; /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }')
 elf=build/'harmonics.elf';binary=build/'harmonics.bin';subprocess.run([cross+'ld.exe','-T',str(link),'--gc-sections','-e',entry,'-o',str(elf),*map(str,objs)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};assert sy['cache_code_end']<0x468ad000 and sy['cache_end']<0x468ae000
 return binary.read_bytes(),dict(code=0x468a8000,bss=0x468ad000,end=sy['cache_end'],code_end=sy['cache_code_end'],entry=sy[entry],source_commit='08460a69a7e1f7a81c5a2abcc7189c9a6b7208d4',source_sha256='2b46fd3d702c4570af7fadc6e187a931d0f40d69532c3bf0a46ef4d1454bad84',status='experimental',hardware_tested=False)

def apply(root,build,prefix,rt,tail,meta,patch):
 from gen_governor_recovery_test import TAIL
 code,m=prepare(root,build)
 assert meta['audio_headroom']['hall']['end']<=m['code'] and m['code_end']<m['bss'] and m['end']<0x468ae000 and not meta.get('mixer_headroom')
 assert not any(tail[m['code']-TAIL:m['code_end']-TAIL]) and not any(tail[m['bss']-TAIL:m['end']-TAIL])
 patch(m['code'],bytes(len(code)),code,tail)
 old=bytes.fromhex('4fefff68206f009c');at=0x467449be
 patch(at,old,b'\x4e\xf9'+struct.pack('>I',m['entry'])+b'\x4e\x71',rt)
 return dict(m,old_entry=at,old_prologue=old.hex(),code_bytes=len(code),cache_bytes=m['end']-m['bss'],models=[24])
