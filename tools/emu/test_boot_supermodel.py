#!/usr/bin/env python3
"""SUPERMODEL : vraie tâche ColdFire,80images DSPI,contrat et incompatibilité."""
import argparse,json,pathlib,tempfile,subprocess
import build,gen_boot_supermodel as G
from test_sdvintage import main_os_from_syx
from test_boot_anim import Rig,contract,save,TASK,BUF_PTRS,STACK,TICK_CB,SEM_TICK,SEM_DONE

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--gif');ap.add_argument('--png');ap.add_argument('--with-catalog');ap.add_argument('--render-python');a=ap.parse_args();stock=main_os_from_syx(a.cycles);tw=G.generate(stock)
 root=pathlib.Path(__file__).resolve().parents[2];old=json.loads((root/'tweaks/model-cycles_OS1.13/43-boot-anim.json').read_text())
 try:build.check_conflicts([old,tw])
 except SystemExit:pass
 else:raise AssertionError('Les deux animations doivent être refusées')
 image,_=build.apply_writes(stock,[tw]);original=Rig(stock,stock_tiles=True);original.run(TASK);r=Rig(bytes(image));r.run(TASK)
 assert contract(original.calls)==contract(r.calls)
 assert contract(r.calls)[1]==(('attente',SEM_TICK),90)
 assert contract(r.calls)[2:]==[(('signal',SEM_DONE),1),(('minuteur-',TICK_CB),1),(('fin',SEM_TICK),1)]
 sent=r.frames[1:G.NF+1];want=G.frames();assert len(sent)==G.NF
 assert sent==want,[i for i in range(G.NF) if sent[i]!=want[i]][:10]
 assert all(f==want[-1] for f in r.frames[G.NF+1:])
 assert r.frames[0]==[[0]*128 for _ in range(64)]
 assert not r.bad and not original.bad
 bufs={r.r32(BUF_PTRS),r.r32(BUF_PTRS+4)};ranges=[(b,b+1024) for b in bufs]+[(BUF_PTRS,BUF_PTRS+8),(0xfc03c000,0xfc03c040),(STACK-0x10000,STACK)]
 assert not [x for x in r.writes if not any(lo<=x<hi for lo,hi in ranges)]
 assert G.TITLE_X+len(G.TC)==G.CREDIT_X+len(G.CC) and G.CREDIT_H<G.TITLE_H
 print('ok :80images natives pixel exact, signature petite alignée à droite,1,8s stock,signal/minuteur/écritures bornées,ancienboot incompatible',flush=True)
 if a.with_catalog:
  c=json.loads(pathlib.Path(a.with_catalog).read_text());ids=['6ch-usbup','model-tg-st','sample-preview-st','trig-hold','arp','tempo-max','multiline-browser','level-pan-values','trigless-dim','midi-live-both','syntakt-tg-sd-cp-toy-bits-swarm-macro-acid','scale-gen-st-queued','lfo-secondary','scramble-st-gen-queued']
  chosen=[next(t for t in c['tweaks'] if t['id']==id) for id in ids]
  chosen += [t for t in c['tweaks'] if t['id']=='midi-bank-bundle']
  build.check_conflicts(chosen+[tw])
  image,_=build.apply_writes(stock,chosen+[tw]);combo=Rig(bytes(image));combo.run(TASK);assert combo.frames==r.frames and not combo.bad
  print('ok : images et contrat identiques avec tous les mods sélectionnés',flush=True)
 if a.render_python:
  with tempfile.TemporaryDirectory() as tmp:
   f=pathlib.Path(tmp)/'frames.json';f.write_text(json.dumps(sent));cmd=[a.render_python,str(root/'tools/render_supermodel_startup.py'),'--frames',str(f)]
   if a.gif:cmd+=['--gif',a.gif]
   if a.png:cmd+=['--png',a.png]
   subprocess.run(cmd,check=True)
 elif a.gif or a.png:save(sent,a.gif,a.png)
if __name__=='__main__':main()
