#!/usr/bin/env python3
"""Prototype CC ColdFire : plage complète, coalescence, équité et exclusion IRQ."""
import argparse,pathlib,subprocess,tempfile
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}})
 with tempfile.TemporaryDirectory() as t:
  p=pathlib.Path(t)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'q.o'),str(root/'tools/machines/midi_lanes/lfo_cc_queue.s')],check=True)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'s.o'),str(root/'tools/machines/midi_lanes/lfo_cc_service.s')],check=True)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'n.o'),str(root/'tools/machines/midi_lanes/lfo_cc_names.s')],check=True)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'l.o'),str(root/'tools/machines/midi_lanes/lfo_cc_lane.s')],check=True)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'c.o'),str(root/'tools/machines/midi_lanes/lfo_cc_settings.s')],check=True)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'rate.o'),str(root/'tools/machines/midi_lanes/lfo_cc_rate.s')],check=True)
  subprocess.run([cross+'ld','-Ttext=0x930e0000','-e','mlcc_put','-o',str(p/'q.elf'),str(p/'q.o'),str(p/'s.o'),str(p/'n.o'),str(p/'l.o'),str(p/'c.o'),str(p/'rate.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'q.elf'),str(p/'q.bin')],check=True)
  r.u.mem_write(0x930e0000,(p/'q.bin').read_bytes());r.s=symbols(cross,p/'q.elf')
 cfg=0x93060000
 assert r.call('mlcc_cfg_init',cfg)==1
 maxima=(32767,23,32767,128,6,32767,4,32767)
 for lane in range(6):
  for lfo in range(2):
   assert r.call('mlcc_cfg_get',cfg,lane,lfo,3)==128
   assert r.call('mlcc_cfg_get',cfg,lane,lfo,7)==16384
   for field,maximum in enumerate(maxima):
    for value in (0,maximum):
     before=bytearray(r.u.mem_read(cfg,192))
     assert r.call('mlcc_cfg_edit',cfg,lane,lfo,field,value)==1
     before[lane*32+lfo*16+field*2:lane*32+lfo*16+field*2+2]=value.to_bytes(2,'big')
     assert bytes(r.u.mem_read(cfg,192))==bytes(before)
     assert r.call('mlcc_cfg_get',cfg,lane,lfo,field)==value
    assert r.call('mlcc_cfg_edit',cfg,lane,lfo,field,maximum+1)==0
 assert r.call('mlcc_cfg_edit',cfg,6,0,3,1)==0
 assert r.call('mlcc_cfg_get',cfg,0,2,3)==0xffffffff
 print('ok : douze réglages LFO MIDI privés, huit champs bornés, OFF128 et aucune donnée audio')
 for cc in range(128):
  ptr=r.call('mlcc_name',cc);text=bytes(r.u.mem_read(ptr,24)).split(b'\0')[0].decode()
  assert text.split()[0]=='CC'+str(cc),(cc,text)
 for cc,label in ((1,'CC1 Mod'),(7,'CC7 Volume'),(74,'CC74 Cutoff'),(127,'CC127'),(128,'OFF'),(129,'ERR'),(0xffffffff,'ERR')):
  ptr=r.call('mlcc_name',cc);assert bytes(r.u.mem_read(ptr,24)).split(b'\0')[0].decode()==label
 print('ok : destinations CC0–127, noms usuels, OFF128 distinct du CC127')
 ctx=0x93070000
 def reset():r.u.mem_write(ctx,bytes(148));r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
 reset()
 for cc in range(128):
  for value in (0,64,127):
   assert r.call('mlcc_put',ctx,0,6,cc,value,4)==1
   assert r.call('mlcc_take',ctx)==int.from_bytes(bytes((0xb6,cc,value,4)),'big')
   assert r.call('mlcc_put',ctx,0,6,cc,value,4)==1
   assert r.call('mlcc_take',ctx)==0
 reset()
 for slot in range(12):
  for value in range(128):assert r.call('mlcc_put',ctx,slot,6+slot//2,74,value,4)==1
 for slot in range(12):
  assert r.call('mlcc_take',ctx)==int.from_bytes(bytes((0xb6+slot//2,74,127,4)),'big')
 assert r.call('mlcc_take',ctx)==0
 # Revenir à la dernière valeur retirée annule la valeur intermédiaire.
 assert r.call('mlcc_put',ctx,0,6,74,50,4)==1
 assert r.call('mlcc_put',ctx,0,6,74,127,4)==1
 assert r.call('mlcc_take',ctx)==0
 for ipl in range(1,8):
  reset();sr=0x2000|(ipl<<8);r.u.reg_write(mk.UC_M68K_REG_SR,sr)
  assert r.call('mlcc_put',ctx,11,11,127,127,2)==1
  assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x2700==sr
  before=bytes(r.u.mem_read(ctx,148));assert r.call('mlcc_take',ctx)==0
  assert bytes(r.u.mem_read(ctx,148))==before
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
  assert r.call('mlcc_take',ctx)==0xbb7f7f02
 reset();before=bytes(r.u.mem_read(ctx,148))
 for args in ((0,0,6,1,1,4),(ctx+1,0,6,1,1,4),(ctx,12,6,1,1,4),(ctx,0,16,1,1,4),(ctx,0,6,128,1,4),(ctx,0,6,1,128,4),(ctx,0,6,1,1,1),(ctx,0,6,1,1,5)):
  assert r.call('mlcc_put',*args)==0
  assert bytes(r.u.mem_read(ctx,148))==before
 # Les canaux édités et ports de chaque voie alimentent le paquet CC.
 pattern=0x93080000
 for lane in range(6):
  for lfo in range(2):
   for channel in (0,6+lane,15):
    reset();r.u.mem_write(pattern,bytes(1584))
    r.u.mem_write(pattern+264*lane,bytes((1,0,channel,2+lane%3)))
    assert r.call('mlcc_lane_put',ctx,pattern,lane,lfo,74,99)==1
    assert r.call('mlcc_take',ctx)==int.from_bytes(bytes((0xb0+channel,74,99,2+lane%3)),'big')
    r.u.mem_write(pattern+264*lane+1,b'\x01')
    assert r.call('mlcc_lane_put',ctx,pattern,lane,lfo,74,100)==0
    assert r.call('mlcc_take',ctx)==0
 print('ok : deux LFO × six voies, canal éditable/port propre, mute sans nouvel envoi CC')
 # Une purge retire seulement les deux LFO de la voie et permet la reprise.
 reset()
 for lane in range(6):
  for lfo in range(2):assert r.call('mlcc_put',ctx,lane*2+lfo,lane+6,74,50,4)==1
 for ipl in range(8):
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2000|(ipl<<8))
  assert r.call('mlcc_lane_cancel',ctx,2)==1
  assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x2700==0x2000|(ipl<<8)
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
 packets=[]
 while (packet:=r.call('mlcc_take',ctx)):packets.append(packet)
 assert len(packets)==10 and all(packet>>24!=0xb8 for packet in packets)
 assert r.call('mlcc_put',ctx,4,8,74,50,4)==1
 assert r.call('mlcc_take',ctx)==0xb84a3204
 before=bytes(r.u.mem_read(ctx,148))
 for c,lane in ((0,2),(ctx+1,2),(ctx,6),(ctx,0xffffffff)):
  assert r.call('mlcc_lane_cancel',c,lane)==0
  assert bytes(r.u.mem_read(ctx,148))==before
 print('ok : purge CC des deux LFO par voie, autres voies conservées, reprise et SR')
 reset();sent=[]
 def send(a):
  assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x700==0
  sent.append((bytes(r.u.mem_read(a[1],a[0])),a[2]));return 0
 r.stubs[0x400826b0]=send;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400826b0,end=0x400826b0)
 for slot in range(12):assert r.call('mlcc_put',ctx,slot,6+slot//2,slot,64,4)==1
 before=bytes(r.u.mem_read(ctx,148));r.w32(0x40fe4228,0)
 assert r.call('mlcc_service',ctx,99)==0 and not sent and bytes(r.u.mem_read(ctx,148))==before
 r.w32(0x40fe4228,1);r.u.reg_write(mk.UC_M68K_REG_SR,0x2500)
 assert r.call('mlcc_service',ctx,99)==0 and not sent and bytes(r.u.mem_read(ctx,148))==before
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
 assert r.call('mlcc_service',ctx,0)==0 and not sent
 assert r.call('mlcc_service',ctx,99)==8 and len(sent)==8
 assert r.call('mlcc_service',ctx,8)==4 and len(sent)==12
 assert sent==[(bytes((0xb6+i//2,i,64)),4) for i in range(12)]
 print('ok : service CC borné8, ABI routeur MIDI, pas de retrait hors IPL0 ou routeur absent')
 print('ok : CC0–127, valeurs0–127, 12 sources indépendantes, canaux7–12 et coalescence')
 print('ok : ordre équitable, suppression doublons, publication IRQ et consommation IPL0 uniquement')
 rate=0x93065000;reset();r.u.mem_write(rate,bytes(4));sent.clear();counts=[0]*12
 for block in range(1500):
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2500)
  for slot in range(12):assert r.call('mlcc_put',ctx,slot,6+slot//2,slot,block%128,4)==1
  assert r.call('mlcc_rate_tick',rate)==1
  assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x2700==0x2500
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
  result=r.call('mlcc_rate_service',ctx,rate)
  assert result==int((block+1)%6==0)
  assert r.call('mlcc_rate_service',ctx,rate)==0
 assert len(sent)==250
 for packet,port in sent:counts[packet[1]]+=1
 assert max(counts)-min(counts)<=1 and min(counts)>=20,counts
 before=bytes(r.u.mem_read(ctx,148));r.u.mem_write(rate,(6).to_bytes(4,'big'))
 for ipl in range(1,8):
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2000|(ipl<<8))
  assert r.call('mlcc_rate_service',ctx,rate)==0
  assert bytes(r.u.mem_read(ctx,148))==before and r.r32(rate)==6
 print('ok :1500 blocs simulés ->250 CC maximum, douze sources équitables et aucun retrait IRQ')
 print('Limite : prototype isolé ; aucun menu, oscillateur ou writer physique raccordé')
if __name__=='__main__':main()
