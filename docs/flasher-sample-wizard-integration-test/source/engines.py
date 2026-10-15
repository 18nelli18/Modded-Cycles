"""Prototype privé : Wizard autonome + moteurs, MACRO, ACID corrigée et WAVE.

Le mode « tg » du générateur désigne ici seulement la présence d'un sampler
au slot 6. Son contexte est notre extraction ; aucun mod Model-TG requis.
"""
import pathlib,json,copy,struct,importlib.util
import build,syntakt,gen_syntakt_engines as gs,gen_macro_syntakt as gms,gen_macro as gm,gen_acid as ga
from chord_keys_pr87 import load_stock
from gen_seq_gen import symbols
gs.gx.CROSS='m68k-elf-'
P=pathlib.Path('work/sample-wizard-main');stock=load_stock('firmware/model-cycles_OS1.13.syx');st=syntakt.dsp_image('firmware/Syntakt_OS1.42.syx');wizard=json.load(open(P/'installer.json'));sy={k:int(v,16) for k,v in wizard['symbols'].items()};cur=bytes(build.apply_writes(stock,[wizard])[0]);raw=build.payload_runtime(wizard,stock,None)
ctx=dict(sy,img=cur,blob=raw,blob_at=int(wizard['append']['at'],16),at=int(wizard['append']['at'],16)+len(raw),id='sample-wizard',symbols_hex=wizard['symbols']);ctx['mod_held']=sy['av_never'];ctx['ah_noenv']=sy['av_noop']
legacy=gs.tg_context(stock);oldsy=symbols('m68k-elf-',pathlib.Path('../model-tg/build/_b.elf'));oldsy.update({k:int(v,16) for k,v in legacy['symbols_hex'].items()});mapping={v:sy[k] for k,v in oldsy.items() if k in sy and 0x401ab750<=v<int(legacy['reserved_end'])}
def relocated(b):
 b=bytearray(b)
 for at in range(0,len(b)-3,2):
  v=struct.unpack_from('>I',b,at)[0]
  if v in mapping:struct.pack_into('>I',b,at,mapping[v])
 return bytes(b)
# Quinze machines au maximum : tables explicitement bornées, 8+7 repères.
original_rows=gs.set_rows

def rows(n):
 original_rows(n)
 if n==8:
  for k,off in dict(DESCN=0x33f00,ROWSN=0x35860,CCROWSN=0x35a40,RECS=0x35c20,REC_ATK=0x35f20).items():setattr(gs,k,gs.PAY+off)
 else:
  gs.DESCN=gs.PAY+gs.LAYOUT['DESCN'];gs.RECS=gs.PAY+gs.LAYOUT['RECS'];gs.REC_ATK=gs.PAY+gs.LAYOUT['REC_ATK']
gs.set_rows=rows;gs.MAX_EXTRA=8;gs.MARKS_ROW=8
oldmarks=gs.marks_asm

def marks(a,ins,lab,nm):
 first=len(a);oldmarks(a,ins,lab,nm)
 for i in range(first,len(a)):
  if a[i]=='\tlsl.l #3, %d0':a[i]='\tmulu.w #6, %d0'
  elif a[i]=='\tsub.l %d4, %d0':a[i]='\tnop'
gs.marks_asm=marks
# Pas de mesure CPU ni d'étage d'effets TG ajouté aux moteurs externes.
old_dispatch=gs.dispatch_tg_asm

def dispatch(syms,rnd_at,tg):
 text=old_dispatch(syms,rnd_at,tg);a=text.index('4:\tmove.l\t0xfc07800c');b=text.index('\tmovea.l\t%d6',a);text=text[:a]+'4:\n'+text[b:];a=text.index('\tmove.l\t0xfc07800c',text.index('4:\n'));b=text.index('9:\tjmp',a);text=text[:a]+text[b:];text=text.replace(f"\tjsr\t{tg['ah_noenv']:#x}", '\tnop');return text
gs.dispatch_tg_asm=dispatch
# WAVE compilée depuis les sources MIT déjà intégrées à la branche principale.
spec=importlib.util.spec_from_file_location('wizard_wavetable',pathlib.Path('work/kevin-wave-acid/tools/gen_wavetable.py'));gw=importlib.util.module_from_spec(spec);spec.loader.exec_module(gw)
# Réassembler la glue avec les deux buffers partagés : les LEA PC-relatifs
# ne peuvent pas être déplacés après l'assemblage par un simple remplacement.
old_glue,old_smp=gw.glue_asm,gw.smp_glue_asm
def shared_glue(symbols,mach=6):
 text=old_glue(symbols,mach).replace('wt_msg:\t.space\t64','wt_msg_unused:\t.space\t64')
 assert 'wt_msg_unused:' in text
 return text+'\n.equ wt_msg, '+hex(sy['msg_buf'])+'\n'
def shared_smp():
 text=old_smp().replace('smp_mode:\t.long\t0','smp_mode_unused:\t.long\t0')
 assert 'smp_mode_unused:' in text
 return text+'\n.equ smp_mode, '+hex(sy['id_mode'])+'\n'
gw.glue_asm,gw.smp_glue_asm=shared_glue,shared_smp
basecat=json.load(open('work/lfo-clear-test3/chosen-tg-select-all.json'));known=next(t for t in basecat if t['id'].startswith('syntakt-tg'));codes=tuple(gs.CATALOG);pay=gs.PAY_TG;gs.set_base(pay);an=gs.analyse(st,gs.generation(codes));lay=an['lay'];gs.dispatch_tg_asm=old_dispatch;gs.marks_asm=oldmarks;gs.MARKS_ROW=7;gs.set_rows=original_rows
tw=gms.versioned(codes,True)
parts0={int(p['dest'],16):p for p in tw['append']['parts'] if 'hex' in p};nm=7+len(codes);dat=bytes.fromhex(parts0[gs.DATA]['hex']);bsy={k:int(v,16) for k,v in tw['gov'].items()}
for i,c in enumerate(codes):
 e=gs.CATALOG[c]['engine'];bsy['bridge_update_'+str(e)]=struct.unpack_from('>I',dat,4*(nm+7+i))[0];bsy['bridge_render_'+str(e)]=struct.unpack_from('>I',dat,4*(2*nm+7+i))[0]
stubs0=bytes.fromhex(parts0[gs.STUBS]['hex']);after=next(w for w in tw['writes'] if w['off']+build.BASE==gs.TG_AFTER[0]);entry=int(after['new'][4:12],16)-gs.STUBS;assert stubs0[entry:entry+6]==bytes.fromhex('2f032f024eb9');bsy['voice_done']=int.from_bytes(stubs0[entry+6:entry+10],'big')
br=dict(bridge=bytes.fromhex(parts0[gs.DST_BRIDGE]['hex']),hot=[(at,bytes.fromhex(parts0[at]['hex']),None) for at,_,_ in lay['tails'] if at in parts0],syms=bsy,gov=tw['gov'],extra=[])
gs.STUBS=pay+0x32a00
gs.dispatch_tg_asm=dispatch;gs.marks_asm=marks;gs.MARKS_ROW=8;gs.set_rows=rows
br['bridge']=relocated(br['bridge']);br['hot']=[(at,relocated(b),f) for at,b,f in br['hot']]
parts=list(br['extra']);machines=[]
for label,meta,at,up,rnd in [('MACRO',gm.MACHINE,pay+0x42000,'macro_update','macro_render'),('ACID',ga.MACHINE,pay+0x76000,'acid_update','acid_render')]:
 part=copy.deepcopy(next(p for p in known['append']['parts'] if int(p['dest'],16)==at and 'hex' in p));parts.append(part);machines.append(dict(meta,label=label,update=int(known['symbols'][up],16),render=int(known['symbols'][rnd],16)))
 # Comparaison directe avec la recette Kevin corrigée, pas une simple étiquette.
 if label=='ACID':
  pairs=json.load(open('work/sample-wizard-current-main/source/acid-fade-map.json'))['maps']['pairs'];assert any(part==p['new_part'] for p in pairs),'corps ACID non corrigé'
wave=gw.wave_part(pay+0x79000,pay+0x7b000,7+len(codes)+2,pay+0x7b000);parts += [dict(dest=hex(at),hex=b.hex()) for at,b in wave['blobs']];machines.append(wave['machine'])
own=dict(machines=machines,bridge=br,end=wave['end'],boot2=((lay['end']+15)&~15,pay+0x42000),parts=parts)
t,ndesc=gs.build_tweak(stock,st,codes,tg=ctx,own=own);t.update(id='wizard-engines-all-wave',requires=['sample-wizard'],conflicts=[],status='experimental');t['symbols']=dict(known['symbols'],**gw.wave_symbols(wave['syms'],wave['gsyms']));(P/'engine-all.json').write_text(json.dumps(t));(P/'wave.json').write_text(json.dumps(wave,default=lambda x:x.hex() if isinstance(x,bytes) else x));(P/'wave-writes.json').write_text(json.dumps(gw.wave_writes(stock,wave['gsyms'])));(P/'relocation-map.json').write_text(json.dumps({hex(k):hex(v) for k,v in mapping.items()}));build.apply_writes(stock,[wizard,t]);print('PASS Wizard + cinq moteurs + MACRO + ACID corrigée + WAVE :',ndesc,'descripteurs,',wave['end']-pay,'octets RAM ; aucun mod Model-TG requis',flush=True)
