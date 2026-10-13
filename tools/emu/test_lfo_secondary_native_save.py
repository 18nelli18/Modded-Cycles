#!/usr/bin/env python3
"""LFO2 natif : codec OS réel, pont UI/son et remise aux défauts des extras.

Backend UI simulé pour les getters ; aucun résultat matériel revendiqué.
"""
import argparse,json,pathlib,struct
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
import test_lfo_plus as upstream
import build


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--cycles',required=True);ap.add_argument('--tweak',required=True)
 a=ap.parse_args();stock=main_os_from_syx(a.cycles)
 tweak=json.loads(pathlib.Path(a.tweak).read_text())
 patched=build.apply_writes(stock,[tweak])[0]
 upstream.sound(stock,patched,[],{})
 assert not upstream.FAIL,upstream.FAIL
 r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}})
 r.s={k:int(v,16) for k,v in tweak['symbols'].items()}
 for w in tweak['writes']:r.u.mem_write(build.BASE+w['off'],bytes.fromhex(w['new']))
 ctx,frame,access,track,vt,sound=0x93100000,0x93101000,0x93102000,0x93103000,0x93104000,0x93105000
 get_sound,notify=0x93106000,0x93106010
 r.w32(access+4,track);r.w32(track,vt);r.w32(vt+40,get_sound);r.w32(vt+16,notify)
 notices=[]
 def notification(args):
  assert args[0]==track
  notices.append(r.r32(args[1]+4));return 0
 for address,fn in ((0x400cf866,lambda args:0x93107000),(get_sound,lambda args:sound),
                    (notify,notification),(0x400097f0,lambda args:access)):
  existing=address in r.stubs;r.stubs[address]=fn
  if not existing:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=address,end=address)
 r.u.mem_write(ctx,bytes(1240));r.w32(r.s['lf2_context'],ctx)
 values=(0x5aff,11,0x1234,14,3,0x5678,4,0x23ff)
 expected=(0x5aff,0x0b00,0x0300,0x0e00,0x23ff)
 for field,value in enumerate(values):assert r.call('lf2_edit',ctx,0,field,value)==1
 assert struct.unpack('>5H',bytes(r.u.mem_read(sound+76,10)))==expected
 assert notices==[28,29,31,30,32],notices
 assert struct.unpack('>8H',bytes(r.u.mem_read(ctx+192,16)))==(0x5aff,0xb00,0x1234,0xe00,0x300,0x5678,0x400,0x23ff)
 print('ok : huit edits UI, cinq champs natifs notifiés, extras indépendants en RAM')
 for t in range(6):r.u.mem_write(frame+70+t*66,struct.pack('>5H',*expected))
 r.w32(r.s['lf2n_epoch'],1);r.w32(r.s['lf2n_seen'],0)
 r.call('lf2n_sync',ctx,frame)
 loaded=(0x5aff,0xb00,0x4000,0xe00,0x300,0,0,0x23ff)
 for t in range(6):assert struct.unpack('>8H',bytes(r.u.mem_read(ctx+192+16*t,16)))==loaded
 r.u.mem_write(ctx+196,struct.pack('>H',0x1234));r.call('lf2n_sync',ctx,frame)
 assert bytes(r.u.mem_read(ctx+196,2))==b'\x12\x34'
 r.w32(r.s['lf2n_epoch'],2);r.call('lf2n_sync',ctx,frame)
 assert bytes(r.u.mem_read(ctx+196,2))==b'\x40\x00'
 assert r.call('lf2_edit',ctx,0,3,127)==1
 assert bytes(r.u.mem_read(sound+82,2))==bytes(2)
 r.u.mem_write(frame+76,bytes(2));r.call('lf2n_sync',ctx,frame)
 assert bytes(r.u.mem_read(ctx+198,2))==b'\x7f\x00'
 print('ok : six pistes restaurées ; trois extras remis aux défauts à chaque Load, OFF traduit sans destination illégale')
 import test_lfo_secondary_state as audio
 audio.PLACED=a.tweak;engine=audio.Rig(stock);audio.install_entry(engine)
 engine.emac.macsr=0x20;audio.dispatch(engine)
 print('Limite : getters/notifications simulés ; persistance matérielle à valider.')


if __name__=='__main__':main()
