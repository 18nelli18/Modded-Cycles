"""198 : BRAIDS quantizer MIT, table MIDI publiee hors audio."""
import subprocess,json,struct
CODE=0x468f2000;BSS=0x468fa000;END=0x46900000
def apply(root,build,prefix,rt,tail,meta,patch):
 from gen_governor_recovery_test import BASE,TAIL,RUNTIME
 profile=json.loads((root/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());native={k:int(v,16) for t in profile['composedTweaks'] for k,v in t.get('symbols',{}).items()}
 # Le support Model-TG a ete reloge dans le runtime final ; resoudre le
 # vrai snap puis verifier independamment son acces PC-relatif Scale.
 hits=[i for i in range(0,len(rt)-12,2) if rt[i:i+4]==bytes.fromhex('2f0d4a3a')]
 assert len(hits)==1,hits
 snap=RUNTIME+hits[0];delta=snap-native['snap_note']
 for name in ('snap_note','scale_state','key_state','advance_scale','advance_key','nof_noscale','non_noscale'):native[name]+=delta
 assert snap+4+int.from_bytes(rt[hits[0]+4:hits[0]+6],'big',signed=True)==native['scale_state']
 for name in ('nof_noscale','non_noscale'):
  i=native[name]-RUNTIME;assert rt[i-4:i-2] in (bytes.fromhex('4eba'),bytes.fromhex('6100'))
  assert native[name]-2+int.from_bytes(rt[i-2:i],'big',signed=True)==snap
 src=root/'tools/machines/scale166';cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 aliases={'bq_scale':native['scale_state'],'bq_key':native['key_state'],'bq_off_return':native['nof_noscale'],'bq_on_return':native['non_noscale'],'lp_frame':meta['lfo_polarity']['symbols']['lp_frame'],'lp_old_frame':meta['lfo_polarity']['symbols']['lp_old_frame']}
 # Le service UI reste chaine au service de polarite et au frame natif.
 at=meta['lfo_polarity']['symbols']['lp_ui_frame'];off=at-TAIL;raw=bytes(tail[off:off+6]);n=6
 for source in (src/'braids/quantizer.cc',src/'bridge.cc',src/'hooks.S'):
  obj=build/('bq-'+source.name+'.o');objects.append(obj);subprocess.run([cross+('g++.exe' if source.suffix=='.cc' else 'gcc.exe'),'-mcpu=54418','-O2','-fwrapv','-fno-exceptions','-fno-rtti','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-I'+str(src),'-c',str(source),'-o',str(obj)],check=True)
 ld=build/'scale166.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin');ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} bq_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); bq_end = .; }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(v:=line.split())==3};assert sy['bq_code_end']<BSS<sy['bq_end']<END
 assert TAIL+len(tail)<CODE;tail.extend(bytes(CODE-TAIL-len(tail)));tail.extend(binary.read_bytes().ljust(sy['bq_end']-CODE,b'\0'))
 for name,target in [('snap_note','bq_snap'),('advance_scale','bq_advance_scale'),('advance_key','bq_advance_key')]:
  addr=native[name];o=addr-RUNTIME;old=bytes(rt[o:o+6]);assert len(old)==6;patch(addr,old,bytes.fromhex('4ef9')+struct.pack('>I',sy[target]),rt)
 patch(at,raw[:n],bytes.fromhex('4ef9')+struct.pack('>I',sy['bq_frame'])+bytes.fromhex('4e71')*((n-6)//2),tail)
 return dict(code=CODE,bss=BSS,end=sy['bq_end'],symbols=sy,aliases=aliases,scales=['Off','Major','Minor','Dorian','Major Pentatonic'],off='native bypass',mode='nearest in-scale MIDI note',upstream='https://github.com/pichenettes/eurorack/tree/master/braids',credit='Emilie Gillet / Mutable Instruments',license='MIT',microtonal=False,compute='UI table build; no quantizer loops in audio',note_off_matching=True,hardware_tested=False,status='experimental')
