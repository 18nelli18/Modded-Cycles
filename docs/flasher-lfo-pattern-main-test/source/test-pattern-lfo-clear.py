"""Vrai clear/Undo de pattern hors GRID : six LFO ; frontières modèle simulées."""
import json,struct,random
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as m
import build
from chord_keys_pr87 import load_stock
from test_track_lfo_clear import Fixture,DEFAULT1,DEFAULT2,DEFAULTR
import test_arp as ta
stock=load_stock('firmware/model-cycles_OS1.13.syx');cl=json.load(open('work/lfo-clear-v3/clear.json'));p=json.load(open('work/genie-controls-main/profiles.json'))['111'];lf=next(t for t in json.load(open('work/supermodel-support/frontend-catalog.json')) if t['id']=='lfo-secondary');cat={'tweaks':[p,lf]};im=bytearray(build.apply_writes(stock,[p,lf])[0])
for w in cl['writes']:im[w['off']:w['off']+len(bytes.fromhex(w['new']))]=bytes.fromhex(w['new'])
r=Fixture(bytes(im),cl,cat);r.w32(r.imp['A_audio_owner'],0)
raw=bytes.fromhex(p['append']['parts'][0]['hex']);r.uc.mem_write(int(p['append']['dest'],16),raw);r.uc.mem_write(int(cl['raw']['dest'],16),bytes.fromhex(cl['raw']['hex']))
# Six modèles inline : layout natif du getter 0x4000cfcc.
pattern=r.root+5192;ptnraw=0x93900000;kit=0x93910000;vt=0x93920000;get=0x93920100;notify=get+16;kitvt=vt+0x200;kitget=get+0x200
r.w32(pattern,vt);r.w32(vt+40,get);r.w32(vt+16,notify);r.custom[get]=lambda a:ptnraw;r.custom[notify]=lambda a:0
r.w32(r.root+116,kitvt);r.w32(kitvt+48,kitget);r.custom[kitget]=lambda a:kit;r.w32(kitvt+92,notify)
r.custom[0x400cfd0e]=lambda a:0x93930000;r.custom[0x4006a96c]=lambda a:0
r.custom[0x400d0974]=lambda a:0x93930100;r.custom[0x400060d8]=lambda a:0x93930200
r.custom[0x400d4082]=lambda a:r.uc.mem_write(a[0],bytes(8)) or a[0]
r.custom[0x4007700e]=lambda a:0
for i,tr in enumerate(r.tracks):
 old=tr.obj;tr.obj=pattern+112+88*i;r.uc.mem_write(tr.obj,r.rd(old,88))
 r.custom[tr.f10]=lambda a,i=i:r.tracks[i].data
r.custom[0x4000f23e]=lambda a:r.tracks[r.sel].obj
rng=random.Random(908);r.uc.mem_write(ptnraw,bytes(rng.randrange(256) for _ in range(30710)));r.uc.mem_write(kit,bytes(7094));before=r.all_state();pattern_before=r.rd(ptnraw,30710)
try:assert r.invoke(0x4001b1c0)==1
except Exception:
 print('FAIL PC/regs',hex(r.uc.reg_read(m.UC_M68K_REG_PC)),{n:hex(r.uc.reg_read(getattr(m,'UC_M68K_REG_'+n))) for n in ['D0','D1','D2','D3','D4','D5','D6','D7','A0','A1','A2','A3','A4','A5','A6','A7']},flush=True);raise
print('outcome',r.r32(r.s['avcl_p_outcome']),'valid',r.r32(r.s['avcl_p_valid']),flush=True)
after=r.all_state();assert r.rd(ptnraw,30710)!=pattern_before
for i in range(6):
 assert after['sound'][i][22:38]==DEFAULT1,(i,'LFO1')
 assert after['sound'][i][76:86]==DEFAULT2,(i,'LFO2')
 assert after['cfg'][i*16:i*16+16]==DEFAULTR
try:assert r.invoke(0x4001b1c0)==1
except Exception:
 print('UNDO FAIL',hex(r.uc.reg_read(m.UC_M68K_REG_PC)),{n:hex(r.uc.reg_read(getattr(m,'UC_M68K_REG_'+n))) for n in ['D0','D1','D2','A0','A1','A2','A3','A4','A5','A6','A7']},flush=True);raise
print('undo outcome',r.r32(r.s['avcl_p_outcome']),flush=True)
assert r.rd(ptnraw,30710)==pattern_before
assert r.all_state()==before
print('PASS vrai clear pattern hors GRID et Undo : séquence native, six LFO1/LFO2 et phases restaurés exactement.')

# Un Load invalide le snapshot LFO même si le record natif est encore présent.
assert r.invoke(0x4001b1c0)==1
r.w32(r.imp['A_LF2_epoch'],24)
cleared=r.all_state()
assert r.invoke(0x4001b1c0)==1
assert r.all_state()['sound']==cleared['sound']
assert r.all_state()['cfg']==cleared['cfg']
print('PASS epoch Load changé : aucun ancien LFO restauré par Undo.')
