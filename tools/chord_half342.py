"""Comparaison CHORD24k :17 points, reconstruction32frames, horloge48k intacte.

Seuls les oscillateurs sont sous-echantillonnes. Un point de regard avance
permet l interpolation sans historique partage ni rupture aux bords de bloc.
Les pas de phase, gain et poids sont doubles puis le cadre natif restaure.
"""
from pathlib import Path
import hashlib,os,re,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
CODE=0x467a6000;END=0x467a8000;FRAME=96

def source():
 s=(ROOT/'tools/machines/chord_cpu/oscillator.S').read_text()
 assert s.count('.rept 4')==4
 s=s.replace('.rept 4','.rept 2').replace('moveq #8,%d0','moveq #16,%d0')
 for macro in ['TWO 0','TWO 1','ONE 0','ONE 1']:
  block='#ifdef CHORD_SECOND_FAST\n '+macro+'\n '+macro+'\n#endif'
  assert s.count(block)==1;s=s.replace(block,'')
 s=s.replace('moveq #16,%d0','moveq #8,%d0')
 def macro(name):return re.search(r'\.macro '+name+r'\b.*?\.endm',s,re.S).group()
 peeks=[]
 for name in ['TWO','ONE','SECOND']:
  body=macro(name).replace('.macro '+name+' ','.macro QH_'+name+' ',1)
  body=body.replace(' addl %a4,%d7\n','').replace(' addl %fp,%d1\n','')
  peeks.append(body)
 pm=macro('PM_CONST')
 peek=pm.replace('.macro PM_CONST ','.macro QH_PM ',1)
 for line in [' addl %sp@(100),%d4\n',' addal %sp@(104),%fp\n',' addl %sp@(80),%d7\n',' movel %d7,%acc1\n',' addl %sp@(84),%d1\n',' macl %d4,%d3,%a2@+,%d3,%acc1\n']:
  assert line in peek;peek=peek.replace(line,'')
 peek=peek.replace(' msacl %d1,%d6,%a1@+,%d3,%acc0',' msacl %d1,%d6,%acc0')
 peeks.append(peek)
 # Les modulations sont des tableaux48k : visiter les indices pairs, y compris32.
 changed=pm.replace(' msacl %d1,%d6,%a1@+,%d3,%acc0',' addq.l #4,%a1\n msacl %d1,%d6,%a1@+,%d3,%acc0').replace(' macl %d4,%d3,%a2@+,%d3,%acc1',' addq.l #4,%a2\n macl %d4,%d3,%a2@+,%d3,%acc1')
 s=s.replace(pm,changed)
 # Chaque chemin rend son17e point sans avancer les controles une33e fois.
 for label,dest in [('chord_second_const','qh_second'),('chord_second_ramp','qh_second'),('.Ltwo_const','qh_two'),('.Ltwo_ramp','qh_two'),('.Lone_const','qh_one')]:
  start=s.index('\n'+label+':');end=s.index(' braw .Ldone',start)
  s=s[:end]+s[end:].replace(' braw .Ldone',' braw '+dest,1)
 s=s.replace('\n.Ldone:\n','\n braw qh_one\n.Ldone:\n',1)
 for label,dest in [('.Lpm_loop','qh_pm_both'),('.Lpm_first_loop','qh_pm_first'),('.Lpm_second_loop','qh_pm_second')]:
  start=s.index('\n'+label+':');end=s.index(' braw .Lpm_finish',start)
  s=s[:end]+s[end:].replace(' braw .Lpm_finish',' braw '+dest,1)
 s=s.replace('\n.Lpm_finish:\n','\n braw qh_pm_both\n.Lpm_finish:\n',1)
 assert s.count('jmp 0x400a89d4')==2
 s=s.replace('jmp 0x400a89d4','jmp qh_expand')
 s+='\n'+'\n'.join(peeks)+'\n'
 for label,operation,finish in [('qh_two','QH_TWO 0','.Ldone'),('qh_one','QH_ONE 0','.Ldone'),('qh_second','QH_SECOND 0','.Ldone'),('qh_pm_both','QH_PM 0,0','.Lpm_finish'),('qh_pm_first','QH_PM 1,0','.Lpm_finish'),('qh_pm_second','QH_PM 2,0','.Lpm_finish')]:
  s+=f'{label}:\n {operation}\n bra.w {finish}\n'
 # Tous les operandes du noyau continuent de designer son cadre natif.
 s=re.sub(r'%sp@\((\d+)\)',lambda m:f'%sp@({int(m[1])+FRAME})',s)
 words=[80,84,100,104,116,120]
 entry=f' lea -{FRAME}(%sp),%sp\n movem.l %d0-%d1/%a0-%a1,(%sp)\n move.l %a0,40(%sp)\n move.l %a3,44(%sp)\n'
 for i,offset in enumerate(words):entry+=f' move.l {FRAME+offset}(%sp),%d0\n move.l %d0,{16+4*i}(%sp)\n add.l %d0,%d0\n move.l %d0,{FRAME+offset}(%sp)\n'
 entry+=' movem.l (%sp),%d0-%d1/%a0-%a1\n'
 guard=''' move.l %a0,%d0
 sub.l %a3,%d0
 cmpi.l #128,%d0
 bcs.w qh_alias
 move.l %a3,%d0
 sub.l %a0,%d0
 cmpi.l #128,%d0
 bcs.w qh_alias
'''
 s=s.replace('chord_fast:\n','chord_fast:\n'+guard+'\nqh_enter:\n'+entry,1)
 tail='\nqh_expand:\n move.l %d1,48(%sp)\n move.l %d7,52(%sp)\n'
 for slot in [40,44]:
  tail+=f''' movea.l {slot}(%sp),%a0
 lea 64(%a0),%a1
 lea 128(%a0),%a2
 moveq #15,%d0
qh_expand_{slot}:
 move.l (%a1),%d2
 move.l -(%a1),%d3
 move.l %d2,%d4
 eor.l %d3,%d4
 asr.l #1,%d4
 and.l %d3,%d2
 add.l %d2,%d4
 move.l %d4,-(%a2)
 move.l %d3,-(%a2)
 subq.l #1,%d0
 bpl.w qh_expand_{slot}
'''
 for i,offset in enumerate(words):tail+=f' move.l {16+4*i}(%sp),%d0\n move.l %d0,{FRAME+offset}(%sp)\n'
 tail+=f''' move.l 48(%sp),%d1
 move.l 52(%sp),%d7
 movea.l 40(%sp),%a0
 lea 128(%a0),%a0
 movea.l 44(%sp),%a3
 lea 128(%a3),%a3
 lea {FRAME}(%sp),%sp
 jmp 0x400a89d4
'''
 return s+tail+'\nqh_alias:\n jmp qh_old\n'

def apply(meta,native,runtime,out):
 base=0x46700000;nb=0x40000400;out=Path(out);out.mkdir(parents=True,exist_ok=True)
 assert not meta.get('chord_half_rate')
 assert any(e['kind']=='remove' and e['address']<=CODE and END<=e['address']+e['bytes'] for e in meta['clean_layout']['retirement']['edits'])
 assert not any(runtime[CODE-base:END-base])
 old=bytes(native[0x400a8906-nb:0x400a890c-nb]);assert old==b'\x4e\xf9'+struct.pack('>I',meta['chord_second']['symbols']['chord_fast'])
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
 os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
 (out/'chord-half.S').write_text(source());run('gcc','-mcpu=54418','-DCHORD_SECOND_FAST','-DCHORD_ECO_LOOKUP','-c',out/'chord-half.S','-o',out/'chord-half.o')
 run('ld','-Ttext',hex(CODE),'--defsym','qh_old='+hex(meta['chord_second']['symbols']['chord_fast']),'-e','chord_fast','-o',out/'chord-half.elf',out/'chord-half.o');run('objcopy','-O','binary',out/'chord-half.elf',out/'chord-half.bin')
 blob=(out/'chord-half.bin').read_bytes();assert CODE+len(blob)<=END
 symbols={v[2]:int(v[0],16) for line in run('nm',out/'chord-half.elf').splitlines() if len(v:=line.split())==3}
 new=b'\x4e\xf9'+struct.pack('>I',symbols['chord_fast']);native[0x400a8906-nb:0x400a890c-nb]=new;runtime[CODE-base:CODE-base+len(blob)]=blob
 return dict(code=CODE,code_bytes=len(blob),symbols=symbols,sha256=hashlib.sha256(blob).hexdigest(),patches=[dict(at=0x400a8906,old=old.hex(),new=new.hex())],oscillator_rate=24000,output_rate=48000,lookahead_points=1,new_state_bytes=0,quality_changed=True,hardware_tested=False)
