"""Groove/Humanize et CHORD Strum PPPCCC MIT ; UI Mod Setup propre.
Code468b2000..468ba000 et BSS468ba000..468bb000, avant art RETROSYN.
Les tables et noyaux seuls sont portes ; aucun patch FX/gestes tiers applique.
"""
import struct,subprocess,json,sys,hashlib,re
CODE=0x468b2000;UI=0x468b3000;BSS=0x468ba000;END=0x468bb000

def apply(root,build,prefix,rt,tail,meta,patch,hierarchy=False,groove_switch=False,human_apply=False,filter_modes=False,lfo_polarity=False,lfo_options=False,lfo_compact_ram=False,filter_key_guard=False,ui_idle=False):
 from gen_governor_recovery_test import BASE,RUNTIME,TAIL
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 src=root/'tools/machines/groove_strum';sys.path.insert(0,str(src));import cores156 as core
 def read(at,n):
  arr,base=(prefix,BASE) if at<RUNTIME else (rt,RUNTIME) if at<TAIL else (tail,TAIL);return bytes(arr[at-base:at-base+n])
 def put(at,old,new):
  assert read(at,len(old))==old,(hex(at),read(at,len(old)).hex(),old.hex());patch(at,old,new,prefix if at<RUNTIME else rt if at<TAIL else tail)
 aliases={**meta['symbols'],**meta['mute_quant']['aliases'],**meta['mute_quant']['symbols']}
 if ui_idle:aliases['gc_input_quiet']=meta['fx_menu']['symbols']['fx_input_quiet']
 hooks=[];tramp='.text\n';cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
 mq=meta['mute_quant']['symbols']
 for name,at,target in [('key',mq['mq_key'],'gc_key'),('encoder',mq['mq_encoder'],'gc_encoder'),('draw',mq['mq_draw'],'gc_draw'),('frame',mq['mq_frame'],'gc_frame')]:
  raw=read(at,32);alias='gc_previous_'+name;n=0
  if raw[:2]==b'\x4e\xf9':n=6;aliases[alias]=int.from_bytes(raw[2:6],'big')
  else:
   for ins in cs.disasm(raw,at):
    assert not ins.mnemonic.startswith(('b','j')),(name,ins.mnemonic);n+=ins.size
    if n>=6:break
   assert n>=6 and n%2==0;tramp+='\n.globl '+alias+'\n'+alias+':\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n'
  hooks.append((at,raw[:n],target))
 rootmenu=(build/'mq_root.S').read_text().replace('mq_root_draw','gc_root_draw').replace('moveq #9,%d0','moveq #10,%d0').replace('    jsr wf_menu_row','    clrb %a0@(836)\n    jsr wf_menu_row')
 rootmenu=rootmenu.replace('.Lquant:', '.Lgroove: .asciz "Grv"\n.Lquant:')+'\n.long 0,0,0,.Lgroove,0,1,.Lts_label,0,0,0,0,0,0,1,gc_root_value,0,0,0,0,0,0\n'
 sub=(build/'mq_sub.S').read_text();sub=sub[:sub.index('.Lon:')]
 sub=sub.replace('mq_sub_draw','gc_sub_draw').replace('mq_menu_row','gc_menu_row').replace('mq_menu_edit','gc_menu_edit').replace('movel mq_row','movel gc_row').replace('moveq #2,%d0','moveq #5,%d0').replace('.Lts_title_header: .long 4,4,0','.Lts_title_header: .long 6,6,0').replace('.asciz "Mute"','.asciz "Groove"').replace('.asciz "Quant"','.asciz "Setup"').replace('    jsr gc_menu_row','    clrb %a0@(248)\n    clrb %a0@(332)\n    clrb %a0@(416)\n    jsr gc_menu_row')
 sub+='\n.Lmode: .asciz "Grv"\n.Ltrack: .asciz "Trk"\n.Ltime: .asciz "Tim"\n.Lvel: .asciz "Vel"\n.Lstrum: .asciz "Str"\n.Lallocator: .byte 0\n.balign 4\n.Lts_rows:\n'
 for k,label in enumerate(('mode','track','time','vel','strum')):sub+=f'.long 0,0,0,.L{label},0,1,.Lts_label,0,0,0,0,0,0,1,gc_value{k},0,0,0,0,0,0\n'
 hp='''.text
.globl gc_hload,gc_hinit
gc_hload:
 move.b %a3@(38),%a2@(38)
 lea %a3@(40),%a0
 lea %a2@(40),%a1
 moveq #11,%d1
1: move.b (%a0)+,(%a1)+
 subq.l #1,%d1
 bpl 1b
 rts
gc_hinit:
 clr.b %d0
 move.b %d0,%a0@(38)
 lea %a0@(40),%a1
 moveq #11,%d1
1: clr.b (%a1)+
 subq.l #1,%d1
 bpl 1b
 rts
'''
 extra=[]
 if hierarchy:
  template=sub[:sub.index('.Lmode:')]
  def view(name,title,subtitle,rows,getrow,getedit):
   text=template.replace('gc_sub_draw',name).replace('gc_menu_row',getrow).replace('gc_menu_edit',getedit).replace('movel gc_row,%d0','jsr '+getrow).replace('moveq #5,%d0',f'moveq #{len(rows)},%d0')
   text=re.sub(r'    clrb %a0@\(\d+\)\n','',text)
   text=text.replace('    jsr '+getrow,''.join(f'    clrb %a0@({80+84*i})\n' for i in range(len(rows)))+'    jsr '+getrow,1)
   text=text.replace('.Lts_title_header: .long 6,6,0',f'.Lts_title_header: .long {len(title)},{len(title)},0').replace('.asciz "Groove"',f'.asciz "{title}"').replace('.Lts_subtitle_header: .long 5,5,0',f'.Lts_subtitle_header: .long {len(subtitle)},{len(subtitle)},0').replace('.asciz "Setup"',f'.asciz "{subtitle}"')
   for i,(label,fn) in enumerate(rows):text+=f'.Llabel{i}: .asciz "{label}"\n'
   text+='.Lallocator: .byte 0\n.balign 4\n.Lts_rows:\n'
   for i,(label,fn) in enumerate(rows):text+=f'.long 0,0,0,.Llabel{i},0,1,.Lts_label,0,0,0,0,0,0,1,{fn},0,0,0,0,0,0\n'
   return text
  extra=[('gc_top.S',view('gc_top_draw','Mod','Setup',[('','gc_top_global_value'),('','gc_top_track_value')],'gc_tree_row','gc_tree_edit')),
   ('gc_global.S',view('gc_global_draw','Global','Mod',[('Pad','wf_menu_value'),('USB','wf_usb_menu_value'),('Num','vp_menu_value'),('Mute','lm_menu_value'),('Dly','dl_menu_value'),('DX','dx_menu_value'),('QntM','gc_root_value'),('Grv','gc_root_value')]+([('LFOs','gc_lfo_value')] if lfo_options else []),'gc_tree_row','gc_tree_edit')),
   ('gc_track.S',view('gc_track_draw','Track','Mod',(([('SCRM','sx_root_value'),('S.Chn','du_root_value'),('Human','gc_root_value')]+([('LFO','gc_root_value')] if lfo_polarity else []))+([('LFO','gc_root_value')] if lfo_polarity else [])),'gc_tree_row','gc_tree_edit')),
   ('gc_human.S',view('gc_human_draw','Human','Track',([('Trk','gc_value1'),('Tim','gc_value2'),('Vel','gc_value3'),('Apply','gc_value6'),('Undo','gc_value7')] if human_apply else [('Trk','gc_value1'),('Tim','gc_value2'),('Vel','gc_value3')]),'gc_menu_row','gc_menu_edit'))]
  if lfo_polarity:extra.append(('gc_pol.S',view('gc_pol_draw','LFO','Polarity',[('Trk','gc_pol_value0'),('LFO','gc_pol_value1'),('Pol.','gc_pol_value2')],'gc_menu_row','gc_menu_edit')))
  sub=view('gc_sub_draw','Groove','Global',([('On','gc_value0'),('','gc_value5'),('Str','gc_value4')] if groove_switch else [('Grv','gc_value0'),('Str','gc_value4')]),'gc_menu_row','gc_menu_edit')
 for n,text in [('gc_root.S',rootmenu),('gc_sub.S',sub),('gc_tramp.S',tramp),('gc_pattern.S',hp)]+extra: (build/n).write_text(text)
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 for p in [src/('control175.c' if lfo_compact_ram else 'control174.c' if lfo_options else 'control163.c' if lfo_polarity else 'control162.c' if filter_modes else 'control161.c' if human_apply else 'control158.c' if groove_switch else 'control157.c' if hierarchy else 'control156.c'),*[build/n for n in ('gc_root.S','gc_sub.S','gc_tramp.S','gc_pattern.S')]+[build/n for n,_ in extra]]:
  obj=build/(p.name+'.o');objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418',*(['-DUI_IDLE210=1'] if ui_idle else []),*(['-DFILTER_KEYS202=1'] if filter_key_guard else []),'-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(p),'-o',str(obj)],check=True)
 if human_apply:aliases['hu_apply']=0x468c1000
 ld=build/'groove-strum.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 ld.write_text(f'SECTIONS {{ .text {UI:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} gc_code_end = .; .bss {BSS:#x} (NOLOAD): {{ *(.bss*) *(COMMON) }} . = ALIGN(4); gc_end = .; }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(v:=line.split())==3};assert sy['gc_code_end']<BSS and sy['gc_end']<END
 assert meta['private_retrosyn']['symbols']['retrosyn_code_end']<=CODE and END<=0x468bb000
 assert len(tail)>=END-TAIL and not any(tail[CODE-TAIL:END-TAIL]),'Reservation deja occupee'
 core.AMOUNTS=sy['gc_amounts'];core.GMODE=sy['gc_groove'];core.STRUM=sy['gc_strum'];core.CNT=sy['gc_ticks'];core.G0=sy['gc_g0']
 gc,gs=core.build_g2(core.M_T,sy['gc_rng']);gc=(gc[:gs['HUM']-core.M_G]+bytes.fromhex('4e75')) if human_apply else gc;tc,ts=core.build_t(0x468b2300,gs['HUM']);sc,ss=core.build_strum_core()
 assert core.M_G+len(gc)<=core.M_T and core.M_T+len(tc)<=0x468b2300 and core.M_ST+len(sc)<=UI
 tables=json.loads((src/'grooves.json').read_text())['grooves'];data=b''.join(struct.pack('64b',*next(t for t in tables if t['index']==i)['offset_256th_step'])+bytes(next(t for t in tables if t['index']==i)['velocity']) for i in range(1,8));assert len(data)==7*128
 pointers=struct.pack('>7I',*[0x468b2400+128*i for i in range(7)])
 for at,b in [(core.M_G,gc),(core.M_T,tc),(0x468b2300,pointers),(0x468b2400,data),(core.M_ST,sc),(UI,binary.read_bytes())]:put(at,bytes(len(b)),b)
 # Les cinq sites natifs restent gardes individuellement sur la composition finale.
 orig=bytes.fromhex('7e10c2874a41670c3208c3fc000c4c001800da81');h=b'\x4e\xb9'+struct.pack('>I',gs['G'])+struct.pack('>H',0x6000|(0x40054b0c-(0x40054af8+8)))+b'\x4e\x71'*6;assert len(h)==len(orig);put(0x40054af8,orig,h)
 for at,old,target in [(0x400ab240,bytes.fromhex('4cef1c3c0008'),ss['ST']),(0x400ab2d2,bytes.fromhex('223c20000000'),ss['G0F'])]:put(at,old,(b'\x4e\xf9' if at==0x400ab240 else b'\x4e\xb9')+struct.pack('>I',target))
 for at,old,target in hooks:put(at,old,b'\x4e\xf9'+struct.pack('>I',sy[target])+b'\x4e\x71'*((len(old)-6)//2))
 at=mq['mq_root_draw'];put(at,read(at,6),b'\x4e\xf9'+struct.pack('>I',sy['gc_root_draw']))
 (build/'groove-core.bin').write_bytes(gc);(build/'strum-core.bin').write_bytes(sc)
 return dict(code=CODE,ui=UI,bss=BSS,end=sy['gc_end'],code_bytes=sy['gc_code_end']-CODE,symbols={**sy,**{'G':gs['G'],'HUM':gs['HUM'],'T':ts['T'],'ST':ss['ST'],'G0F':ss['G0F']}},aliases=aliases,grooves=(['Boom Bap','Disco','Reggae','Bongo','Caixixi','Highlife','Kuduro'] if groove_switch else ['Swing','Boom Bap','Disco','Reggae','Bongo','Caixixi','Highlife','Kuduro']),pattern_header_bytes=[],humanize_storage=("Apply/Undo to pattern, stopped only; no playback randomization" if human_apply else "global per-track, /Groove.cfg; Chord Keys header untouched"),strum_range_ms=[-80,80],settings_file='/Groove.cfg',controls=('Mod Setup > Global/Track' if hierarchy else 'Mod Setup > Grv: Mode/Trk/Time/Vel/Strum'),hierarchy=hierarchy,separate_switch=groove_switch,default=('Off, Type Boom Bap, Humanize0, Strum0' if groove_switch else 'Swing, Humanize0, Strum0'),upstream='https://github.com/gialloinfuso/PPPCCC-Model-Cycles-1.13-Mods',upstream_revision='61c7432076e49b3050c7e076a5b602747d36fb8c',license='MIT',credit='PPPCCC/gialloinfuso',status='experimental',hardware_tested=False)
