"""Moteur Attack, codecs réels et interface Genie sans accès matériel."""
import json,struct,copy,random
import build,test_lfo_plus as C
from chord_keys_pr87 import load_stock
P='work/genie-attack-test/';d=json.load(open(P+'data.json'));w=copy.deepcopy(json.load(open('work/sample-wizard-main/installer.json')));sg=copy.deepcopy(json.load(open('work/genie-queue-choice/recipes.json'))['wizard']);s={k:int(v,16) for k,v in d['recipe']['symbols'].items()};ws={k:int(v,16) for k,v in w['symbols'].items()};ss={k:int(v,16) for k,v in sg['symbols'].items()}
for ch in d['payload']:
 p=w['append']['parts'][0];i=ch['off']*2;assert p['hex'][i:i+len(ch['old'])]==ch['old'];p['hex']=p['hex'][:i]+ch['new']+p['hex'][i+len(ch['old']):]
for ch in d['sg']:
 off=ch['at']-build.BASE;x=next(x for x in sg['writes'] if x['off']<=off and off+len(ch['old'])//2<=x['off']+len(x['new'])//2);i=(off-x['off'])*2;assert x['new'][i:i+len(ch['old'])]==ch['old'];x['new']=x['new'][:i]+ch['new']+x['new'][i+len(ch['old']):]
t=copy.deepcopy(d['recipe']);t['writes']+=d['attack']+d['pool'];t['writes'].sort(key=lambda x:x['off']);stock=load_stock('firmware/model-cycles_OS1.13.syx');img,_=build.apply_writes(stock,[w,sg,t]);r=C.Rig(img,[(int(w['append']['dest'],16),build.payload_runtime(w,stock,None))]);rng=random.Random(30)
# Bypass exact, rampe monotone, durée par piste, indépendance six voix.
buf=C.FAKE+0x30000;frame=C.FAKE+0x40000;trigger=C.FAKE+0x50000;previous=trigger+4
r.stub(ws['sampler_pre'],lambda a:0)
for track in range(6):
 r.w32(ws['trk_mach']+track*4,0)
 for value in [0,256,0x2000,0x7f00]:
  r.w16(frame+46,value);r.w8(frame+18,track%6);r.w32(trigger,1);r.w32(previous,0)
  r.call(s['ava_pre'],regs={C.D[1]:0x11223344,C.D[2]:track,C.A[2]:frame,C.A[3]:previous,C.A[5]:trigger},check='pre ABI')
  raw=struct.pack('>32i',*([0x20000000]*32));r.uc.mem_write(buf,raw);r.call(s['ava_run'],buf,track,check='ramp ABI');out=struct.unpack('>32i',r.rd(buf,128))
  if not value:assert r.rd(buf,128)==raw
  else:assert out[0]==0 and all(a<=b for a,b in zip(out,out[1:])) and out[-1]>0,(track,value,out)
  gain=r.r32(ws['atk_gain']+track*4);r.w32(previous,1);r.call(s['ava_pre'],regs={C.D[1]:0,C.D[2]:track,C.A[2]:frame,C.A[3]:previous,C.A[5]:trigger});assert r.r32(ws['atk_gain']+track*4)==gain
print('PASS six tracks, four attack settings: zero bit exact, real trigger-edge restart, monotone ramps and no repeated reset, ABI')
# Wizard ne reçoit pas deux enveloppes.
r.w32(ws['trk_mach'],6);r.w32(ws['atk_step'],500);r.w32(ws['atk_gain'],0);raw=struct.pack('>32i',*range(32));r.uc.mem_write(buf,raw);r.call(s['ava_run'],buf,0);assert r.rd(buf,128)==raw
print('PASS Wizard bypass of the additional synth ramp; existing sampler envelope retained')
# Les codecs du son natifs gardent Attack et les cinq paramètres SecondLFO.
for machine in range(7):
 vals=[0x4c00,0x0800,0x0300,0x1800,0x5100];snd=bytearray(C.sound_bytes(rng,vals));snd[38]=machine;struct.pack_into('>H',snd,66,0x2800);r.uc.mem_write(C.SOUND,bytes(snd));r.call(C.SND_SAVE2,C.REC,C.SOUND,check='native sound save');assert r.r16(C.REC+76)==0x2800
 r.call(C.SND_LOAD,C.SOUND2,C.REC,check='native sound load');assert r.r16(C.SOUND2+66)==0x2800
print('PASS native current-format sound save/load Attack on stock and Wizard; no filter added')
ram=C.PSRC;file=C.ROWS;locks=[(0,0,23,0x1a00),(5,63,23,0x4500),(2,8,32,0x0300)]
def init():r.uc.mem_write(ram,(b'\xff\xff'*(34*64)+bytes(33))*6)
init()
for tr,st,k,v in locks:r.w16(ram+4385*tr+68*st+2*k,v);r.w8(ram+4385*tr+4352+k,1)
r.call(C.PLK_SAVE,file,ram,0,check='lock save');init();r.call(C.PLK_LOAD,ram,file,check='lock load')
for tr,st,k,v in locks:assert r.r16(ram+4385*tr+68*st+2*k)==v
print('PASS native pool Attack locks and ChordKeys Harmony survive together')
# Rendu : vraies fonctions propres, rasterisation OS remplacée seulement par collecte.
rects=[];texts=[];bitmap=C.BMP
r.stub(C.FILL_RECT,lambda a:rects.append(tuple(a[:6])) or 0)
def string(at):
 out=b''
 while r.r8(at):out+=bytes([r.r8(at)]);at+=1
 return out.decode('ascii')
r.stub(C.TEXT,lambda a:texts.append((a[2],a[3],string(r.r32(r.uc.reg_read(C.A[7])+28)) if string(a[5])=='%s' else str(r.r32(r.uc.reg_read(C.A[7])+28)))) or 0)
r.w32(ss['sg_intro'],0);r.w32(ss['sg_row'],0);r.w32(ss['sg_edit'],0);r.call(ss['sg_render'],C.VIEWOBJ,bitmap,check='render ABI');assert (19,46,'S.G.') in texts,(texts,rects);assert any(x[1:]==(2,0,36,63,0xffffffff) for x in rects);assert all(x>=44 or x==19 for x,y,text in texts),texts
print('PASS actual Genie render: restored S.G./20-rectangle lamp, text in right panel, highlight right of lamp, ABI')
# Vtable privée LedHandler, aucun changement dans le tableau stock.
r.call(s['avg_open_led'],regs={C.A[4]:C.VIEWOBJ});assert r.r32(C.VIEWOBJ+0x2f00)==s['avg_led_vt']+8;assert r.uc.reg_read(C.D[0])==ss['sg_pad']
r.w32(C.VIEWOBJ,ss['sg_vt']+8);assert r.call(0x400f4cec,C.VIEWOBJ,0x401121c0,0x400ff970,0xfffffffe)==C.VIEWOBJ+0x2f00
print('PASS actual OS dynamic_cast recognizes private Genie LedHandler; stock vtable unchanged')
# Mutes : getter réel de bitmap natif, sortie LED remplacée uniquement par collecte.
kit=C.FAKE+0x60000;handle=kit+48;vt=kit+0x1000;rawmute=kit+0x2000;code=kit+0x3000;mask=kit+0x4000;writer=kit+0x5000
r.w32(handle,vt);r.w32(vt+40,code);r.uc.mem_write(code,b'\x20\x3c'+struct.pack('>I',rawmute)+b'\x4e\x75');r.stub(C.CUR_PROJ,lambda a:kit);r.stub(C.PROJ_SEQ,lambda a:handle);r.stub(0x400cfaf4,lambda a:writer);r.stub(0x400060bc,lambda a:48+a[0]);writes=[];r.stub(0x40005f86,lambda a:writes.append(tuple(a[:4])) or 0)
for bits in range(64):
 r.w32(rawmute+20,bits);r.w32(ss['sg_func'],1);r.w32(mask,0);r.w32(mask+4,0);writes.clear();r.call(s['avg_led'],C.VIEWOBJ+12,0,mask,check='mute LED ABI');assert len(writes)==6
 for tr,x in enumerate(writes):assert x==(writer,48+tr,260 if bits&(1<<tr) else 3,0x404a8cb8),(bits,tr,x)
 assert r.r32(mask)==0x003f0000 and r.r32(mask+4)==0
r.w32(ss['sg_func'],0);writes.clear();r.call(s['avg_led'],C.VIEWOBJ+12,0,mask);assert not writes
assert not C.FAIL and not r.bad,(C.FAIL,r.bad)
print('PASS all64 stock mute masks: dim muted, lit unmuted; only pad mask claimed, native steps/pulses untouched; FUNC release relinquishes LEDs')
# Vrai gestionnaire LED et RTTI : pads prioritaires, pas de la vue du dessous.
manager=kit+0x6000;top=kit+0x6100;bottom=kit+0x6200;lower=kit+0x7000;lowvt=kit+0xa000;fake=kit+0xb000
r.uc.mem_write(lower,r.rd(C.VIEWOBJ,0x2f10));r.uc.mem_write(lowvt,r.rd(s['avg_led_vt'],20));r.w32(lower+0x2f00,lowvt+8);r.w32(lowvt+16,fake);r.w32(ss['sg_func'],1)
def background(args):
 for led in range(1,17):
  if not r.r32(writer+40+4*led):r.w32(writer+40+4*led,3 if led%2 else 1)
 r.w32(args[2],0);r.w32(args[2]+4,0x1fffe)
 return 1
r.stub(fake,background);r.stub(0x400e8684,lambda a:0);r.stub(0x400d08ce,lambda a:0);r.stub(0x40005f86,None)
head=manager+20;r.w32(head,bottom);r.w32(head+4,top);r.w32(top,head);r.w32(top+4,bottom);r.w32(top+8,C.VIEWOBJ);r.w32(bottom,top);r.w32(bottom+4,head);r.w32(bottom+8,lower)
r.w32(rawmute+20,0b101010);r.uc.mem_write(writer,bytes(256));r.call(0x40076ca2,manager)
assert [r.r32(writer+40+4*(48+i)) for i in range(6)]==[3,260,3,260,3,260]
assert [r.r32(writer+40+4*i) for i in range(1,17)]==[3 if i%2 else 1 for i in range(1,17)]
print('PASS actual OS LED manager/RTTI/writer: mute pads owned by Genie, sequencer step lights preserved beneath it')
