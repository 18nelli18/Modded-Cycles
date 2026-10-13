#!/usr/bin/env python3
"""Chaîne complète sidecar compilée, backend FS simulé, sans matériel."""
import argparse,pathlib,subprocess,tempfile,struct,json
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig,OBJ,RAW,STACK,STOP
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--cc-storage',action='store_true');ap.add_argument('--extended',action='store_true');ap.add_argument('--working',action='store_true');ap.add_argument('--write-first',action='store_true');ap.add_argument('--restore-saved',action='store_true');ap.add_argument('--tweak');ap.add_argument('--audio-lfo',action='store_true');ap.add_argument('--live-record',action='store_true');a=ap.parse_args();data_size=4992 if a.audio_lfo else (4896 if a.extended else 1584)
 if a.audio_lfo:assert a.extended and a.tweak
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);objs=[]
  for name in ('presence','working_slot','ui_cancel','service','retire','prepare','publish','load_hook','restore_step','restore','project','save_hook','session','directory','initial','guard','checked','codec','verify','io','path','snapshot','load','commit'):
   obj=p/(name+'.o');objs.append(str(obj));subprocess.run([cross+'as','-march=cfv4e',*(['--defsym','ML_STORAGE2=1'] if a.extended else []),*(['--defsym','ML_WORKING=1'] if a.working else []),*(['--defsym','ML_SAVE_FIRST=1'] if a.write_first else []),*(['--defsym','ML_RESTORE_SAVED=1'] if a.restore_saved else []),*(['--defsym','ML_STORAGE=1'] if name=='project' else []),*(['--defsym','ML_GENIE=1','--defsym','ML_CLIPBOARD=1'] if name=='ui_cancel' else []),'-o',str(obj),str(root/'tools/machines/midi_lanes'/('storage_'+name+'.s'))],check=True)
  for name in ('banks','runtime'):
   obj=p/(name+'.o');objs.append(str(obj));subprocess.run([cross+'as','-march=cfv4e',*(['--defsym','ML_STORAGE2=1'] if a.extended else []),'-o',str(obj),str(root/'tools/machines/midi_lanes'/(name+'.s'))],check=True)
  (p/'link.ld').write_text('SECTIONS { .text 0x93050000 : { *(.text*) *(.rodata*) *(.data*) } } ml_runtime = 0x93079008; ml_clock_state = 0x9307900c; ml_pattern = 0x93079014; ml_context = 0x93079024; mlp_keyboard_cancel = 0x93079028; mlp_held = 0x9307902c; mlp_remove = 0x93079030; mlp_changed = 0x93079034; ml_gq_state = 0x93079038; ml_gu_valid = 0x9307903c; SG_undo_valid = 0x93079040; mlp_clip_invalidate = 0x93079044; ml_store_save_feedback = 0x93079048; ml_store_load_feedback = 0x9307904c; ml_store_save_error = 0x93079050;')
  subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','ml_store_session_save','-o',str(p/'e.elf'),*objs],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'e.elf'),str(p/'e.bin')],check=True);code=(p/'e.bin').read_bytes();syms=symbols(cross,p/'e.elf')
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;fixture_syms=dict(syms);r.u.mem_write(0x93050000,code)
 r.u.mem_write(0x93079048,b'\x4e\x75');r.u.mem_write(0x9307904c,b'\x4e\x75')
 if a.tweak:
  tweak=json.loads(pathlib.Path(a.tweak).read_text())
  syms={k:int(v,16) for k,v in tweak['symbols'].items()};r.s=syms
  for part in tweak['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
  # Fragments propres dans les masques libérés ; laisser les hooks natifs
  # aux vérifications ABI ci-dessous, qui les installent explicitement.
  for w in tweak['writes']:
   at=0x40000400+w['off']
   if 0x40100000<=at<0x401ab750:r.u.mem_write(at,bytes.fromhex(w['new']))
 if a.audio_lfo:r.w32(syms['LF2_context'],0) # fixture sans le tweak LFO2 natif
 if a.extended:
  def extended_call(name,*args):
   fn=r.s[name] if isinstance(name,str) else name
   r.u.mem_write(STACK,struct.pack('>'+'I'*(len(args)+1),STOP,*args));r.u.reg_write(mk.UC_M68K_REG_A7,STACK)
   r.u.emu_start(fn,STOP,count=12000000)
   assert r.u.reg_read(mk.UC_M68K_REG_PC)==STOP,name
   assert r.u.reg_read(mk.UC_M68K_REG_A7)==STACK+4,name
   return r.u.reg_read(mk.UC_M68K_REG_D0)
  r.call=extended_call
 feedback=[]
 if a.tweak:
  addr=syms['TG_show_popup']
  def popup(args):
   assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x700==0
   feedback.append(r.string(args[0]));return 0
  r.stubs[addr]=popup;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 if a.tweak:
  expected=['MIDI SAVE ERR','MIDI: IRQ','MIDI: LOADING','CTX: NO LOAD','MIDI: OWNER','MIDI: SYNC','MIDI: BANK','MIDI: SLOT','MIDI: PATH','MIDI: ROOT','MIDI: DIR','MIDI: SNAP','MIDI: COMMIT','MIDI: CREATE','MIDI: DATA','MIDI: OPEN','MIDI: ALLOC','WRITE: ZERO','MIDI: FLUSH','MIDI: CLOSE','MIDI: BUFFERS','MIDI: LOOKUP A','MIDI: LOOKUP B','MIDI: GUARD','MIDI: RAM ONLY','MIDI: VERIFY']
  r.w32(syms['ml_store_save_status'],0);r.w32(syms['ml_store_io_poison'],0)
  for error,message in enumerate(expected):
   r.w32(syms['ml_store_save_error'],error);r.call('ml_store_save_feedback');assert feedback[-1]==message
  r.w32(syms['ml_store_save_error'],3)
  r.w32(syms['ml_store_load_serial'],1)
  for seen,ready,error,busy,message in ((0,0,0,0,'CTX: NO UI'),(1,0,0,0,'CTX: UI IPL'),(1,1,0,1,'CTX: BUSY'),(1,1,1,0,'CTX: RAM'),(1,1,0,0,'CTX: STATE')):
   for symbol,v in (('ml_store_ui_seen',seen),('ml_store_ui_ready',ready),('ml_store_load_error',error),('ml_store_io_busy',busy)):r.w32(syms[symbol],v)
   r.call('ml_store_save_feedback');assert feedback[-1]==message
  for symbol in ('ml_store_load_serial','ml_store_ui_seen','ml_store_ui_ready','ml_store_load_error','ml_store_io_busy'):r.w32(syms[symbol],0)
  r.w32(syms['ml_store_io_poison'],1);r.call('ml_store_save_feedback');assert feedback[-1]=='MIDI: DISK'
  r.w32(syms['ml_store_io_poison'],0);r.w32(syms['ml_store_save_error'],0)
 ctx,pathA,pathB,recA,recB,scratch,snapshot,bank=[0x93090000+i*0x2000 for i in range(8)]
 r.u.mem_write(ctx,struct.pack('>11I',pathA,pathB,recA,recB,scratch,snapshot,0,0,0,0,0))
 dirs={'/':2};files={};handles={};positions={};log=[];fault={'write':False,'read':False,'verify':False}
 def lookup(args):
  parent,name,out=args[:3];name=r.string(name);prefix=next(k for k,v in dirs.items() if v==parent)
  path=prefix.rstrip('/')+'/'+name;log.append(('lookup',path))
  if path in dirs:r.u.mem_write(out,struct.pack('>IH',dirs[path],1));return 1
  if path in files:r.u.mem_write(out,struct.pack('>IH',1000,2));return 1
  return 0
 def mkdir(args):
  path=r.string(args[0]);log.append(('mkdir',path));assert path not in dirs and path not in files
  dirs[path]=2+len(dirs);return 0
 def opened(args):
  path,mode,handle=r.string(args[0]),r.string(args[1]),args[2]
  log.append(('open',path,mode))
  if mode=='r' and path not in files:return -1
  if mode=='w':files[path]=b''
  handles[handle]=path;positions[handle]=0;return 0
 def read(args):
  out,size,handle=args[:3];data=files[handles[handle]]
  if fault['read']:r.w32(syms['ml_store_io_poison'],1)
  r.u.mem_write(out,data[:size]);return min(size,len(data))
 def write(args):
  source,size,handle=args[:3]
  if fault['write']:return 0
  at=positions[handle];data=bytes(r.u.mem_read(source,size));old=files[handles[handle]]
  files[handles[handle]]=old[:at]+data+old[at+size:];positions[handle]=at+size
  if fault['verify']:files[handles[handle]]=files[handles[handle]][:-1]
  return size
 for addr,fn in ((0x4007ad86,lookup),(0x4007ac46,mkdir),(0x4007bc5e,opened),
                 (0x4007baaa,read),(0x4007bb0a,write),(0x4007bc1c,lambda a:0),
                 (0x4007bb76,lambda a:0),(0x4007e2f6,lambda a:0)):
  r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 def payload(note):
  data=bytearray(1584)
  for lane in range(6):
   off=lane*264;data[off:off+8]=bytes((1,0,6+lane,2,16,0,0,0))
   for step in range(64):data[off+8+step*4:off+12+step*4]=bytes((note,100,1,1))
  
  if a.extended:
   data.extend(bytes((0,8,0,0,5,1,0,0))*390)
   data.extend(struct.pack('>8H',16384,9,16384,128,0,0,0,16384)*12)
  if a.audio_lfo:data.extend(struct.pack('>8H',16384,9<<8,16384,127<<8,0,0,0,16384)*6)
  return bytes(data)
 def save(id,slot,pat,note):
  r.u.mem_write(bank,payload(note));return r.call('ml_store_session_save',ctx,id,slot,pat,bank)
 def load(id,slot,pat):
  return r.call('ml_store_session_load',ctx,id,slot,pat)
 if a.extended:
  assert load(0x12345678,3,5)==3 and dirs=={'/':2} and not files
  assert not any(entry[0]=='open' for entry in log)
  assert r.r32(syms['ml_store_read_error'])==0
 if a.audio_lfo:
  r.u.mem_write(bank,payload(67))
  assert r.call(fixture_syms['ml_record_encode'] if a.working else 'ml_record_encode_v2',recA,4928,bank,3,4,7)==1
  dirs['/ModdedCycles']=3;dirs['/ModdedCycles/03-12345678']=4
  legacy='/ModdedCycles/03-12345678/SEQ-04-'
  files[legacy+'A']=bytes(r.u.mem_read(recA,4928))
  assert load(0x12345678,3,4)==1
  assert bytes(r.u.mem_read(snapshot,data_size))==payload(67)
  assert save(0x12345678,3,4,68)==1
  assert files[legacy+'B'][:4]==(b'MBK4' if a.live_record else b'MBK3')
  assert load(0x12345678,3,4)==2
  assert bytes(r.u.mem_read(snapshot,data_size))==payload(68)
  print('ok : migration MBK2 -> MBK3 avec LFO2 audio désactivé, génération et copies A/B conservées')
  del files[legacy+'A'];del files[legacy+'B']
 assert save(0x12345678,3,5,60)==1,log
 assert '/ModdedCycles/03-12345678' in dirs
 path='/ModdedCycles/03-12345678/SEQ-05-'
 assert files[path+'A'][:4]==(b'MBK4' if a.live_record else (b'MBK3' if a.audio_lfo else (b'MBK2' if a.extended else b'MBK1'))) and path+'B' not in files
 assert save(0x12345678,3,5,72)==1
 assert struct.unpack('>I',files[path+'B'][20:24])[0]==1
 r.u.mem_write(snapshot,bytes(data_size));assert load(0x12345678,3,5)==2
 assert bytes(r.u.mem_read(snapshot,data_size))==payload(72)
 # Deux patterns et deux identités/slots ne partagent pas les séquences.
 assert save(0x12345678,3,6,64)==1
 assert save(0xabcdef01,3,5,67)==1
 assert save(0x12345678,4,5,69)==1
 for id,slot,pat,note in ((0x12345678,3,5,72),(0x12345678,3,6,64),(0xabcdef01,3,5,67),(0x12345678,4,5,69)):
  assert load(id,slot,pat)>0
  assert bytes(r.u.mem_read(snapshot,data_size))==payload(note)
 # Dernière copie corrompue -> récupération de A ; snapshot musical intact.
 bad=bytearray(files[path+'B']);bad[-1]^=1;files[path+'B']=bytes(bad)
 assert load(0x12345678,3,5)==1 and bytes(r.u.mem_read(snapshot,data_size))==payload(60)
 fault['write']=True;assert save(0x12345678,3,5,80)==0
 if a.extended:assert r.r32(syms['ml_store_save_error'])==17
 fault['write']=False
 assert load(0x12345678,3,5)==1 and bytes(r.u.mem_read(snapshot,data_size))==payload(60)
 if a.extended:
  good_a=files[path+'A'];bad_a=bytearray(good_a);bad_a[-1]^=1
  files[path+'A']=bytes(bad_a);before=bytes(r.u.mem_read(snapshot,data_size))
  assert load(0x12345678,3,5)==0
  assert r.r32(syms['ml_store_read_error'])==4
  assert bytes(r.u.mem_read(snapshot,data_size))==before
  files[path+'A']=good_a
 # Projet absent : pas de publication ; identité zéro et bornes refusées.
 before=bytes(r.u.mem_read(snapshot,data_size));assert load(99,0,0)==(3 if a.extended else 0)
 assert bytes(r.u.mem_read(snapshot,data_size))==before
 for id,slot,pat in ((0,0,0),(1,96,0),(1,0,96)):
  n=len(log);assert save(id,slot,pat,60)==0 and len(log)==n
 # Vrai Save projet -> hook compilé -> sauvegarde de toutes les banques visitées.
 table=0x9307a000;bank2=0x9307b000;cache=0x9307c000;callback=0x9307d000;serialized=0x41400000
 r.u.mem_write(table,bytes(384));r.w32(table+5*4,bank);r.w32(table+6*4,bank2)
 r.u.mem_write(bank,payload(76));r.u.mem_write(bank2,payload(81))
 r.w32(syms['ml_bank_table'],table);r.w32(syms['ml_store_project_ctx'],ctx)
 r.w32(syms['ml_store_owner_id'],0x12345678);r.w32(RAW+8,0x12345678)
 r.u.mem_write(callback,bytes(16))
 native={'convert':1,'save':1}
 for addr,fn in ((0x400cfdaa,lambda a:cache),(0x4006a216,lambda a:serialized),
                 (0x4005d18a,lambda a:native['convert']),(0x4006a4d6,lambda a:native['save']),
                 (0x400d0aae,lambda a:0),(0x400cf044,lambda a:0)):
  r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 assert bytes(r.u.mem_read(0x4000f850,8)).hex()=='4cd77c1c4fef0034'
 r.u.mem_write(0x4000f850,b'\x4e\xf9'+struct.pack('>I',syms['ml_store_save_hook'])+b'\x4e\x71')
 if a.write_first:
  r.stubs[0x400cf866]=lambda a:OBJ
  r.u.mem_write(0x4000f762,b'\x4e\xf9'+struct.pack('>I',syms['ml_store_save_entry'])+b'\x4e\x71')
 def native_save(slot=3):
  r.u.mem_write(STACK,struct.pack('>4I',STOP,OBJ,slot,callback))
  r.u.reg_write(mk.UC_M68K_REG_A7,STACK)
  try:r.u.emu_start(0x4000f762,STOP,count=12000000)
  except Exception:
   print("Save PC",hex(r.u.reg_read(mk.UC_M68K_REG_PC)),"ctx",hex(r.r32(syms["ml_store_project_ctx"])),"owner",hex(r.r32(syms["ml_store_owner_id"])),"serial",r.r32(syms["ml_store_load_serial"]))
   raise
  assert r.u.reg_read(mk.UC_M68K_REG_PC)==STOP
  assert r.u.reg_read(mk.UC_M68K_REG_A7)==STACK+4
  return r.u.reg_read(mk.UC_M68K_REG_D0)&255
 if a.extended:
  before=dict(files);r.w32(syms['ml_store_project_ctx'],0)
  if a.write_first:r.w32(syms['ml_store_load_serial'],1)
  assert native_save()==1 and files==before
  assert r.r32(syms['ml_store_save_status'])==0 and r.r32(syms['ml_store_save_error'])==3
  if a.tweak:assert feedback[-1]==('CTX: NO UI' if a.write_first else 'CTX: NO LOAD')
  r.w32(syms['ml_store_project_ctx'],ctx)
  if a.write_first:r.w32(syms['ml_store_load_serial'],0)
 assert native_save()==1
 assert r.r32(syms['ml_store_save_status'])==1
 if a.tweak:assert feedback[-1]=='MIDI SAVED'
 if a.cc_storage:
  assert a.tweak and a.extended
  cc_maps=bytearray(bytes((255,64))*72);cc_maps[:4]=bytes((74,77,71,99));r.u.mem_write(syms['mlkc_state'],bytes(cc_maps))
  cc_locks=r.call('mlkc_locks_for',bank,1);assert cc_locks
  assert r.call('mlkc_lock_set',cc_locks,0,3,0,74,111)==1
  assert r.call('mlkc_lock_set',cc_locks,5,63,11,0,0)==1
  assert native_save()==1 and not r.r32(syms['mlkcs_save_error'])
  map_files=[v for k,v in files.items() if '/CCM-' in k];lock_files=[v for k,v in files.items() if '/CCL-05-' in k]
  assert any(v[32:]==bytes(cc_maps) for v in map_files)
  assert any(v[32:]==bytes(r.u.mem_read(cc_locks,9216)) for v in lock_files)
  print('ok : Save natif écrit maps CC144 et locks9216 via writer/readback réels, CC0/valeur0 conservés')
 for pat,note in ((5,76),(6,81)):
  assert load(0x12345678,3,pat)>0 and bytes(r.u.mem_read(snapshot,data_size))==payload(note)
 # Échec Save natif : aucune écriture annexe ; identité étrangère : refus.
 before=dict(files);native['save']=0
 assert native_save()==0 and files==before
 native['save']=1;r.w32(RAW+8,0x87654321)
 assert native_save()==1 and files==before
 assert r.r32(syms['ml_store_save_status'])==0
 if a.tweak:assert feedback[-1]=='MIDI: OWNER'
 if a.extended:assert r.r32(syms['ml_store_save_error'])==4
 r.w32(RAW+8,0x12345678)
 if a.write_first:
  # Save As change l'identité pendant le vrai Save, pas avant son entrée.
  r.stubs[0x400cf866]=lambda a:OBJ
  r.w32(syms['ml_store_load_ready'],1)
  r.stubs[0x4006a4d6]=lambda a:r.w32(RAW+8,0x10203040) or 1
  assert native_save(8)==1 and r.r32(syms['ml_store_save_status'])==1
  assert r.r32(syms['ml_store_load_pending_slot'])==8
  assert r.r32(syms['ml_store_owner_id'])==0x10203040
  assert bytes(r.u.mem_read(bank,data_size))==payload(76)
  for pat,note in ((5,76),(6,81)):
   assert load(0x10203040,8,pat)>0 and bytes(r.u.mem_read(snapshot,data_size))==payload(note)
  assert native_save(8)==1 and r.r32(syms['ml_store_save_status'])==1
  r.stubs[0x4006a4d6]=lambda a:native['save']
  r.w32(RAW+8,0x12345678);r.w32(syms['ml_store_owner_id'],0x12345678)
  r.w32(syms['ml_store_load_pending_id'],0x12345678)
  print('ok : Save As natif conserve banques, écrit sous nouvelle identité et accepte un second Save')
 # Rechargement dans une nouvelle table RAM, indépendante de la table active.
 restored=0x9307e000;r.u.mem_write(restored,bytes(384));active_before=bytes(r.u.mem_read(table,384))
 def restore(id,slot):
  r.u.mem_write(STACK,struct.pack('>5I',STOP,ctx,id,slot,restored))
  r.u.reg_write(mk.UC_M68K_REG_A7,STACK)
  r.u.emu_start(syms['ml_store_project_restore'],STOP,count=18000000)
  assert r.u.reg_read(mk.UC_M68K_REG_PC)==STOP
  return r.u.reg_read(mk.UC_M68K_REG_D0)
 assert restore(0x12345678,3)==1
 for pat,note in ((5,76),(6,81)):
  ptr=r.r32(restored+pat*4);assert ptr and bytes(r.u.mem_read(ptr,data_size))==payload(note)
 assert r.r32(restored+7*4)==0 and bytes(r.u.mem_read(table,384))==active_before
 # Table non vide refusée sans écraser ses pointeurs.
 prior=bytes(r.u.mem_read(restored,384));assert restore(0x12345678,3)==0
 assert bytes(r.u.mem_read(restored,384))==prior
 # Allocation refusée : aucune table partiellement restaurée publiée.
 r.u.mem_write(restored,bytes(384));r.fail_new=r.new_count+1
 assert restore(0x12345678,3)==0 and bytes(r.u.mem_read(restored,384))==bytes(384)
 r.fail_new=0
 # Échec après une première allocation : libérer toute la restauration partielle.
 freed=[];r.stubs[0x400802ec]=lambda a:freed.append(a[0]) or 0
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400802ec,end=0x400802ec)
 r.fail_new=r.new_count+2
 assert restore(0x12345678,3)==0 and bytes(r.u.mem_read(restored,384))==bytes(384)
 assert len(freed)==1 and bytes(r.u.mem_read(table,384))==active_before
 r.fail_new=0
 # Restauration incrémentale : un seul pattern et aucune publication par appel.
 r.u.mem_write(restored,bytes(384))
 def step(index):
  return r.call('ml_store_restore_step',ctx,0x12345678,3,restored,index)
 for index in range(96):
  start=len(log)
  assert step(index)==(2 if index==95 else 1)
  # Les ouvertures ne concernent que les deux copies du pattern demandé.
  for entry in log[start:]:
   if entry[0]=='open':assert '/SEQ-%02d-'%index in entry[1],entry
 for pat,note in ((5,76),(6,81)):
  ptr=r.r32(restored+pat*4);assert ptr and bytes(r.u.mem_read(ptr,data_size))==payload(note)
 assert bytes(r.u.mem_read(table,384))==active_before
 prior=bytes(r.u.mem_read(restored,384))
 assert step(5)==0 and step(96)==0
 assert bytes(r.u.mem_read(restored,384))==prior
 # Un service disque occupé ne doit pas devenir une fausse absence de fichier.
 n=len(log);r.w32(syms['ml_store_io_busy'],1)
 assert step(7)==0 and len(log)==n
 r.w32(syms['ml_store_io_busy'],0)
 assert bytes(r.u.mem_read(restored,384))==prior
 print('ok : restauration incrémentale, un pattern/appel, fin95, aucune publication audio')
 # Publication atomique : identité native et notification toujours actuelles.
 empty=0x9307f000
 for name,value in (('ml_bank_empty',empty),('ml_runtime',0x93080000),('ml_clock_state',0x93081000),('ml_play_pattern',bank),('ml_pattern',bank)):
  r.w32(syms[name],value)
 current={'id':0x12345678};activations=[]
 def activate(args):
  assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x700==0x700
  assert r.r32(syms['ml_bank_table'])==table
  activations.append(tuple(args[:4]));r.w32(args[0],args[3]);return 1
 for addr,fn in ((0x400cf866,lambda a:OBJ),(0x4000eae2,lambda a:current['id']),(syms['ml_bank_activate'],activate)):
  existed=addr in r.stubs
  r.stubs[addr]=fn
  if not existed:
   handle=r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
   if addr==syms['ml_bank_activate']:activation_hook=handle
 r.w32(syms['ml_store_load_pending_id'],0x12345678);r.w32(syms['ml_store_load_serial'],3)
 def publish(serial=3):return r.call('ml_store_publish',restored,0x12345678,serial)
 assert publish(2)==0 and not activations
 current['id']=99;assert publish()==0 and not activations
 current['id']=0x12345678
 assert publish()==table
 assert len(activations)==1 and r.r32(syms['ml_bank_table'])==restored
 assert r.r32(syms['ml_pattern'])==empty and r.r32(syms['ml_play_pattern'])==empty
 assert r.r32(syms['ml_store_owner_id'])==0x12345678
 assert bytes(r.u.mem_read(table,384))==active_before
 assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x700==0
 assert publish()==0 and len(activations)==1
 print('ok : publication sous IPL7, identité/serial obsolètes refusés, ancienne table conservée')
 # Lecture physique en erreur malgré1616 octets reçus -> refus du chargement.
 fault['read']=True;assert load(0x12345678,3,5)==0
 assert r.r32(syms['ml_store_io_busy'])==0
 print('ok : save/load sidecar complet, répertoires, identité/slot/pattern, A/B/CRC, récupération et erreurs')
 print('ok : Save natif -> hook -> toutes banques visitées, aucun sidecar sur échec natif/identité différente')
 print('ok : restauration multi-pattern dans table privée, table active intacte, allocation/alias refusés')
 # Préallocation UI : un échec ne publie aucun contexte ; réessai idempotent.
 r.w32(syms['ml_store_project_ctx'],0);r.fail_new=r.new_count+1
 assert r.call('ml_store_prepare')==0 and r.r32(syms['ml_store_project_ctx'])==0
 r.fail_new=0;assert r.call('ml_store_prepare')==1
 allocated=r.r32(syms['ml_store_project_ctx']);assert allocated
 assert [r.r32(allocated+i*4) for i in range(6)]==[allocated+off for off in (44,80,116,116+data_size+32,116+2*(data_size+32),116+3*(data_size+32))]
 assert bytes(r.u.mem_read(allocated+24,20))==bytes(20)
 assert bytes(r.u.mem_read(allocated+116,4*(data_size+32)))==bytes(4*(data_size+32))
 count=r.new_count;assert r.call('ml_store_prepare')==1 and r.new_count==count
 fault['read']=False;r.w32(syms['ml_store_io_poison'],0)
 r.u.mem_write(bank,payload(84))
 assert r.call('ml_store_session_save',allocated,0x10203040,9,12,bank)==1
 assert r.call('ml_store_session_load',allocated,0x10203040,9,12)>0
 assert bytes(r.u.mem_read(allocated+116+3*(data_size+32),data_size))==payload(84)
 print(f'ok : préallocation UI{116+4*(data_size+32)}, buffers disjoints initialisés, échec/réessai sans fuite')
 # Service UI complet, interruption d'une candidature par un nouveau Load.
 native_context=0x93082000;embedded=native_context+1956;empty=native_context+2340
 r.w32(syms['ml_context'],native_context);r.w32(syms['ml_bank_empty'],empty)
 r.u.mem_write(embedded,bytes(384));r.w32(embedded,native_context)
 r.w32(syms['ml_bank_table'],embedded);r.w32(syms['ml_pattern'],native_context)
 r.w32(syms['ml_play_pattern'],native_context)
 cancelled=[]
 def keyboard_cancel(args):
  assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x700==0
  cancelled.append(True);return 0
 def clip_invalidate(args):
  assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x700==0x700
  return 0
 for name,fn in (('mlp_keyboard_cancel',keyboard_cancel),('mlp_clip_invalidate',clip_invalidate)):
  addr=syms[name];r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 for name in ('mlp_held','mlp_remove','mlp_changed','ml_gq_state','ml_gu_valid','SG_undo_valid'):r.w32(syms[name],1)
 # Exécuter maintenant le vrai runtime/activate compilé, sans stub.
 r.u.hook_del(activation_hook);del r.stubs[syms['ml_bank_activate']]
 runtime=r.r32(syms['ml_runtime']);clock=r.r32(syms['ml_clock_state'])
 r.u.mem_write(runtime,bytes(320));r.u.mem_write(clock,b'\xa5'*52)
 r.w32(runtime,1);r.w32(runtime+8,1);r.w32(runtime+12,1)
 r.w32(runtime+16,0x96486403);r.w32(runtime+272,0x86480003);r.w32(runtime+276,8)
 current['id']=0x12345678
 if a.restore_saved:
  assert a.write_first and a.extended
  if a.audio_lfo:
   # Test FS sans page/LFO natif ; leur sync réel est prouvé par storage_bank.
   at=syms['ml_bank_ui_sync'];r.stubs[at]=lambda args:1
   r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  # Démarrage sans ancien owner/table musical : seules les annexes subsistent.
  r.u.mem_write(0x404e9b4d,b'\x03')
  for addr,fn in ((0x400d0a10,lambda args:0x930a8000),
                  (0x4008c2c2,lambda args:6),(0x4008c324,lambda args:current['id'])):
   r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
  r.w32(syms['ml_store_load_serial'],0);r.w32(syms['ml_store_owner_id'],0)
  r.u.mem_write(bank,bytes(data_size));r.u.mem_write(bank2,bytes(data_size))
  before_files=dict(files)
  for index in range(96):r.call('ml_store_service')
  assert files==before_files and r.r32(syms['ml_store_load_ready'])==1
  assert r.r32(syms['ml_store_load_status'])==1
  table=r.r32(syms['ml_bank_table']);assert table!=embedded
  for pat,note in ((5,76),(6,81)):
   ptr=r.r32(table+pat*4);assert ptr and bytes(r.u.mem_read(ptr,data_size))==payload(note)
  assert r.r32(syms['ml_store_owner_id'])==current['id']
  assert native_save()==1 and r.r32(syms['ml_store_save_status'])==1
  if a.cc_storage:
   assert bytes(r.u.mem_read(syms['mlkc_state'],144))==bytes(cc_maps)
   cc_table=r.r32(syms['ml_bank_table']);cc_bank=r.r32(cc_table+20);cc_restored=r.call('mlkc_locks_for',cc_bank,0);assert cc_restored
   assert r.call('mlkc_lock_get',cc_restored,0,3,0)==(74<<8|111)
   assert r.call('mlkc_lock_get',cc_restored,5,63,11)==0
   print('ok : restauration service boot réelle adopte maps et locks après notes, anciens buffers séparés')
  if a.live_record:
   # Paquet produit par la capture libre : note/vélocité/durée/retard persistants.
   recorded=r.r32(table+5*4)
   r.u.mem_write(recorded+8,bytes((73,91,4,37)))
   assert native_save()==1 and r.r32(syms['ml_store_save_status'])==1
   assert load(current['id'],3,5)>0
   assert bytes(r.u.mem_read(snapshot+8,4))==bytes((73,91,4,37))
   r.w32(syms['ml_store_load_pending_id'],current['id'])
   r.w32(syms['ml_store_load_pending_slot'],3)
   r.w32(syms['ml_store_load_serial'],r.r32(syms['ml_store_load_serial'])+1)
   for index in range(96):r.call('ml_store_service')
   table=r.r32(syms['ml_bank_table']);recorded=r.r32(table+5*4)
   assert bytes(r.u.mem_read(recorded+8,4))==bytes((73,91,4,37))
   print('ok : live libre sauvegarde/restaure note73, vélocité91, durée4, retard9/64 dans MBK4')
   before_files=dict(files)
  # Changer de projet ne doit pas recopier les séquences de l'ancien.
  current['id']=0x55667788;r.w32(RAW+8,current['id'])
  r.w32(syms['ml_store_load_pending_id'],current['id'])
  r.w32(syms['ml_store_load_pending_slot'],4)
  r.w32(syms['ml_store_load_serial'],r.r32(syms['ml_store_load_serial'])+1)
  for index in range(96):r.call('ml_store_service')
  assert bytes(r.u.mem_read(r.r32(syms['ml_bank_table']),384))==bytes(384)
  assert files==before_files or all(k in files for k in before_files)
  # Slot introuvable après Load : B reste jouable, Save protégé, notes intactes.
  r.w32(syms['ml_store_load_pending_slot'],96)
  r.u.mem_write(0x404e9b4d,b'\xff')
  r.w32(syms['ml_store_load_ready'],0)
  r.w32(syms['ml_store_load_serial'],r.r32(syms['ml_store_load_serial'])+1)
  kept=r.r32(syms['ml_bank_table']);r.w32(kept+5*4,bank)
  r.u.mem_write(bank,payload(89));before_failed=dict(files)
  r.call('ml_store_service')
  assert r.r32(syms['ml_store_load_ready'])==1
  assert r.r32(syms['ml_store_ram_only'])==1
  assert r.r32(syms['ml_bank_table'])==kept and bytes(r.u.mem_read(bank,data_size))==payload(89)
  assert native_save()==1 and r.r32(syms['ml_store_save_status'])==0
  assert r.r32(syms['ml_store_save_error'])==24 and files==before_failed
  current['id']=0x66778899;r.w32(RAW+8,current['id'])
  r.w32(syms['ml_store_load_pending_id'],current['id']);r.w32(syms['ml_store_load_ready'],0)
  r.w32(syms['ml_store_load_serial'],r.r32(syms['ml_store_load_serial'])+1)
  r.call('ml_store_service')
  assert r.r32(syms['ml_store_load_ready'])==1 and r.r32(syms['ml_store_ram_only'])==1
  assert bytes(r.u.mem_read(r.r32(syms['ml_bank_table']),384))==bytes(384)
  assert files==before_failed
  print('ok : association slot refusée conserve accès B et notes du même projet ; nouveau projet RAM vide, Save bloqué')
  print('ok : démarrage sans données MIDI RAM restaure les patterns 5/6 depuis fichiers puis Save fonctionne')
  print('ok : autre projet sans annexes donne banque vide ; aucune écriture pendant restauration')
  print('Limite : fichiers simulés ; persistance physique après extinction à tester')
  return
 if a.write_first:
  assert a.extended and not a.working
  # Même association native de slot, mais aucune restauration ne bloque Save.
  r.u.mem_write(0x404e9b4d,b'\x03')
  for addr,fn in ((0x400d0a10,lambda args:0x930a8000),
                  (0x4008c2c2,lambda args:6),
                  (0x4008c324,lambda args:current['id'])):
   r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
  r.w32(syms['ml_store_load_serial'],0)
  before_log=len(log);before_files=dict(files)
  r.call('ml_store_service')
  assert len(log)==before_log and files==before_files
  assert r.r32(syms['ml_store_load_ready'])==1
  assert r.r32(syms['ml_store_load_status'])==1
  assert r.r32(syms['ml_store_owner_id'])==current['id']
  table=r.r32(syms['ml_bank_table'])
  assert bytes(r.u.mem_read(table,384))==bytes(384)
  r.w32(table+5*4,bank);r.u.mem_write(bank,payload(77))
  assert native_save()==1 and r.r32(syms['ml_store_save_status'])==1
  assert load(current['id'],3,5)>0
  assert bytes(r.u.mem_read(snapshot,data_size))==payload(77)
  fault['verify']=True;r.u.mem_write(bank,payload(78))
  assert native_save()==1 and r.r32(syms['ml_store_save_status'])==0
  assert r.r32(syms['ml_store_save_error'])==25
  fault['verify']=False
  fault['write']=True;r.u.mem_write(bank,payload(78))
  assert native_save()==1 and r.r32(syms['ml_store_save_status'])==0
  fault['write']=False
  assert load(current['id'],3,5)>0
  assert bytes(r.u.mem_read(snapshot,data_size))==payload(77)
  # Reprise native du même projet après Save refusé : garder table et accès B.
  ready_before=r.r32(syms['ml_store_load_ready']);serial_before=r.r32(syms['ml_store_load_serial'])
  retained_table=r.r32(syms['ml_bank_table']);retained_notes=bytes(r.u.mem_read(bank,data_size))
  r.u.mem_write(STACK,struct.pack('>I',STOP));r.u.reg_write(mk.UC_M68K_REG_A7,STACK)
  r.u.reg_write(mk.UC_M68K_REG_D0,1);r.u.reg_write(mk.UC_M68K_REG_D2,RAW)
  r.u.reg_write(mk.UC_M68K_REG_D3,96)
  # Entrer avant le prologue hook avec l'épilogue sauvegardé attendu.
  saved=bytes(32);r.u.mem_write(STACK-32,saved+struct.pack('>I',STOP));r.u.reg_write(mk.UC_M68K_REG_A7,STACK-32)
  r.u.emu_start(syms['ml_store_load_hook'],STOP,count=100000)
  assert r.r32(syms['ml_store_load_serial'])==serial_before and r.r32(syms['ml_store_load_ready'])==ready_before
  r.call('ml_store_service')
  assert r.r32(syms['ml_bank_table'])==retained_table and bytes(r.u.mem_read(bank,data_size))==retained_notes
  print('ok : reprise native du même projet après Save refusé conserve table, notes et accès B')
  # Sans service UI ni Load : le Save natif confirme le propriétaire et le slot.
  r.w32(syms['ml_store_load_serial'],0);r.w32(syms['ml_store_owner_id'],0)
  r.w32(syms['ml_store_load_active'],0);r.w32(syms['ml_store_load_ready'],0)
  r.w32(syms['ml_store_project_ctx'],0)
  pending_table=r.r32(syms['ml_bank_table']);assert pending_table
  r.w32(pending_table+5*4,bank);r.u.mem_write(bank,payload(86))
  old_table=bytes(r.u.mem_read(pending_table,384));old_notes=bytes(r.u.mem_read(bank,data_size))
  assert native_save()==1 and r.r32(syms['ml_store_save_status'])==1
  assert r.r32(syms['ml_store_load_serial'])==1 and r.r32(syms['ml_store_load_ready'])==1
  assert r.r32(syms['ml_bank_table'])==pending_table
  assert bytes(r.u.mem_read(pending_table,384))==old_table and bytes(r.u.mem_read(bank,data_size))==old_notes
  r.call('ml_store_service')
  assert r.r32(syms['ml_bank_table'])==pending_table
  assert load(current['id'],3,5)>0 and bytes(r.u.mem_read(snapshot,data_size))==payload(86)
  # Une table appartenant à un autre projet ne peut jamais être adoptée.
  r.w32(syms['ml_store_load_serial'],0);r.w32(syms['ml_store_owner_id'],99)
  assert r.call('ml_store_bind_save',OBJ,3)==0
  assert r.r32(syms['ml_store_load_serial'])==0 and r.r32(syms['ml_store_owner_id'])==99
  r.w32(syms['ml_store_owner_id'],0);r.w32(syms['ml_store_project_ctx'],0)
  r.fail_new=r.new_count+1
  assert r.call('ml_store_bind_save',OBJ,3)==0
  assert r.r32(syms['ml_store_owner_id'])==0 and r.r32(syms['ml_store_load_serial'])==0
  assert r.r32(syms['ml_store_bind_error'])==4
  r.fail_new=0
  allocator=r.stubs[0x400802e0]
  def load_during_alloc(args):
   pointer=allocator(args)
   r.w32(syms['ml_store_load_serial'],7);r.w32(syms['ml_store_load_ready'],0)
   return pointer
  r.stubs[0x400802e0]=load_during_alloc
  assert r.call('ml_store_bind_save',OBJ,3)==0
  assert r.r32(syms['ml_store_load_serial'])==7 and r.r32(syms['ml_store_owner_id'])==0
  assert r.r32(syms['ml_bank_table'])==pending_table and r.r32(syms['ml_store_load_ready'])==0
  r.stubs[0x400802e0]=allocator
  print('ok : allocation refusée et Load pendant initialisation refusent adoption sans perdre les notes')
  print('ok : Save sans Load/service UI initialise le contexte et conserve les séquences éditées ; propriétaire étranger refusé')
  print('ok : contexte natif sans lecture au démarrage, B accessible immédiatement')
  print('ok : vrai Save Project + écriture/relecture MIDI, échec d’écriture refuse succès et conserve copie valide')
  print('Limite : filesystem simulé ; aucune persistance matérielle revendiquée')
  return
 r.w32(syms['ml_store_load_pending_id'],current['id']);r.w32(syms['ml_store_load_pending_slot'],3)
 r.w32(syms['ml_store_load_serial'],4)
 r.w32(syms['ml_store_io_busy'],1);count=r.new_count
 r.call('ml_store_service');assert r.new_count==count
 r.w32(syms['ml_store_io_busy'],0)
 # Contexte absent + allocation temporairement impossible : conserver le Load
 # en attente, puis reprendre sans nouvelle notification native.
 r.w32(syms['ml_store_project_ctx'],0);r.fail_new=r.new_count+1
 r.call('ml_store_service')
 assert r.r32(syms['ml_store_project_ctx'])==0
 assert r.r32(syms['ml_store_load_active'])==0
 assert r.r32(syms['ml_store_load_error'])==1
 r.fail_new=0
 r.call('ml_store_service');r.call('ml_store_service')
 assert r.r32(syms['ml_store_load_active'])==1 and r.r32(syms['ml_bank_table'])==embedded
 before=dict(files);assert native_save()==1 and files==before and r.r32(syms['ml_store_save_status'])==0
 if a.extended:assert r.r32(syms['ml_store_save_error'])==2
 if a.tweak:assert feedback[-1]=='MIDI: LOADING'
 prior_freed=len(freed);r.w32(syms['ml_store_load_serial'],5)
 r.call('ml_store_service');assert len(freed)==prior_freed+1
 for index in range(95):r.call('ml_store_service')
 assert r.r32(syms['ml_store_load_status'])==1 and r.r32(syms['ml_store_load_active'])==0
 newtable=r.r32(syms['ml_bank_table']);assert newtable!=embedded
 assert native_context not in freed and embedded not in freed
 assert bytes(r.u.mem_read(embedded,384))==bytes(384)
 for pat,note in ((5,76),(6,81)):
  ptr=r.r32(newtable+pat*4);assert ptr and bytes(r.u.mem_read(ptr,data_size))==payload(note)
 count=r.new_count;done_frees=len(freed)
 r.call('ml_store_service');assert r.new_count==count and len(freed)==done_frees
 assert r.call('ml_store_retire',newtable)==0 and len(freed)==done_frees
 assert len(cancelled)==1
 assert r.r32(runtime)==2 and r.r32(runtime+12)==0
 assert r.r32(runtime+16)==0x86480003 and r.r32(runtime+20)==0x86480003
 assert bytes(r.u.mem_read(clock,52))==bytes(52)
 for name in ('mlp_held','mlp_remove','mlp_changed','ml_gq_state','ml_gu_valid','SG_undo_valid'):assert r.r32(syms[name])==0
 # Échec d'allocation du premier pattern : table active conservée, candidat retiré.
 r.w32(syms['ml_store_load_serial'],6);r.fail_new=r.new_count+2
 before_freed=len(freed)
 for index in range(6):r.call('ml_store_service')
 assert r.r32(syms['ml_store_load_status'])==0xffffffff
 assert r.r32(syms['ml_store_load_active'])==0 and r.r32(syms['ml_bank_table'])==newtable
 assert len(freed)==before_freed+1 and len(cancelled)==1
 r.fail_new=0;count=r.new_count;r.call('ml_store_service');assert r.new_count==count
 # Annulation après restauration d'un pattern alloué : banque + table libérées.
 r.w32(syms['ml_store_load_serial'],7)
 for index in range(6):r.call('ml_store_service')
 assert r.r32(syms['ml_store_load_active'])==1
 before_freed=len(freed);r.w32(syms['ml_store_load_serial'],8)
 r.w32(syms['ml_store_load_pending_id'],99)
 r.call('ml_store_service')
 assert len(freed)==before_freed+2 and r.r32(syms['ml_bank_table'])==newtable
 assert len(cancelled)==1
 # Working96 : vrai getter OS signé, métadonnées du projet avant lecture.
 current['id']=0x12345678;r.u.mem_write(0x404e9b4d,b'\x03')
 metadata={'id':current['id'],'type':6}
 for addr,fn in ((0x400d0a10,lambda args:0x930a8000),
                 (0x4008c2c2,lambda args:metadata['type']),
                 (0x4008c324,lambda args:metadata['id'])):
  r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 r.w32(syms['ml_store_load_pending_id'],current['id'])
 r.w32(syms['ml_store_load_pending_slot'],96)
 r.w32(syms['ml_store_load_serial'],9)
 for index in range(96):r.call('ml_store_service')
 assert r.r32(syms['ml_store_load_status'])==1
 workingtable=r.r32(syms['ml_bank_table'])
 for pat,note in ((5,76),(6,81)):
  ptr=r.r32(workingtable+pat*4)
  assert ptr and bytes(r.u.mem_read(ptr,data_size))==payload(note)
 if a.working:
  # Working96 sans WRK : hérite de SEQ, puis checkpoint séparé du Save.
  seq_before={k:v for k,v in files.items() if '/SEQ-' in k}
  assert r.r32(syms['ml_store_namespace'])==2
  ptr=r.r32(workingtable+5*4);r.u.mem_write(ptr,payload(92))
  if a.audio_lfo:
   # Cette fixture FS n'a pas l'objet UI natif complet. Le test bank couvre
   # séparément le vrai ui_sync/LFO2 ; ici préserver la banque restaurée.
   at=syms['ml_bank_ui_sync'];r.stubs[at]=lambda args:1
   r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  r.call('ml_store_save_notice',OBJ,96);assert r.r32(syms['ml_store_save_status'])==1
  assert {k:v for k,v in files.items() if '/SEQ-' in k}==seq_before
  assert any('/WRK-05-' in k for k in files)
  r.w32(syms['ml_store_load_serial'],11)
  for index in range(96):r.call('ml_store_service')
  workingtable=r.r32(syms['ml_bank_table'])
  assert bytes(r.u.mem_read(r.r32(workingtable+5*4),data_size))==payload(92)
  # Reload explicite ignore WRK et retrouve SEQ.
  r.w32(syms['ml_store_load_pending_slot'],3)
  r.w32(syms['ml_store_load_serial'],12)
  for index in range(96):r.call('ml_store_service')
  workingtable=r.r32(syms['ml_bank_table'])
  assert bytes(r.u.mem_read(r.r32(workingtable+5*4),data_size))==payload(76)
  print('ok : WRK isolé de SEQ, restauration working96 et Reload explicite distincts')
 # Mauvaise identité : aucune lecture disque, ancienne table conservée.
 metadata['id']=99;r.w32(syms['ml_store_load_pending_slot'],96);r.w32(syms['ml_store_load_serial'],13)
 before_log=len(log);r.call('ml_store_service')
 assert len(log)==before_log and r.r32(syms['ml_bank_table'])==workingtable
 assert r.r32(syms['ml_store_load_status'])==0xffffffff
 print('ok : working96 résolu via slot/type/identité natifs, restauration correcte ; autre projet refusé avant I/O')
 print('ok : service UI96 ticks, remplacement candidat, publication/nettoyage, contexte natif conservé')
 if a.extended:
  # Notification IRQ différée : Save refuse avant restauration, UI seule
  # annule les anciennes notes même si l'I/O est encore occupée.
  r.w32(syms['ml_store_load_ready'],0);r.w32(syms['ml_store_suspend_pending'],1)
  before_files=dict(files);before_cancel=len(cancelled)
  assert native_save()==1 and files==before_files
  assert r.r32(syms['ml_store_save_error'])==2
  r.w32(syms['ml_store_io_busy'],1);r.call('ml_store_service')
  assert r.r32(syms['ml_store_suspend_pending'])==0
  assert len(cancelled)==before_cancel+1 and r.r32(syms['ml_store_load_ready'])==0
  r.w32(syms['ml_store_io_busy'],0)
  print('ok : notification différée, Save bloqué avant restauration, annulation uniquement depuis UI')
 if a.working:
  # Démarrage sans événement Load : contexte vivant validé, aucun fichier écrit.
  r.w32(syms['ml_store_load_serial'],0);r.w32(syms['ml_store_suspend_pending'],0)
  before_files=dict(files);before_log=len(log)
  r.stubs[0x400cf866]=lambda args:0
  r.call('ml_store_bootstrap');assert r.r32(syms['ml_store_bootstrap_error'])==1
  r.stubs[0x400cf866]=lambda args:OBJ
  r.stubs[0x4000eae2]=lambda args:0
  r.call('ml_store_bootstrap');assert r.r32(syms['ml_store_bootstrap_error'])==2
  r.stubs[0x4000eae2]=lambda args:current['id']
  metadata['id']=99
  r.call('ml_store_bootstrap')
  assert r.r32(syms['ml_store_load_serial'])==0
  metadata['id']=current['id'];metadata['type']=5
  r.call('ml_store_bootstrap')
  assert r.r32(syms['ml_store_load_serial'])==0
  metadata['type']=6
  ids=iter((current['id'],current['id']+1))
  r.stubs[0x4000eae2]=lambda args:next(ids)
  r.call('ml_store_bootstrap')
  assert r.r32(syms['ml_store_load_serial'])==0 and r.r32(syms['ml_store_bootstrap_error'])==4
  r.stubs[0x4000eae2]=lambda args:current['id']
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2500);r.call('ml_store_bootstrap')
  assert r.r32(syms['ml_store_load_serial'])==0
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2000);r.call('ml_store_bootstrap')
  assert r.r32(syms['ml_store_load_serial'])==1
  assert r.r32(syms['ml_store_load_pending_id'])==current['id']
  assert r.r32(syms['ml_store_load_pending_slot'])==96
  assert r.r32(syms['ml_store_suspend_pending'])==1
  assert r.r32(syms['ml_store_load_ready'])==0
  r.call('ml_store_bootstrap');assert r.r32(syms['ml_store_load_serial'])==1
  assert files==before_files and len(log)==before_log
  for index in range(96):r.call('ml_store_service')
  assert r.r32(syms['ml_store_load_status'])==1
  assert r.r32(syms['ml_store_load_ready'])==1
  assert files==before_files
  print('ok : bootstrap natif sans Load, slot/type/identité vérifiés, IPL refusé, restauration UI complète sans écriture')
  # Tout premier démarrage : aucune annexe ; publier une banque vide utilisable.
  dirs.clear();dirs['/']=2;files.clear();log.clear()
  # Nouvelle notification native : le compteur ne repart pas à zéro en cours de session.
  r.w32(syms['ml_store_load_serial'],r.r32(syms['ml_store_load_serial'])+1)
  for index in range(96):r.call('ml_store_service')
  assert r.r32(syms['ml_store_load_ready'])==1 and r.r32(syms['ml_store_load_status'])==1
  table=r.r32(syms['ml_bank_table']);assert bytes(r.u.mem_read(table,384))==bytes(384)
  assert not files and not any(entry[0] in ('open','mkdir') for entry in log)
  print('ok : premier démarrage sans sidecars, zéro fopen/mkdir, banque vide publiée et accès B rétabli')
 if a.extended and a.working:
  # Annexe présente mais tronquée : accès RAM rétabli, jamais d'écrasement.
  dirs['/ModdedCycles']=3;dirs['/ModdedCycles/03-12345678']=4
  badpath='/ModdedCycles/03-12345678/WRK-00-A'
  files[badpath]=b'BROKEN';before_files=dict(files)
  r.w32(syms['ml_store_load_serial'],r.r32(syms['ml_store_load_serial'])+1)
  r.w32(syms['ml_store_load_ready'],0)
  for index in range(96):r.call('ml_store_service')
  assert r.r32(syms['ml_store_load_status'])==0xffffffff
  assert r.r32(syms['ml_store_read_error'])==6
  assert r.r32(syms['ml_store_ram_only'])==1
  assert r.r32(syms['ml_store_load_ready'])==1
  table=r.r32(syms['ml_bank_table'])
  assert bytes(r.u.mem_read(table,384))==bytes(384)
  assert native_save()==1 and r.r32(syms['ml_store_save_error'])==24
  assert files==before_files
  del files[badpath]
  r.w32(syms['ml_store_load_serial'],r.r32(syms['ml_store_load_serial'])+1)
  for index in range(96):r.call('ml_store_service')
  assert r.r32(syms['ml_store_load_status'])==1
  assert r.r32(syms['ml_store_ram_only'])==0
  print('ok : annexe tronquée distinguée, B RAM accessible, Save protégé, Reload valide réactive la persistance')
 print('Backend FS simulé, vrai runtime MIDI compilé ; hooks boot/Load non installés dans le flasher.')
if __name__=='__main__':main()
