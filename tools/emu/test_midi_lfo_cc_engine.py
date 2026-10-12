#!/usr/bin/env python3
"""LFO MIDI : adaptateur ColdFire et moteur natif, sans toucher l'état audio."""
import argparse,pathlib,subprocess,tempfile,struct
from unicorn import m68k_const as mk
from test_tempo_max import Rig,LFO_PHASE,OBJ
import test_lfo_secondary_state as native
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 r=Rig(main_os_from_syx(a.cycles));native.install_entry(r);r.emac.macsr=0x20
 with tempfile.TemporaryDirectory() as temp:
  p=pathlib.Path(temp);objects=[]
  for name in ('frame','settings','queue','lane'):
   obj=p/(name+'.o');objects.append(str(obj))
   subprocess.run([cross+'as','-march=cfv4e','-o',str(obj),str(root/'tools/machines/midi_lanes'/('lfo_cc_'+name+'.s'))],check=True)
  subprocess.run([cross+'ld','-Ttext=0x93040000','-e','mlcc_frame_prepare','-o',str(p/'e.elf'),*objects],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'e.elf'),str(p/'e.bin')],check=True)
  r.uc.mem_write(0x93040000,(p/'e.bin').read_bytes());s=symbols(cross,p/'e.elf')
 def call(name,*args):return r.call(s[name],*args)[0]
 cfg=0x93060000;frame=0x93061000;state=0x93062000;q=0x93063000;pattern=0x93064000
 r.uc.reg_write(mk.UC_M68K_REG_SR,0x2000);assert call('mlcc_cfg_init',cfg)==1
 # Vérifier l'encodage natif et les128 CC, qui doivent tous viser le dummy11.
 for cc in range(129):
  for lfo in range(2):
   for lane in range(6):
    for field,value in enumerate((20000+lane,9,16384,cc,3,16384,0,28000)):
     assert call('mlcc_cfg_edit',cfg,lane,lfo,field,value)==1
   before=bytes(r.uc.mem_read(cfg,192))
   assert call('mlcc_frame_prepare',cfg,frame,lfo)==1
   assert bytes(r.uc.mem_read(cfg,192))==before
   for lane in range(6):
    values=struct.unpack('>8H',r.uc.mem_read(frame+lane*66+16,16))
    assert values==(20000+lane,9<<8,16384,(127 if cc==128 else 11)<<8,3<<8,16384,0,28000),values
 print('ok :128 CC + OFF, douze réglages séparés, enums natifs et cible fictive privée')
 # Échec sans aucune écriture, même pour un réglage invalide de la dernière voie.
 r.uc.mem_write(cfg+5*32+14,struct.pack('>H',65535));before=bytes(r.uc.mem_read(frame,476))
 assert call('mlcc_frame_prepare',cfg,frame,0)==0 and bytes(r.uc.mem_read(frame,476))==before
 assert call('mlcc_cfg_edit',cfg,5,0,7,28000)==1
 for src,dst,lfo in ((0,frame,0),(cfg,0,0),(cfg+1,frame,0),(cfg,cfg+4,0),(cfg,frame,2)):
  assert call('mlcc_frame_prepare',src,dst,lfo)==0
 r.uc.reg_write(mk.UC_M68K_REG_SR,0x2400)
 assert call('mlcc_frame_prepare',cfg,frame,0)==0
 r.uc.reg_write(mk.UC_M68K_REG_SR,0x2000)
 print('ok : champs invalides, chevauchement, pointeurs et IRQ refusés avant écriture')
 audio_frame=b'\xa5'*476;audio_state=b'\x5a'*192
 r.uc.mem_write(OBJ,audio_frame);r.uc.mem_write(LFO_PHASE,audio_state)
 r.uc.mem_write(pattern,bytes(1584));r.uc.mem_write(q,bytes(148))
 for lane in range(6):r.uc.mem_write(pattern+264*lane,bytes((1,0,6+lane,4)))
 for lfo in range(2):
  for cc in (0,1,7,74,127,128):
   for lane in range(6):assert call('mlcc_cfg_edit',cfg,lane,lfo,3,cc)==1
   r.uc.mem_write(state,bytes(192));seen=[set() for _ in range(6)]
   assert call('mlcc_frame_prepare',cfg,frame,lfo)==1
   for tick in range(64):
    r.uc.reg_write(mk.UC_M68K_REG_SR,0x2500)
    assert call('mlcc_frame_reset',frame)==1
    assert r.uc.reg_read(mk.UC_M68K_REG_SR)&0x700==0x500
    r.uc.reg_write(mk.UC_M68K_REG_SR,0x2000)
    frame_before=bytes(r.uc.mem_read(frame,476))
    r.call(native.ENTRY,frame,14400,0,state)
    after=bytes(r.uc.mem_read(frame,476))
    allowed={lane*66+36+i for lane in range(6) for i in range(2)}
    assert all(x==y or off in allowed for off,(x,y) in enumerate(zip(frame_before,after)))
    for lane in range(6):
     value=call('mlcc_value',state,lane)
     if cc==128:assert value==0xffffffff
     else:
      assert 0<=value<=127,(cc,lane,value,r.r32(state+lane*32+16))
      assert value==r.r16(frame+lane*66+36)//256
      seen[lane].add(value)
      assert call('mlcc_lane_put',q,pattern,lane,lfo,cc,value)==1
    while (packet:=call('mlcc_take',q)):
     status,c,v,port=packet.to_bytes(4,'big')
     assert 0xb6<=status<=0xbb and c==cc and v<=127 and port==4
   if cc!=128:assert all(len(x)>1 for x in seen),seen
   assert bytes(r.uc.mem_read(OBJ,476))==audio_frame
   assert bytes(r.uc.mem_read(LFO_PHASE,192))==audio_state
 print('ok : moteur LFO natif -> valeur CC -> file privée, CC0/1/7/74/127/OFF, deux LFO et six canaux')
 print('ok : phases et paramètres audio inchangés ; seules six cibles fictives modifiées, valeurs MIDI bornées')
 for delta in (-2147483648,-16385,-16384,0,16128,16129,2147483647):
  r.w32(state+16,11);r.w32(state+20,delta)
  assert call('mlcc_value',state,0)==max(0,min(127,(16384+delta)//256))
 print('ok : saturation signée sans overflow, centre64 et plage0..127')
 assert not r.bad
 print('Limite : menus, cadence audio/limitation débit et publication firmware restent à raccorder')
if __name__=='__main__':main()
