#!/usr/bin/env python3
"""Note79 : LEDs REC B et pads ChordKeys stock sans TRIG physique tenu.

--bank JSON --chord JSON --with-chord --output JSON [--check].
Adapteurs propres ajoutés au RAW déjà réservé ; aucune E/S ni fonction audio.
"""
import argparse,copy,hashlib,json,pathlib,struct,subprocess,tempfile
import aplib_cost,build
SRC=pathlib.Path(__file__).parent/'machines/midi_play_ui/controls.s'
def generate(base,chord,with_chord=False,dynamic=False):
 t=copy.deepcopy(base);s={k:int(v,16) for k,v in t['symbols'].items()};ck={k:int(v,16) for k,v in chord['symbols'].items()};ap=t['append'];part=ap['parts'][0];dest=int(part['dest'],16);raw=bytearray.fromhex(part['hex']);start=dest+len(raw);assert start==s['ML_BANK_END']
 if not dynamic:assert start==0x401cdca0
 imports={'MLP_TRACK':s['mlp_track'],'MLP_HELD':s['mlp_live_held'],'TG_PHASE':s['TG_slide_phase'],'CK_HELD_PADS':ck['held_pads'],'CK_PAD':ck['ck_ui_pad']}
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d);subprocess.run(['m68k-elf-as','-march=cfv4e','-o',str(p/'ui.o'),str(SRC)],check=True)
  (p/'ui.ld').write_text('\n'.join(k+' = '+hex(v)+';' for k,v in imports.items())+f'\nSECTIONS {{ .adapter {start:#x} : {{ *(.text*) *(.data*) . = ALIGN(16); }} }}')
  subprocess.run(['m68k-elf-ld','-T',str(p/'ui.ld'),'-e','mpu_led_begin','-o',str(p/'ui.elf'),str(p/'ui.o')],check=True);subprocess.run(['m68k-elf-objcopy','-O','binary','--only-section=.adapter',str(p/'ui.elf'),str(p/'ui.bin')],check=True)
  code=(p/'ui.bin').read_bytes();own={x[2]:int(x[0],16) for line in subprocess.check_output(['m68k-elf-nm',str(p/'ui.elf')],text=True).splitlines() if len(x:=line.split())==3 and x[2].startswith('mpu_')}
 edits=[]
 def patch(at,old,new,role):
  assert len(old)==len(new) and raw[at-dest:at-dest+len(old)]==old,(role,hex(at));raw[at-dest:at-dest+len(old)]=new;edits.append(dict(at=hex(at),old=old.hex(),new=new.hex(),role=role))
 lo=s['mlp_led']-dest;hi=s['mlp_cursor']-dest
 pattern=b'\x2a\x00\x20\x39'+struct.pack('>I',s['mlp_track']);at=raw.index(pattern,lo,hi);assert raw.find(pattern,at+1,hi)<0
 patch(dest+at,pattern,b'\x4e\xb9'+struct.pack('>I',own['mpu_led_begin'])+b'\x4e\x71','record_frame')
 at=raw.index(bytes.fromhex('7801082a00000003'),lo,hi);end=raw.index(bytes.fromhex('4879404a8cb82f04'),at,hi);old=bytes(raw[at:end]);assert b'\x4e\xb9'+struct.pack('>I',s['TG_slide_phase']) in old
 new=b'\x4e\xb9'+struct.pack('>I',own['mpu_led_state'])+b'\x4e\xf9'+struct.pack('>I',dest+end);new+=b'\x4e\x71'*((len(old)-len(new))//2);patch(dest+at,old,new,'step_states')
 if with_chord:
  at=ck['ck_ui_pad_thunk'];expected=bytes.fromhex('51af000451af00044ef9')+struct.pack('>I',ck['ck_ui_pad']);assert raw[at-dest:at-dest+14]==expected
  patch(at+8,expected[8:],b'\x4e\xf9'+struct.pack('>I',own['mpu_pad']),'chord_pad')
 raw+=code;end=dest+len(raw);assert end<=(0x401cf750 if dynamic else 0x401ce400)
 at=s['ml_boot_skip'];patch(at,b'\x20\x7c'+struct.pack('>I',start),b'\x20\x7c'+struct.pack('>I',end),'boot_end')
 packed=aplib_cost.pack(bytes(raw),depth=512,lazy=True);assert int(ap['at'],16)+len(packed)<=build.END_LIMIT
 part['hex']=raw.hex();ap['size']=len(raw);ap['compressed_hex']=packed.hex();t['symbols'].update({k:hex(v) for k,v in own.items()});t['symbols']['ML_BANK_END']=hex(end);t['symbols']['ML_BANK_SIZE']=hex(len(raw))
 primary=next(w for w in chord['writes'] if w['off']==0x4010025c-build.BASE);assert primary['new']==struct.pack('>I',ck['ck_ui_pad']).hex()
 t['play_ui']={'chord_primary':dict(off=primary['off'],old=primary['old'],new=struct.pack('>I',own['mpu_pad']).hex()),'start':hex(start),'end':hex(end),'size':len(code),'with_chord':with_chord,'edits':edits,'raw_sha256':hashlib.sha256(raw).hexdigest(),'flash_margin':build.END_LIMIT-int(ap['at'],16)-len(packed)}
 return t

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bank',required=True);p.add_argument('--chord',required=True);p.add_argument('--with-chord',action='store_true');p.add_argument('--dynamic',action='store_true');p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();t=generate(json.loads(pathlib.Path(a.bank).read_text()),json.loads(pathlib.Path(a.chord).read_text()),a.with_chord,a.dynamic);data=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==data
 else:out.write_text(data)
 print('ok : UI REC/Chord,',t['play_ui'])
if __name__=='__main__':main()
