"""TINY ajoute en index18 ; metadonnees seules, tous moteurs existants conserves.
La zone467ea000..467ef000 est un padding nul avant le BSS Elder467f0000.
Aucun agrandissement de reservation RAM ni compilation du DSP TINY.
"""
import json,struct,subprocess,hashlib
DATA=0x467ea000;DESC=0x467ea200;CODE=0x467ec000;END=0x467ef000
OLD_DATA=0x46789000;OLD_DESC=0x46789400

def apply(root,build,prefix,rt,tail,oldrt,meta,patch,reorder=False,shadow=None,speak=None,legacy=None,retro=None,punch=None):
 DATA,DESC=(0x467e9800,0x467e9a00) if shadow else (0x467ea000,0x467ea200)
 nm=24 if punch else 23 if retro else 22 if legacy else 21 if speak else 20 if shadow else 19;ndesc=161 if punch else 156 if retro else 151 if legacy else 146 if speak else 141 if shadow else 136;stride=nm*4;mapping=nm*16
 from gen_governor_recovery_test import BASE,RUNTIME,TAIL
 import gen_syntakt_engines as gs,gen_sdvintage_7th as g7
 import build_machine_identity_test as identity
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 prof=json.loads((root/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text())
 tg={k:int(v,16) for t in prof['composedTweaks'] if t['id']=='sample-wizard' for k,v in t['symbols'].items()}
 images=[gs.CATALOG[c]['image'] for c in ['sd','cp','toy','bits','swarm']]+[4]*6
 gs.LAYOUT.update(STUBS=0x88000,DATA=0x89000,DESCN=0x89400,ROWSN=0x84000,CCROWSN=0x84400,RECS=0x84800);gs.set_base(RUNTIME);gs.MARKS_ROW=9;gs.MARKS['x']=68
 def compile(text,name,at):
  src=build/(name+'.S');obj=build/(name+'.o');elf=build/(name+'.elf');binary=build/(name+'.bin');src.write_text(text)
  subprocess.run([cross+'gcc.exe','-mcpu=54418','-c',str(src),'-o',str(obj)],check=True)
  subprocess.run([cross+'ld.exe','-e','state_at','-Ttext',hex(at),'-o',str(elf),str(obj)],check=True)
  subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
  sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3}
  return binary.read_bytes(),sy
 oldcode,oldsy=compile(gs.detours_asm(11,images,[76+5*i for i in range(11)],tg),'tiny_old_metadata',0x46788000)
 gs.LAYOUT.update(STUBS=CODE-RUNTIME,DATA=DATA-RUNTIME,DESCN=DESC-RUNTIME);gs.set_base(RUNTIME);gs.MARKS_ROW=12 if retro else 11 if speak else 10
 text=gs.detours_asm(nm-7,images+([4,4,4,4,4,4] if punch else [4,4,4,4,4] if retro else [4,4,4,4] if legacy else [4,4,4] if speak else [4,4] if shadow else [4]),[76+5*i for i in range(nm-7)],tg)
 # Dix colonnes sur deux lignes, pas de19e repere hors ecran.
 text=text.replace('lsl.l #3, %d0\n\tsub.l %d4, %d0\n\tadd.l #68, %d0','mulu.w #'+str(5 if speak else 6)+', %d0\n\tadd.l #68, %d0')
 left,right=meta['identity_symbols']['identity_left'],meta['identity_symbols']['identity_right']
 text+='\n.globl tiny_left,tiny_right\ntiny_left:\n cmpi.l #18,%d3\n beq 1f\n movea.l 0x40fe32cc,%a1\n jmp '+hex(left+6)+'\n1: lea tiny_stats,%a1\n suba.l %d4,%a1\n jmp 0x4678812a\ntiny_right:\n cmpi.l #18,%d3\n beq 1f\n cmpi.l #6,%d3\n jmp '+hex(right+6)+'\n1: move.l #tiny_icon,%d4\n jmp 0x46788144\n'
 if reorder:
  text=text.replace('cmp.l %d5, %d3','''move.l %d5,%d0
 cmpi.l #17,%d0
 bcs.s 8f
 eori.l #3,%d0
8: cmp.l %d0,%d3''')
  text+='''
.globl tiny_menu_increment
tiny_menu_increment:
 cmpi.l #17,%d0
 bcs.s 1f
 eori.l #3,%d0
1: add.l %d5,%d0
 bpl.s 2f
 moveq #0,%d0
2: cmpi.l #18,%d0
 ble.s 3f
 moveq #18,%d0
3: cmpi.l #17,%d0
 bcs.s 4f
 eori.l #3,%d0
4: moveq #-1,%d1
 jmp 0x400148bc
'''
 if shadow:
  text=text.replace('tiny_left:\n','tiny_left:\n cmpi.l #19,%d3\n bne.s 9f\n lea.l 0x467ed600,%a1\n suba.l %d4,%a1\n jmp 0x4678812a\n9:\n')
  text=text.replace('tiny_right:\n','tiny_right:\n cmpi.l #19,%d3\n bne.s 9f\n move.l #0x467ed61c,%d4\n jmp 0x46788144\n9:\n')
  # Positions17/18/19 -> TINY/Shadow/MIDI ; IDs existants inchanges.
  at=text.index('move.l %d5,%d0');end=text.index('8: cmp.l %d0,%d3',at)+len('8: cmp.l %d0,%d3')
  text=text[:at]+"move.l %d5,%d0\n cmpi.l #17,%d0\n bcs.s 8f\n addq.l #1,%d0\n cmpi.l #20,%d0\n bne.s 8f\n moveq #17,%d0\n8: cmp.l %d0,%d3"+text[end:]
  at=text.index('tiny_menu_increment:');end=text.index('\n #',at) if '\n #' in text[at:] else len(text)
  text=text[:at]+"""tiny_menu_increment:
 cmpi.l #17,%d0
 bcs.s 1f
 subq.l #1,%d0
 cmpi.l #16,%d0
 bne.s 1f
 moveq #19,%d0
1: add.l %d5,%d0
 bpl.s 2f
 moveq #0,%d0
2: cmpi.l #19,%d0
 ble.s 3f
 moveq #19,%d0
3: cmpi.l #17,%d0
 bcs.s 4f
 addq.l #1,%d0
 cmpi.l #20,%d0
 bne.s 4f
 moveq #17,%d0
4: moveq #-1,%d1
 jmp 0x400148bc
"""+text[end:]
 if speak:
  text=text.replace('cmpi.l #20,%d0','cmpi.l #21,%d0').replace('moveq #19,%d0','moveq #20,%d0').replace('cmpi.l #19,%d0\n ble.s 3f','cmpi.l #20,%d0\n ble.s 3f')
  text=text.replace('tiny_left:\n','tiny_left:\n cmpi.l #20,%d3\n bne.s 7f\n lea.l 0x46823000,%a1\n suba.l %d4,%a1\n jmp 0x4678812a\n7:\n')
  text=text.replace('tiny_right:\n','tiny_right:\n cmpi.l #20,%d3\n bne.s 7f\n move.l #0x4682301c,%d4\n jmp 0x46788144\n7:\n')
 if legacy:
  text=text.replace('cmpi.l #21,%d0','cmpi.l #22,%d0').replace('moveq #20,%d0','moveq #21,%d0').replace('cmpi.l #20,%d0\n ble.s 3f','cmpi.l #21,%d0\n ble.s 3f')
  text=text.replace('tiny_left:\n','tiny_left:\n cmpi.l #21,%d3\n bne.s 6f\n lea.l 0x46888000,%a1\n suba.l %d4,%a1\n jmp 0x4678812a\n6:\n')
  text=text.replace('tiny_right:\n','tiny_right:\n cmpi.l #21,%d3\n bne.s 6f\n move.l #0x4688801c,%d4\n jmp 0x46788144\n6:\n')
 if retro:
  text=text.replace('cmpi.l #22,%d0','cmpi.l #23,%d0').replace('moveq #21,%d0','moveq #22,%d0').replace('cmpi.l #21,%d0\n ble.s 3f','cmpi.l #22,%d0\n ble.s 3f')
  text=text.replace('tiny_left:\n','tiny_left:\n cmpi.l #22,%d3\n bne.s 5f\n lea.l 0x468bb000,%a1\n suba.l %d4,%a1\n jmp 0x4678812a\n5:\n')
  text=text.replace('tiny_right:\n','tiny_right:\n cmpi.l #22,%d3\n bne.s 5f\n move.l #0x468bb01c,%d4\n jmp 0x46788144\n5:\n')
 if punch:
  text=text.replace('cmpi.l #23,%d0','cmpi.l #24,%d0').replace('moveq #22,%d0','moveq #23,%d0').replace('cmpi.l #22,%d0\n ble.s 3f','cmpi.l #23,%d0\n ble.s 3f')
  text=text.replace('tiny_left:\n','tiny_left:\n cmpi.l #23,%d3\n bne.s 4f\n lea.l 0x468ae000,%a1\n suba.l %d4,%a1\n jmp 0x4678812a\n4:\n')
  text=text.replace('tiny_right:\n','tiny_right:\n cmpi.l #23,%d3\n bne.s 4f\n move.l #0x468ae01c,%d4\n jmp 0x46788144\n4:\n')
  # Les trois objets propres a PUNCH ; tous les autres descripteurs delegues.
  text=text.replace('state_at:\n','pn_generic_state:\n').replace('state_connect:\n','pn_generic_connect:\n')
  for entry,fallback in [('state_at','pn_generic_state'),('state_connect','pn_generic_connect')]:
   text+='\n'+entry+':\n move.l 4(%sp),%d0\n cmpi.l #156,%d0\n bcs.w '+fallback+'\n cmpi.l #159,%d0\n bcc.w '+fallback+'\n subi.l #156,%d0\n move.l %d0,-(%sp)\n jsr '+hex(punch['symbols']['punch_state_init'])+'\n addq.l #4,%sp\n'
   if entry=='state_at':text+=' rts\n'
   else:text+=' addi.l #20,%d0\n pea 0x40a71500\n move.l 12(%sp),-(%sp)\n move.l %d0,-(%sp)\n jsr 0x400ddf60\n lea 12(%sp),%sp\n move.l #0x40a71500,%d0\n rts\n'
 # Descripteurs bitmap/pixels reserves loin du code metadata.
 text+='\n.equ tiny_stats,0x467ed000\n.equ tiny_icon,0x467ed01c\n'
 code,sy=compile(text,'tiny_metadata',CODE);assert CODE+len(code)<=0x467ed000
 blob=bytearray(END-DATA)
 def put(at,b):assert DATA<=at and at+len(b)<=END;blob[at-DATA:at-DATA+len(b)]=b
 table=[]
 for k in range(4):
  old=list(struct.unpack_from('>18I',rt,OLD_DATA-RUNTIME+72*k))
  old.append(DATA+(0x1c0 if retro else 0x180 if speak else 0x160 if shadow else 0x144) if k==0 else 0x4677c000 if k==1 else 0x4677c2f2 if k==2 else 19)
  if shadow:old.append(shadow['symbols']['shadow_name'] if k==0 else shadow['symbols']['shadow_update'] if k==1 else shadow['symbols']['shadow_render'] if k==2 else 20)
  if speak:old.append(speak['symbols']['speak_name'] if k==0 else speak['symbols']['speak_update'] if k==1 else speak['symbols']['speak_render'] if k==2 else 21)
  if legacy:old.append(legacy['symbols']['dx7_name'] if k==0 else legacy['symbols']['dx7_update'] if k==1 else legacy['symbols']['dx7_render'] if k==2 else 22)
  if retro:old.append(retro['symbols']['retrosyn_name'] if k==0 else retro['symbols']['retrosyn_update'] if k==1 else retro['symbols']['retrosyn_render'] if k==2 else 23)
  if punch:old.append(punch['symbols']['punch_name'] if k==0 else punch['symbols']['punch_update'] if k==1 else punch['symbols']['punch_render'] if k==2 else 24)
  table+=old
 put(DATA,struct.pack('>'+str(nm*4)+'I',*table));put(DATA+mapping,bytes(rt[OLD_DATA-RUNTIME+288:OLD_DATA-RUNTIME+306])+bytes([18,19,20,21,22,23] if punch else [18,19,20,21,22,0] if retro else [18,19,20,21,0,0] if legacy else [18,19,20,0] if speak else [18,19,0,0] if shadow else [18,0]));put(DATA+(0x1c0 if retro else 0x180 if speak else 0x160 if shadow else 0x144),b'TINY\0')
 desc=bytearray(rt[OLD_DESC-RUNTIME:OLD_DESC-RUNTIME+131*56]);assert len(desc)==131*56
 tiny=oldrt[0x4678ad60-RUNTIME:0x4678ad60-RUNTIME+280];assert len(tiny)==280
 desc.extend(tiny)
 if shadow:
  sd=bytearray(tiny)
  for k in range(5):
   for off,value in [(8,0),(12,127*256),(16,[32,100,64,48,90][k]*256),(44,shadow['symbols']['shadow_labels']+8*k),(52,shadow['symbols']['shadow_short_labels']+8*k)]:struct.pack_into('>I',sd,k*56+off,value)
  desc.extend(sd)
 if speak:
  sd=bytearray(tiny)
  for k in range(5):
   for off,value in [(8,0),(12,127*256),(16,[64,31,64,80,127][k]*256),(44,speak['symbols']['speak_labels']+8*k),(52,speak['symbols']['speak_short_labels']+8*k)]:struct.pack_into('>I',sd,k*56+off,value)
  desc.extend(sd)
 if legacy:
  sd=bytearray(tiny)
  for k in range(5):
   for off,value in [(8,0),(12,(31 if k==1 else 127)*256),(16,[100,0,64,64,127][k]*256),(44,legacy['symbols']['dx7_labels']+8*k),(52,legacy['symbols']['dx7_short_labels']+8*k)]:struct.pack_into('>I',sd,k*56+off,value)
  desc.extend(sd)
 if retro:
  sd=bytearray(tiny)
  for k in range(5):
   for off,value in [(8,0),(12,(5 if k==1 else 127)*256),(16,[0,0,64,0,50][k]*256),(44,retro['symbols']['retrosyn_labels']+8*k),(52,retro['symbols']['retrosyn_short_labels']+8*k)]:struct.pack_into('>I',sd,k*56+off,value)
  desc.extend(sd)
 if punch:
  sd=bytearray(tiny)
  for k in range(5):
   for off,value in [(8,0),(12,(11 if k==1 else 127)*256),(16,[64,0,68,40,50][k]*256),(44,punch['symbols']['punch_labels']+8*k),(52,punch['symbols']['punch_short_labels']+8*k)]:struct.pack_into('>I',sd,k*56+off,value)
  desc.extend(sd)
 assert int.from_bytes(desc[41*56+12:41*56+16],'big')==17*256;struct.pack_into('>I',desc,41*56+12,(nm-1)*256);put(DESC,desc);put(CODE,code)
 # Carte propre a TINY sans changer les douze cartes ajoutees existantes.
 profile=dict(machine=18,name='TINY',icon='T',**{'class':'SYNTH'},style='TINY',str=2,dex=5,mag=3)
 at=0x467ed038
 for descriptor,render,w,h in [(0x467ed000,identity.stats,48,33),(0x467ed01c,identity.icon,34,34)]:
  pixels=(root/'tools/machines/shadow/artwork/tiny-magnifying-glass_34x34.bin').read_bytes() if shadow and descriptor==0x467ed01c else render(profile);mask=identity.encode([[1]*w for _ in range(h)]);ptr=at;put(ptr,pixels);at+=len(pixels);mp=at;put(mp,mask);at+=len(mask);put(descriptor,struct.pack('>7I',0x401117c8,w,h,2,ptr,mp,0))
 if shadow:
  sp=dict(machine=19,name='Shadow',icon='S',**{'class':'SYNTH'},style='PULSAR',str=3,dex=4,mag=4);at=0x467ed638
  for descriptor,render,w,h in [(0x467ed600,identity.stats,48,33),(0x467ed61c,identity.icon,34,34)]:
   pixels=(root/'tools/machines/shadow/artwork/shadow-looming_34x34.bin').read_bytes() if descriptor==0x467ed61c else render(sp);mask=identity.encode([[1]*w for _ in range(h)]);ptr=at;put(ptr,pixels);at+=len(pixels);mp=at;put(mp,mask);at+=len(mask);put(descriptor,struct.pack('>7I',0x401117c8,w,h,2,ptr,mp,0))
  meta['machine_identities'].append(sp)
 if speak:meta['machine_identities'].append(speak['profile'])
 if legacy:meta['machine_identities'].append(legacy['profile'])
 if retro:meta['machine_identities'].append(retro['profile'])
 if punch:meta['machine_identities'].append(punch['profile'])
 assert at<END and not any(tail[DATA-TAIL:END-TAIL]);patch(DATA,bytes(len(blob)),bytes(blob),tail)
 # Reloger uniquement les references connues des tables, pas les chaines/voix.
 moves={OLD_DATA:DATA,OLD_DATA+72:DATA+stride,OLD_DATA+144:DATA+2*stride,OLD_DATA+216:DATA+3*stride,OLD_DATA+288:DATA+mapping,OLD_DESC:DESC,OLD_DESC+8:DESC+8,OLD_DESC+32:DESC+32}
 refs={hex(k):0 for k in moves}
 for area,base in [(prefix,BASE),(rt,RUNTIME),(tail,TAIL)]:
  for off in range(0,len(area)-3,2):
   v=int.from_bytes(area[off:off+4],'big')
   if v in moves:patch(base+off,struct.pack('>I',v),struct.pack('>I',moves[v]),area);refs[hex(v)]+=1
 assert all(refs.values()),refs
 # Entrees metadonnees regenerees : les autres chemins natifs ne bougent pas.
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040);hooks=[]
 for name in ['map_state','state_at','state_connect','cc_bounds','shown','record_at','record_of','marks','knob_vec','desc_machine','builder_row','lfo_gate','amp_row','amp_gate']:
  va=oldsy[name];off=va-0x46788000;n=0
  for ins in cs.disasm(oldcode[off:off+20],va):
   n+=ins.size
   if n>=6:break
  old=oldcode[off:off+n];actual=bytes(rt[va-RUNTIME:va-RUNTIME+n]);assert actual==old,(name,actual.hex(),old.hex())
  patch(va,old,b'\x4e\xf9'+struct.pack('>I',sy[name])+b'\x4e\x71'*((n-6)//2));hooks.append([name,hex(va),n])
 patch(left,bytes.fromhex('227940fe32cc'),b'\x4e\xf9'+struct.pack('>I',sy['tiny_left']),tail)
 patch(right,bytes.fromhex('0c8300000006'),b'\x4e\xf9'+struct.pack('>I',sy['tiny_right']),tail)
 # Limites de selection/dispatch et taille du tableau de19rangees.
 for va,reg in [(0x400a7dba,0x72),(0x400a7df4,0x70),(0x400147a4,0x70),(0x400148aa,0x72),(0x400148b2,0x70),(0x400a25e0,0x70)]:patch(va,bytes([reg,17]),bytes([reg,nm-1]),prefix)
 patch(0x4005a2b8,bytes.fromhex('48780240'),bytes.fromhex('48780300' if punch else '487802e0' if retro else '487802c0' if legacy else '487802a0' if speak else '48780280' if shadow else '48780260'),prefix)
 # Les bornes131/130 resident dans les trampolines32bits prouves MIDI.
 bounds=[]
 for site in g7.BOUNDS:
  off=site-BASE;raw=bytes(prefix[off:off+6])
  if raw[:2]!=b'\x4e\xf9':continue
  target=int.from_bytes(raw[2:],'big')
  if not 0x4678d000<=target<0x4678e000:continue
  i=target-RUNTIME;old=bytes(rt[i:i+6]);value=int.from_bytes(old[2:],'big');assert value in (130,131) and int.from_bytes(old[:2],'big')&0xf1ff==0x203c,(hex(site),old.hex())
  patch(target,old,old[:2]+struct.pack('>I',value+(30 if punch else 25 if retro else 20 if legacy else 15 if speak else 10 if shadow else 5)));bounds.append(hex(site))
 ld=next(int(t['symbols']['ld_api'],16) for t in prof['composedTweaks'] if 'ld_api' in t.get('symbols',{}));patch(ld+12,struct.pack('>I',131),struct.pack('>I',ndesc),tail)
 assert set(bounds)=={hex(site) for site in g7.BOUNDS if site not in {0x4000b208,0x4000b22a,0x4005a50a}},bounds
 if reorder:
  old=bytes.fromhex('7217d085b2806c02701722004681d2819381' if punch else '7216d085b2806c02701622004681d2819381' if retro else '7215d085b2806c02701522004681d2819381' if legacy else '7214d085b2806c02701422004681d2819381' if speak else '7213d085b2806c02701322004681d2819381' if shadow else '7212d085b2806c02701222004681d2819381');assert len(old)==18
  patch(0x400148aa,old,b'\x4e\xf9'+struct.pack('>I',sy['tiny_menu_increment'])+b'\x4e\x71'*6,prefix)
 meta['machine_identities'].append(profile)
 if shadow:
  meta['machine_identities'].sort(key=lambda p:p['machine'])
  descriptor=meta['identity_icons']+8*28;ptr=int.from_bytes(tail[descriptor-TAIL+16:descriptor-TAIL+20],'big');pixels=(root/'tools/machines/shadow/artwork/wave-wavetable_34x34.bin').read_bytes();assert len(pixels)==272;old=bytes(tail[ptr-TAIL:ptr-TAIL+len(pixels)]);patch(ptr,old,pixels,tail)
  shadow['icons']={'Shadow':'shadow-looming','WAVE':'wave-wavetable','TINY':'tiny-magnifying-glass'}
 return dict(menu_order=list(range(17))+([18,19,20,21,22,23,17] if punch else [18,19,20,21,22,17] if retro else [18,19,20,21,17] if legacy else [18,19,20,17] if speak else [18,19,17] if shadow else [18,17]) if reorder else list(range(nm)),menu_reordered=reorder,machine=18,name='TINY',machine_count=nm,models=52,update=0x4677c000,render=0x4677c2f2,code=CODE,code_bytes=len(code),data=DATA,descriptors=DESC,descriptor_count=ndesc,end=END,symbols=sy,metadata_hooks=hooks,references=refs,wide_bounds=bounds,profile=profile,status='experimental',hardware_tested=False,preserves_existing_ids=True,source='resident original TINY; v17 parameter descriptors')
