"""Intégration réelle des adaptateurs filter+Attack, codecs et LFO2."""
exec(open('work/genie-attack-test/test-native.py').read().split('# Bypass exact')[0])
f=json.load(open('work/wizard-filter-continuous/data.json'));base=int(w['append']['dest'],16)
for ch in f['payload']:
 p=w['append']['parts'][0];i=ch['off']*2;assert p['hex'][i:i+len(ch['old'])]==ch['old'];p['hex']=p['hex'][:i]+ch['new']+p['hex'][i+len(ch['old']):]
for ch in f['changes']:
 off=ch['at']-build.BASE;x=next(x for x in t['writes'] if x['off']<=off and off+len(ch['old'])//2<=x['off']+len(x['new'])//2);i=(off-x['off'])*2;assert x['new'][i:i+len(ch['old'])]==ch['old'];x['new']=x['new'][:i]+ch['new']+x['new'][i+len(ch['old']):]
lf=next(x for x in json.load(open('work/sample-wizard-options/case-pair-lfo-secondary.json'))['tweaks'] if x['id']=='lfo-secondary');image,_=build.apply_writes(stock,[w,sg,lf,t,f['recipe']]);r=C.Rig(image,[(base,build.payload_runtime(w,stock,None))]);fs={k:int(v,16) for k,v in f['recipe']['symbols'].items()};frame=C.FAKE+0x30000;buf=C.FAKE+0x40000;trig=C.FAKE+0x50000
r.stub(ws['sampler_pre'],lambda a:0);r.stub(0x40056f58,lambda a:0);r.w32(trig,0);r.w32(trig+4,0)
# Aucun pointeur de voix n'est nécessaire au ladder continu ; ses six slots restent nuls.
assert r.rd(ws['voice_ptr'],24)==bytes(24)
raw=struct.pack('>32i',*([0x18000000]*32))
for active in [0,1,5,-1]:
 for track in range(6):
  r.w8(frame+18,track);r.w16(frame+46,0);r.w16(frame+48,0x3800 if track==active else 32512);r.w16(frame+50,0)
  r.call(fs['avfc_pre'],regs={C.D[1]:0x12345678,C.D[2]:track,C.A[2]:frame,C.A[3]:trig,C.A[5]:trig+4},check='chained pre ABI');r.uc.mem_write(buf+track*128,raw)
 r.call(s['ava_post'],buf,frame,check='chained post ABI')
 for track in range(6):assert (r.rd(buf+track*128,128)!=raw)==(track==active),(active,track)
print('PASS installed coefficient/Attack/filter adapters: native registers, no voice-pointer reads, only selected track filtered, open/no-res exact bypass')
# Wizard reste hors du ladder stock et reçoit son filtre propre uniquement.
r.w8(frame+18,6);r.w16(frame+48,0x1800);r.call(fs['avfc_pre'],regs={C.D[1]:0,C.D[2]:0,C.A[2]:frame,C.A[3]:trig,C.A[5]:trig+4});assert r.r32(ws['gflt_f'])==0
print('PASS Wizard bypass of shared filter; its own filter remains separate')
rng=random.Random(82);vals=[0x4c00,0x0800,0x0300,0x1800,0x5100]
for machine in range(7):
 snd=bytearray(C.sound_bytes(rng,vals));snd[38]=machine;struct.pack_into('>3H',snd,66,0x2200,0x3500,0x1800);snd[72:76]=b'\x12\x34\x56\x78';r.uc.mem_write(C.SOUND,bytes(snd));r.call(C.SND_SAVE2,C.REC,C.SOUND,check='sound save');r.call(C.SND_LOAD,C.SOUND2,C.REC,check='sound load');assert r.rd(C.SOUND2+66,6)==bytes.fromhex('220035001800');assert [r.r16(C.SOUND2+76+2*i) for i in range(5)]==vals;assert r.rd(C.SOUND2+72,4)==b'\x12\x34\x56\x78'
assert not C.FAIL and not r.bad,(C.FAIL,r.bad)
print('PASS seven native sound round-trips: Attack, cutoff/resonance, SecondLFO five saved settings and Wizard packed mode/Slice state; ABI')
