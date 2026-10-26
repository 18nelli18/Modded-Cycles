"""198 : BRAIDS quantizer MIT, table MIDI publiee hors audio."""
import subprocess,json,struct
CODE=0x468f2000;BSS=0x468fa000;END=0x46900000
def apply(root,build,prefix,rt,tail,meta,patch,startup_safe=False,compact_labels=False):
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
 src=root/'tools/machines/scale167';cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 aliases={'bq_scale':native['scale_state']-delta,'bq_key':native['key_state']-delta,'bq_off_return':native['nof_noscale']-delta,'bq_on_return':native['non_noscale']-delta,'lp_frame':meta['lfo_polarity']['symbols']['lp_frame'],'lp_old_frame':meta['lfo_polarity']['symbols']['lp_old_frame']}
 # Le service UI reste chaine au service de polarite et au frame natif.
 at=meta['lfo_polarity']['symbols']['lp_ui_frame'];off=at-TAIL;raw=bytes(tail[off:off+6]);n=6
 for source in (src/'braids/quantizer.cc',src/'bridge.cc',src/'hooks.S',src/'menu.S'):
  obj=build/('bq-'+source.name+'.o');objects.append(obj);subprocess.run([cross+('g++.exe' if source.suffix=='.cc' else 'gcc.exe'),'-mcpu=54418','-O2','-fwrapv','-fno-exceptions','-fno-rtti','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector',*(['-DBQ_STARTUP_SAFE=1'] if startup_safe else []),*(['-DBQ_COMPACT_LABELS=1'] if compact_labels else []),'-I'+str(src),'-c',str(source),'-o',str(obj)],check=True)
 ld=build/'scale166.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin');ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} bq_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); bq_end = .; }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(v:=line.split())==3};assert sy['bq_code_end']<BSS<sy['bq_end']<END
 assert TAIL+len(tail)<CODE;tail.extend(bytes(CODE-TAIL-len(tail)));tail.extend(binary.read_bytes().ljust(sy['bq_end']-CODE,b'\0'))
 for name,target in [('snap_note','bq_snap'),('advance_scale','bq_advance_scale'),('advance_key','bq_advance_key')]:
  addr=native[name];o=addr-RUNTIME;old=bytes(rt[o:o+6]);assert len(old)==6;patch(addr,old,bytes.fromhex('4ef9')+struct.pack('>I',sy[target]),rt)
 patch(at,raw[:n],bytes.fromhex('4ef9')+struct.pack('>I',sy['bq_frame'])+bytes.fromhex('4e71')*((n-6)//2),tail)
 # Rediriger les tables et etendre les gardes du Genie sans deplacer ses autres champs.
 def replace_refs(area,base,old,new):
  needle=struct.pack('>I',old);positions=[i for i in range(0,len(area)-3,2) if area[i:i+4]==needle]
  for i in positions:patch(base+i,needle,struct.pack('>I',new),area)
  return len(positions)
 # La valeur Scale utilise une LEA PC-relative, remplacee par un accessor.
 v=native['value_invoker']+delta;o=v-RUNTIME
 hits2=[i for i in range(o,o+80,2) if rt[i:i+2]==bytes.fromhex('41fa') and rt[i+4:i+8]==bytes.fromhex('20300800')]
 assert len(hits2)==1
 i=hits2[0];patch(RUNTIME+i,bytes(rt[i:i+8]),bytes.fromhex('4eb9')+struct.pack('>I',sy['bq_scale_string'])+bytes.fromhex('4e71'),rt)
 # Ajouter Lock juste avant l'epilogue final du constructeur de menu.
 o=native['install_scale_menu_item']+delta-RUNTIME
 ends=[i for i in range(o,o+900,2) if rt[i:i+6]==bytes.fromhex('4fef00804e75')]
 assert len(ends)==1
 i=ends[0]-6;assert rt[i:i+2]==bytes.fromhex('4cef')
 patch(RUNTIME+i,bytes(rt[i:i+12]),bytes.fromhex('4ef9')+struct.pack('>I',sy['bq_menu_tail'])+bytes.fromhex('4e71')*3,rt)
 sg={k:int(v,16) for t in profile['composedTweaks'] for k,v in t.get('symbols',{}).items() if k.startswith('sg_')}
 refs={}
 for oldname,newname in [('sg_scales','bq_names'),('sg_masks','bq_masks')]:
  refs[oldname]=replace_refs(prefix,BASE,sg[oldname],sy[newname])+replace_refs(rt,RUNTIME,sg[oldname],sy[newname])
  assert refs[oldname]>0
 for name,reg in [('sg_generate','d1'),('sg_enc','d0')]:
  start=sg[name]-BASE;end=start+(360 if name=='sg_generate' else 1500)
  needle=bytes.fromhex('0c8100000004' if reg=='d1' else '0c8000000004')
  hits3=[i for i in range(start,end,2) if prefix[i:i+6]==needle]
  assert len(hits3)==1,(name,hits3)
  i=hits3[0];patch(BASE+i,needle,needle[:5]+bytes([18]),prefix)
 return dict(compact_labels=compact_labels,startup_safe=startup_safe,code=CODE,bss=BSS,end=sy['bq_end'],symbols=sy,aliases=aliases,scales=['Chromatic', 'Major', 'Minor', 'Dorian', 'Maj Pent', 'Phrygian', 'Lydian', 'Mixolyd', 'Locrian', 'Maj Blues', 'Min Blues', 'Min Pent', 'Folk', 'Japanese', 'Gamelan', 'Gypsy', 'Arabian', 'Flamenco', 'Whole Tone'],tones=[[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], [0, 2, 4, 5, 7, 9, 11], [0, 2, 3, 5, 7, 8, 10], [0, 2, 3, 5, 7, 9, 10], [0, 2, 4, 7, 9], [0, 1, 3, 5, 7, 8, 10], [0, 2, 4, 6, 7, 9, 11], [0, 2, 4, 5, 7, 9, 10], [0, 1, 3, 5, 6, 8, 10], [0, 3, 4, 7, 9, 10], [0, 3, 5, 6, 7, 10], [0, 3, 5, 7, 10], [0, 1, 3, 4, 5, 7, 8, 10], [0, 1, 5, 7, 8], [0, 1, 3, 7, 8], [0, 2, 3, 6, 7, 8, 11], [0, 1, 4, 5, 7, 8, 11], [0, 1, 4, 5, 7, 8, 10], [0, 2, 4, 6, 8, 10]],lock_modes=['Off','Original','Braids'],menu_refs=refs,off='native bypass',mode='nearest in-scale MIDI note',upstream='https://github.com/pichenettes/eurorack/tree/master/braids',credit='Emilie Gillet / Mutable Instruments',license='MIT',microtonal=False,compute='UI table build; no quantizer loops in audio',note_off_matching=True,hardware_tested=False,status='experimental')
