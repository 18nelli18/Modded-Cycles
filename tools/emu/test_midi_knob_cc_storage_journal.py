#!/usr/bin/env python3
"""Journal MCC1 A/B ColdFire : Save répété, sélection, corruption, isolation."""
import argparse,pathlib,tempfile,subprocess,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 names=('knob_cc_storage_codec','storage_codec','knob_cc_storage_journal','knob_cc_storage_path','storage_path','knob_cc_storage_prepare','knob_cc_storage_project','knob_cc_storage_restore')
 defs={name:0x9305e000+4*i for i,name in enumerate(('ml_store_presence','ml_store_read_checked','mlkcs_verified','ml_store_io_begin','ml_store_io_end','mlkc_locks_for','mlkc_locks_adopt'))}
 defs['mlkc_state']=0x9305f000
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);objs=[]
  for name in names:
   obj=p/(name+'.o');objs.append(str(obj));subprocess.run([cross+'as','-march=cfv4e','-o',str(obj),str(root/'tools/machines/midi_lanes'/(name+'.s'))],check=True)
  subprocess.run([cross+'ld','-Ttext=0x93050000',*['--defsym='+k+'='+hex(v) for k,v in defs.items()],'-e','mlkcs_save','-o',str(p/'a.elf'),*objs],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'a.elf'),str(p/'a.bin')],check=True);code=(p/'a.bin').read_bytes();syms=symbols(cross,p/'a.elf')
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
 # Trois CRC complets de locks dépassent le budget des petites fixtures UI.
 def call(name,*args):
  r.u.mem_write(STACK,struct.pack('>'+'I'*(len(args)+1),STOP,*args));r.u.reg_write(mk.UC_M68K_REG_A7,STACK)
  r.u.emu_start(r.s[name],STOP,count=3000000)
  assert r.u.reg_read(mk.UC_M68K_REG_PC)==STOP,name
  assert r.u.reg_read(mk.UC_M68K_REG_A7)==STACK+4,name
  return r.u.reg_read(mk.UC_M68K_REG_D0)
 r.call=call
 prepared=r.call('mlkcs_prepare');assert prepared and r.call('mlkcs_prepare')==prepared
 assert r.call('mlkcs_bind',prepared,0x12345678,9,96)==1
 assert r.string(r.r32(prepared))=='/ModdedCycles/09-12345678/CCM-00-A'
 assert r.string(r.r32(prepared+4))=='/ModdedCycles/09-12345678/CCM-00-B'
 assert [r.r32(prepared+i) for i in (8,12,16,20)]==[prepared+120+i*9248 for i in range(4)]
 for ident,slot,pattern in ((0,9,96),(1,96,0),(1,9,97)):
  before=bytes(r.u.mem_read(prepared,120));assert r.call('mlkcs_bind',prepared,ident,slot,pattern)==0
  assert bytes(r.u.mem_read(prepared,120))==before
 ctx,pa,pb,ra,rb,scratch,payload=0x93060000,0x93060100,0x93060140,0x93064000,0x93068000,0x9306c000,0x93070000
 files={};state={'write':1};writes=[]
 def presence(args):return int(any(r.string(r.r32(args[0]+offset)) in files for offset in (0,4)))
 def read(args):
  path,buf,n=args[:3];data=files.get(r.string(path))
  if data is None:return 0
  assert len(data)==n;r.u.mem_write(buf,data);return 1
 def verified(args):
  path,buf,tmp,n=args[:4];assert tmp!=buf
  if not state['write']:return 0
  data=bytes(r.u.mem_read(buf,n));files[r.string(path)]=data;r.u.mem_write(tmp,data);writes.append(r.string(path));return 1
 lookup={};adopted={}
 def adopt(args):adopted[args[0]]=args[1];return 1
 for name,fn in (('mlkc_locks_adopt',adopt),('mlkc_locks_for',lambda args:lookup.get(args[0],0)),('ml_store_presence',presence),('ml_store_read_checked',read),('mlkcs_verified',verified),('ml_store_io_begin',lambda args:1),('ml_store_io_end',lambda args:1)):
  addr=defs[name];r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 for pattern,size in ((96,144),(0,9216),(95,9216)):
  files.clear();writes.clear()
  for copy,out in enumerate((pa,pb)):
   assert r.call('mlkcs_path',out,35,0x12345678,pattern,copy,9)==1
   assert r.string(out)==('/ModdedCycles/09-12345678/%s-%02d-%s'%('CCM' if pattern==96 else 'CCL',0 if pattern==96 else pattern,'AB'[copy]))
  r.u.mem_write(ctx,struct.pack('>12I',pa,pb,ra,rb,scratch,payload,9,pattern,12,pa+26,pb+26,0x12345678))
  data=bytearray(bytes((255,64))*72 if size==144 else b'\xff'*size);data[:2]=bytes((74,64));r.u.mem_write(payload,bytes(data))
  assert r.call('mlkcs_load',ctx)==3
  assert r.call('mlkcs_save',ctx)==1 and writes==[r.string(pa)]
  assert r.call('mlkcs_load',ctx)==1 and bytes(r.u.mem_read(scratch,size))==data
  data[1]=100;r.u.mem_write(payload,bytes(data))
  assert r.call('mlkcs_save',ctx)==1 and writes[-1]==r.string(pb)
  assert r.call('mlkcs_load',ctx)==2 and bytes(r.u.mem_read(scratch,size))==data
  data[1]=50;r.u.mem_write(payload,bytes(data));assert r.call('mlkcs_save',ctx)==1 and writes[-1]==r.string(pa)
  assert r.call('mlkcs_load',ctx)==1 and bytes(r.u.mem_read(scratch,size))==data
  good=files[r.string(pa)];broken=bytearray(good);broken[-1]^=1;files[r.string(pa)]=bytes(broken)
  assert r.call('mlkcs_load',ctx)==2
  count=len(writes);state['write']=0;assert r.call('mlkcs_save',ctx)==0 and len(writes)==count;state['write']=1
  files[r.string(pb)]=bytes(broken);assert r.call('mlkcs_load',ctx)==0
  assert r.call('mlkcs_save',ctx)==0 and len(writes)==count
 # Pipeline projet : maps globales + seulement les patterns avec locks.
 files.clear();writes.clear();state['write']=1
 table,bank,lockbuf=0x93074000,0x93075000,0x93078000
 r.u.mem_write(table,bytes(384));r.w32(table,bank);r.w32(table+12,bank+264)
 maps=bytes((74,64))*72;locks=bytes((74,100))+b'\xff'*9214
 r.u.mem_write(defs['mlkc_state'],maps);r.u.mem_write(lockbuf,locks);lookup[bank]=lockbuf
 assert r.call('mlkcs_save_project',0x12345678,9,table)==1
 assert set(files)=={'/ModdedCycles/09-12345678/CCM-00-A','/ModdedCycles/09-12345678/CCL-00-A'}
 assert files['/ModdedCycles/09-12345678/CCM-00-A'][32:]==maps
 assert files['/ModdedCycles/09-12345678/CCL-00-A'][32:]==locks
 assert r.call('mlkcs_save_project',0x12345678,9,table)==1
 assert '/ModdedCycles/09-12345678/CCM-00-B' in files and '/ModdedCycles/09-12345678/CCL-00-B' in files
 state['write']=0;assert r.call('mlkcs_save_project',0x12345678,9,table)==0 and r.r32(syms['mlkcs_save_error'])==1
 # Candidats privés au chargement : aucune modification du CC actif avant apply.
 state['write']=1;r.call('mlkcs_candidate_reset');adopted.clear()
 r.u.mem_write(defs['mlkc_state'],b'\xee'*144)
 r.call('mlkcs_candidate_step',bank,0,0x12345678,9)
 assert bytes(r.u.mem_read(defs['mlkc_state'],144))==b'\xee'*144 and not adopted
 r.call('mlkcs_candidate_step',bank+264,3,0x12345678,9)
 r.call('mlkcs_candidate_apply',table)
 assert bytes(r.u.mem_read(defs['mlkc_state'],144))==maps
 assert set(adopted)=={bank} and bytes(r.u.mem_read(adopted[bank],9216))==locks
 assert r.r32(syms['mlkcs_load_error'])==0
 # Ancien projet sans fichiers CC : defaults OFF, aucun lock, notes inchangées.
 files.clear();r.call('mlkcs_candidate_reset');adopted.clear()
 r.call('mlkcs_candidate_step',bank,0,0x12345678,9);r.call('mlkcs_candidate_apply',table)
 assert bytes(r.u.mem_read(defs['mlkc_state'],144))==bytes((255,64))*72 and not adopted
 print('ok : restauration CC privée puis adoption après publication MIDI ; projet ancien sans CC=OFF/locks vides')
 print('ok : pipeline Save CC projet maps+locks présents, copiesA/B successives, erreur CC distincte')
 print('ok : namespaces CCM/CCL isolés, première création, SaveA/B/A, génération et récupération copie corrompue')
 print('ok : deux copies invalides refusées sans écriture, échec writer propagé ; notes MBK4 jamais touchées')
 print('Limite : journal isolé avec backend simulé ; hooks Save/Load et allocation firmware à raccorder')
if __name__=='__main__':main()
