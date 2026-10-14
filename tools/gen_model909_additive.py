#!/usr/bin/env python3
"""Prototype additif Model909 : quatre machines, cinq familles de voix.

BD909, SD909, RC909 (rim/clap), TM909 (trois toms), après le Sampler TG.
Les six moteurs stock, leurs tables et descripteurs restent ceux du main.
Source DMDaudio/model909, MIT ; aucune ROM de hats/cymbales incluse.
"""
import argparse,json,pathlib,struct,tempfile
import build,gen_macro as gm,gen_syntakt_engines as gs,gen_sdvintage_7th as g7
SRC=pathlib.Path(__file__).resolve().parent/'machines/model909'
MACHINES=[
 ('BD909','bd',(('BD Attack','ATCK',64),('BD Shape','SHPE',64),('BD Sweep','SWP',64),('BD Sweep Time','STIM',64))),
 ('SD909','sd',(('SD Snappy','SNAP',64),('SD Tone','TONE',64),('SD Pitch Drop','DROP',64),('SD Body','BODY',64))),
 ('RC909','rc',(('RC Tone','TONE',64),('RC Type','TYPE',0,0,1),('RC Spread','SPRD',64),('RC Burst','BRST',64))),
 ('TM909','tom',(('Tom Noise','NOIS',64),('Tom Type','TYPE',0,0,2),('Tom Sweep','SWP',64),('Tom Sweep Time','STIM',64)))]
def context(img,t):
 ap=t['append'];assert len(ap['parts'])==1 and ap['at']==ap['dest'] and int(ap['at'],16)==build.BASE+len(img)
 cur,_=build.apply_writes(img,[t]);tg={k:int(v,16) for k,v in t['symbols'].items()};tg.update(img=bytes(cur),blob=bytes.fromhex(ap['parts'][0]['hex']),blob_at=int(ap['at'],16),at=int(ap['at'],16)+ap['size'],id=t['id'],symbols_hex=t['symbols']);assert tg['at']==tg['reserved_end'];return tg
def compile_machine(tmp,pay,tg,stock_slots=False):
 objs=[]
 for name in ['t9_cycles.c','t9.c']:
  # Le dispatch ajouté applique déjà ah_noenv : ne pas appeler cet étage deux fois.
  out=tmp/(name+'.o');gm.gx.run([gm.gx.CROSS+'gcc','-mcpu=54418','-O2','-malign-int','-ffreestanding','-fno-builtin','-fno-tree-loop-distribute-patterns','-fno-pic','-fno-common','-ffunction-sections','-fdata-sections','-fomit-frame-pointer','-Wall','-Werror','-Wno-unused-function','-Wno-unused-const-variable','-DT9_ANALOG_ONLY',*([f'-DT9_AH_NOENV={tg["ah_noenv"]:#x}'] if stock_slots else []),'-I'+str(SRC),'-c',str(SRC/name),'-o',str(out)]);objs.append(out)
 ld=tmp/'link.ld';ld.write_text(gm.LINK.format(code=pay,bss=pay+gm.BSS_OFF));elf=tmp/'909.elf';raw=tmp/'909.bin';keep=[x for _,pre,_ in MACHINES for n in ['update','render'] for x in ['-u',f't9_{pre}_{n}']]
 gm.gx.run([gm.gx.CROSS+'ld','-T',str(ld),'--gc-sections','--no-warn-rwx-segments','-e','t9_bd_update',*keep,'-o',str(elf),*map(str,objs)])
 gm.gx.run([gm.gx.CROSS+'objcopy','-O','binary','-R','.bss',str(elf),str(raw)]);blob=raw.read_bytes();syms={}
 for line in gm.gx.run([gm.gx.CROSS+'nm',str(elf)]).splitlines():
  p=line.split()
  if len(p)==3:syms[p[2]]=int(p[0],16)
  elif len(p)==2 and p[0]=='U':raise SystemExit('!! symbole externe : '+p[1])
 sections={p[1]:(int(p[3],16),int(p[2],16)) for p in (line.split() for line in gm.gx.run([gm.gx.CROSS+'objdump','-h',str(elf)]).splitlines()) if len(p)>4 and p[0].isdigit()}
 assert set(sections)<=set(['.text','.rodata','.data','.bss']);assert pay+len(blob)<gs.STUBS
 bss,size=sections['.bss'];assert bss==pay+gm.BSS_OFF;return blob,syms,(bss+size+3)&~3
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--tg-recipe',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();img=g7.cycles_main(a.cycles);t=json.loads(pathlib.Path(a.tg_recipe).read_text());tg=context(img,t);gs.set_base(gs.PAY_TG)
 with tempfile.TemporaryDirectory() as d:
  tmp=pathlib.Path(d);blob,syms,end=compile_machine(tmp,gs.PAY_TG,tg);machines=[dict(name=n,label=n,image=[0,1,3,4][i],decay=64,knobs=k,update=syms[f't9_{pre}_update'],render=syms[f't9_{pre}_render']) for i,(n,pre,k) in enumerate(MACHINES)];writes,append=gm.added_machine(img,tg,machines,tmp,[(gs.PAY_TG,blob)],end)
 out={'id':'model909-additive-tg','order':34,'status':'experimental','name':'Model909 : voix additionnelles BD, SD, rim/clap et toms','description':['Voix analogiques DMDaudio/model909 (MIT), ajoutées après le Sampler TG ; six machines stock conservées.','Prototype isolé : intégrations moteur et Banque restantes à vérifier. Aucun échantillon ROM.'],'requires':[t['id']],'conflicts':sorted(gm.other_ids()|{'macro','macro-tg','acid','acid-tg','macro-acid','macro-acid-tg'}),'writes':writes,'append':append,'symbols':{k:hex(v) for k,v in syms.items()},'source':{'repo':'DMDaudio/model909','license':'MIT','commit':'12e359160132fe7df4560ee3e53bd50ab9eebd2b','analog_only':True,'stock_machines_preserved':True}}
 build.apply_writes(img,[t,out]);s=json.dumps(out,ensure_ascii=False,indent=1)+'\n';path=pathlib.Path(a.output)
 if a.check:assert path.read_text()==s
 else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(s)
 print('ok : Model909 additif,',len(blob),'octets code/tables ; quatre machines après TG')
if __name__=='__main__':main()
