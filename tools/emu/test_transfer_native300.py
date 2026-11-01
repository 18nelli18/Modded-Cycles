"""Export3.00 : anciens RSG1 mono/stereo, gain, CRC, hash natif et lectures partielles."""
from pathlib import Path
src=Path(__file__).with_name('test_control_all_undo.py').read_text().split("if m.get('cpu_monitor'):")[0].split('held=set();')[0]
exec(compile(src,__file__,'exec'))
import zlib,random
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE
previous=r;r=Rig(bytes(previous.u.mem_read(0x40000400,0x200000-0x400)),{'writes':[]},{'writes':[],'symbols':{}})
for lo,hi,permissions in previous.u.mem_regions():
 if lo==0x46700000 or lo==0xfc070000:r.u.mem_map(lo,hi-lo+1);r.u.mem_write(lo,bytes(previous.u.mem_read(lo,hi-lo+1)))
def bind(at,fn):
 if at not in r.stubs:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.stubs[at]=fn

s=m['transfer300']['symbols'];mode=m['transfer300']['aliases']['ex_id_mode'];r.w32(mode,1)
msg,vector,reply=0x93180000,0x93181000,0x93190000;datafile=[b''];file_reads=[];closed=[]
file=0x93185000;io=0x93193000;native_closes=[]
# Vraies couches File::read et small-file OS ; seul le backend de stockage est simule.
for at in (0x4007bc5e,0x4007baaa,0x4007bc1c):r.stubs.pop(at,None)
for at in (0x40001cc4,0x40001df6):bind(at,lambda args:0)
def diskread(args):
 inode,off,n,dest=args[:4];assert inode==77;chunk=datafile[0][off:off+n];file_reads.append((off,n));r.u.mem_write(dest,chunk);return len(chunk)
bind(0x4007b8b2,diskread);bind(0x4007c0f2,lambda args:len(datafile[0]))
from unicorn import UC_HOOK_CODE
r.u.hook_add(UC_HOOK_CODE,lambda *args:native_closes.append(1),begin=0x4007bc1c,end=0x4007bc1c)
def make_file():
 r.u.mem_write(file,bytes(44));r.w32(file+8,77);r.w32(file+20,1);r.u.mem_write(file+24,b'\x01');r.w32(0x40f07cf4,1);r.w32(0x40fe8e10+4*(77>>5),1<<(77&31))
def request(t,payload):
 r.u.mem_write(vector,b'\0'*5+payload);r.u.mem_write(msg,bytes(24));r.u.mem_write(msg+8,bytes([t]));r.w32(msg+12,vector);r.w32(msg+16,vector+5+len(payload));r.call(s['ex_request'],msg)
transport,tvt=0x93188000,0x93188100
sent=[]
r.w32(transport,tvt);r.w32(tvt+16,0x93188200);r.w32(tvt+12,0x93188210)
bind(0x93188200,lambda args:sent.append(bytes(r.u.mem_read(args[1],args[2]))) or 1)
bind(0x93188210,lambda args:1)
def send_payload(t,payload):
 r.u.mem_write(reply-5,bytes(5)+payload);r.u.mem_write(msg+8,bytes([t]));r.w32(msg+12,reply-5);r.w32(msg+16,reply+len(payload));before=len(file_reads)
 r.call(0x40094a04,msg,transport)
 assert len(file_reads)==before,'Filesystem access during final send'
 return sent[-1][5:]
def response(t,payload):
 if t in (0xb2,0xb5,0xb6,0xb7) and r.r32(s['active']):
  prefix=21 if t in (0xb6,0xb7) else 17;n=r.r32(s['req_n']);off=r.r32(s['req_off']);assert r.call(s['vx_read'],file,io,n)==n
  data=bytes(r.u.mem_read(io,n));payload=b'\x01'+struct.pack('>IIII',77,off+n,n,off)+(struct.pack('>I',zlib.crc32(data,0xffffffff)) if t in (0xb6,0xb7) else b'')+data
  assert r.r32(file+12)==off+n and r.r32(file+40)==off+n
 return send_payload(t,payload)
def nativehash(payload):
 r.w32(0x4027cca4,0)
 for at in (0x4027d158,0x4027d15c,0x4027d160):r.w32(at,0x43fa243a)
 r.u.mem_write(reply,payload);r.call(0x4007dcb2,reply,len(payload));return r.call(0x4007d9c0)|1
acid=m['acid_articulation'];guard=bytes((i*17+53)&255 for i in range(acid['bss_end']-acid['bss']));r.u.mem_write(acid['bss'],guard)
rng=random.Random(304);cases=0
for stereo in (0,1):
 for gain in (0,1024,4096,16384,65536):
  frames=4099;mid=[rng.randrange(-32768,32768) for _ in range(frames)];side=[rng.randrange(-32768,32768) for _ in range(frames)] if stereo else []
  raw=struct.pack('>'+str(len(mid+side))+'h',*(mid+side));head=bytearray(64)
  for off,val in [(4,len(raw)),(8,48000),(16,frames-1),(20,0x7f000000),(24,0x52534731),(28,gain),(32,stereo)]:struct.pack_into('>I',head,off,val)
  datafile[0]=bytes(head)+raw+bytes(16);original=datafile[0]
  peak=max(abs(v) for i,v0 in enumerate(mid) for v in ([v0+side[i],v0-side[i]] if stereo else [v0]));g=min(gain or 4096,134213632//peak) if peak else gain or 4096;clip=lambda x:max(-32768,min(32767,(x*g)>>12))
  expected_samples=[v for i,v0 in enumerate(mid) for v in ([clip(v0+side[i]),clip(v0-side[i])] if stereo else [clip(v0)])]
  head[1]=stereo;head[24:]=bytes(40);expected=bytes(head)+struct.pack('>'+str(len(expected_samples))+'h',*expected_samples)
  make_file();before=len(file_reads);request(0x30,b'/Resampled/take\0');request(1,b'');assert len(file_reads)==before,'Filesystem access in parser';r.call(s['vx_open'],file);assert r.r32(file+40)==r.r32(file+12)==0;opened=response(0xb0,b'\x01'+struct.pack('>II',77,len(original)));assert int.from_bytes(opened[5:9],'big')==len(expected)
  actual=bytearray();chunk_sizes=[1,13,49,127,257,2048,32768];offset=0
  while offset<len(expected):
   n=min(chunk_sizes[len(actual)%len(chunk_sizes)],len(expected)-offset);request(0x36,struct.pack('>III',77,n,offset));packet=response(0xb6,b'\x01'+struct.pack('>IIIII',77,0,n,offset,0)+bytes(n));assert len(packet)==21+n
   assert int.from_bytes(packet[17:21],'big')==zlib.crc32(packet[21:],0xffffffff),('CRC',stereo,gain)
   actual+=packet[21:];offset+=n
  assert actual==expected,('PCM/header',stereo,gain,next((i for i,(x,y) in enumerate(zip(actual,expected)) if x!=y),None))
  closes=len(native_closes);request(0x31,struct.pack('>I',77));assert len(native_closes)==closes,'Extra close in parser';r.call(0x4007c022,file);closed_packet=response(0xb1,struct.pack('>II',77,len(original)));assert int.from_bytes(closed_packet[4:8],'big')==len(expected);assert len(native_closes)==closes+1 and r.r32(file+20)==0;assert bytes(r.u.mem_read(acid['bss'],len(guard)))==guard,'Export/cancel corrupted ACID state';request(0x10,b'/Resampled\0');request(2,b'');entry=struct.pack('>II',0x12345679,len(original))+b'\0Ftake\0';listing=response(0x90,entry);h=nativehash(expected+bytes(16));assert listing[:8]==struct.pack('>II',h,len(expected)),('hash or size',stereo,gain,listing[:8].hex(),hex(h))
  assert datafile[0]==original;assert bytes(r.u.mem_read(acid['bss'],len(guard)))==guard,'Export corrupted ACID state';cases+=1
# Annulation a mi-fichier : le parseur laisse le File ouvert a son proprietaire natif.
r.w32(mode,1);datafile[0]=original;make_file();request(0x30,b'/Resampled/take\0');r.call(s['vx_open'],file);response(0xb0,b'\x01'+struct.pack('>II',77,len(original)))
# Executer le vrai handler READ, avec retour de structure cache par a0.
session,returned=0x93186000,0x93187000;r.u.mem_write(session,bytes(96));r.w32(session+76,file);bind(0x400802ec,lambda args:0)
request(0x36,struct.pack('>III',77,1024,0));r.u.reg_write(C.UC_M68K_REG_A0,returned);r.call(0x400887c2,session,77,1024,0)
assert r.r32(returned)==0,('Native READ rejected',r.r32(returned))
start=r.r32(returned+12);finish=r.r32(returned+16);assert finish-start==1024 and bytes(r.u.mem_read(start,1024))==expected[:1024]
assert r.r32(file+40)==r.r32(file+12)==1024
# Deuxieme bloc reel : reproduire le rejet de position observe sur le materiel.
request(0x36,struct.pack('>III',77,1024,1024));r.u.reg_write(C.UC_M68K_REG_A0,returned);r.call(0x400887c2,session,77,1024,1024)
assert r.r32(returned)==0,('Second native READ rejected',r.r32(returned))
start=r.r32(returned+12);assert bytes(r.u.mem_read(start,1024))==expected[1024:2048]
assert r.r32(file+40)==r.r32(file+12)==2048
# Meme fichier rouvert : le cache du premier bloc ne doit pas court-circuiter
# l avancement du nouveau File. Executer le vrai detour OPEN avec a5/session.
bind(0x40089eca,lambda args:0)
for reopen in range(3):
 make_file();request(0x30,b'/Resampled/take\0');r.u.reg_write(C.UC_M68K_REG_A5,session);r.call(s['vx_open_hook'])
 request(0x36,struct.pack('>III',77,1024,0));r.u.reg_write(C.UC_M68K_REG_A0,returned);r.call(0x400887c2,session,77,1024,0)
 assert r.r32(returned)==0 and r.r32(file+40)==1024,('Reopened cached first chunk',reopen,r.r32(file+40))
 assert bytes(r.u.mem_read(r.r32(returned+12),1024))==expected[:1024]
before=len(native_closes);io_count=len(file_reads);request(0x31,struct.pack('>I',77));assert len(native_closes)==before and len(file_reads)==io_count
assert r.u.mem_read(file+24,1)==b'\x01';r.call(0x4007c022,file);assert len(native_closes)==before+1 and r.u.mem_read(file+24,1)==b'\0'
assert bytes(r.u.mem_read(acid['bss'],len(guard)))==guard
# Fichier standard : aucune conversion, le chemin RPC natif reste libre.
head=bytearray(64);struct.pack_into('>II',head,4,128,48000);datafile[0]=bytes(head)+bytes(128);make_file();request(0x30,b'/Other/regular\0');r.call(s['vx_open'],file);packet=b'\x01'+struct.pack('>II',77,len(datafile[0]));assert response(0xb0,packet)==packet
# Vrai constructeur CLOSE : le corps est ajoute APRES l initialisation a longueur zero.
obj,record=0x9318a000,0x9318b000;r.u.mem_write(obj,bytes(96));r.u.mem_write(record,struct.pack('>II',77,208))
r.w32(s['closing'],1);r.w32(s['closed_sid'],77);r.w32(s['closed_size'],192)
r.call(0x400ecb6a,obj,0x1234,record)
start=r.r32(obj+12);end=r.r32(obj+16);assert end-start==13
assert bytes(r.u.mem_read(start+5,8))==struct.pack('>II',77,208),'Constructor body missing'
r.call(0x40094a04,obj,transport);assert sent[-1][5:]==struct.pack('>II',77,192),'Final native send did not correct late body'
r.w32(mode,0);request(0x30,b'/Resampled/take\0');assert not r.r32(s['active'])
print('PASS',cases,'legacy recordings: native File read and single native close, gain/stereo/CRC/hash, no I/O in parser/serializer',flush=True)
a.output.write_text(json.dumps(dict(cases=cases,source_syx=m['sha256'],legacy_RSG1=True,mono=True,stereo=True,playback_gain=True,partial_reads=True,native_File_read=True,native_File_close_once=True,sample_reply_types=True,virtual_close_size=True,native_READ_handler=True,mid_transfer_cancel=True,no_IO_in_parser_serializer=True,acid_state_unchanged=True,interleaved_identity_queries=True,crc_matches_zlib=True,canonical_hash_matches_native=True,disk_unchanged=True,non_RSG1_unchanged=True,hardware_tested=False),indent=2)+'\n')
