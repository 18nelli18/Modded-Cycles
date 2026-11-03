"""Comparaison Eco HALL et activation independante, baseLUT350 ou302."""
from pathlib import Path
import hashlib,os,struct,subprocess
CODE=0x467a1200;BSS=0x467a2000;END=0x467a2100
def apply(meta,native,runtime,out,pressure=False,delay=False):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);base=0x46700000;root=Path(__file__).resolve().parents[1]
 for lo,hi in [(CODE,END),(END,END+256)]:
  assert not any(runtime[lo-base:hi-base])
  assert any(e['kind']=='remove' and e['address']<=lo and hi<=e['address']+e['bytes'] for e in meta['clean_layout']['retirement']['edits'])
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)])
 def symbols(elf):return {v[2]:int(v[0],16) for line in run('nm',elf).decode().splitlines() if len(v:=line.split())==3}
 fs=meta['fx_menu']['symbols'];ps=meta['per_track_fx']['symbols'];hall=meta['hall_merged_gain'];hc=hall['code'];hl=0x46704400
 assert hashlib.sha256(runtime[hc-base:hc-base+hall['code_bytes']]).hexdigest()==hall['sha256']
 aliases={k:v for k,v in fs.items() if k.startswith('hall_') or k in ('ps_comb','ps_ap')};aliases['eco_panic']=ps['mf_fx_panic_count']
 if pressure:aliases.update(eco_irq_t0=ps['gb_irq_t0'],eco_irq_active=ps['gb_irq_active'])
 script=f'SECTIONS {{ .text {hc:#x} : {{ *(.text*) *(.rodata*) }} .bss {END:#x} (NOLOAD) : {{ *(.bss*) }} eco_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items())
 (out/'hall.ld').write_text(script);run('gcc','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-common',*(['-DECO_VOICE_FIRST'] if pressure else []),'-c',root/'tools/machines/fx_menu/hall-eco351.c','-o',out/'hall.o');run('ld','-T',out/'hall.ld','-o',out/'hall.elf',out/'hall.o');run('objcopy','-O','binary',out/'hall.elf',out/'hall.bin');hb=(out/'hall.bin').read_bytes();hs=symbols(out/'hall.elf');assert hc+len(hb)<=hl and hs['eco_end']<=END+256
 runtime[hc-base:hl-base]=hb+bytes(hl-hc-len(hb))
 patches=[]
 def patch(at,old,new):
  off=at-base;assert runtime[off:off+len(old)]==old,(hex(at),runtime[off:off+len(old)].hex(),old.hex())
  runtime[off:off+len(new)]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 patch(fs['fx_hall'],b'\x4e\xf9'+struct.pack('>I',hall['symbols']['fx_hall']),b'\x4e\xf9'+struct.pack('>I',hs['fx_hall']))
 name=fs['fx_rev_names']+44;old=bytes(runtime[name-base:name-base+4]);ptr=int.from_bytes(old,'big');assert bytes(runtime[ptr-base:ptr-base+5])==b'HALL\0';patch(name,old,struct.pack('>I',hs['eco_hall_name']))
 rev=fs['fx_reverb'];oldrev=bytes(runtime[rev-base:rev-base+10]);assert oldrev==bytes.fromhex('4e56ff942039')+struct.pack('>I',fs['ch_mode'])
 delay_site=fs['fx_delay'];olddel=bytes(runtime[delay_site-base:delay_site-base+6]);assert olddel==b'\x4e\xf9'+struct.pack('>I',ps['pots_slot_delay'])
 asm='.text\n.globl sf_old_reverb\nsf_old_reverb:\n.byte '+','.join(map(str,oldrev))+f'\njmp {rev+10:#x}\n'
 (out/'bridge.S').write_text(asm);run('gcc','-mcpu=54418','-c',out/'bridge.S','-o',out/'bridge.o');run('gcc','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-common',*(['-DSF_ECO_DELAY'] if delay else []),'-c',root/'tools/machines/track_fx/slot-sleep351.c','-o',out/'sleep.o')
 aliases=dict(sf_rev=fs['ch_mode'],sf_del=fs['cr_mode'],sf_panic=ps['mf_fx_panic_count'],sf_old_delay=ps['pots_slot_delay'])
 objects=[out/'bridge.o',out/'sleep.o']
 if delay:
  aliases.update(ed_line=ps['fx_line'],ed_panic=ps['mf_fx_panic_count'],ed_native_active=fs['nd_active'],ed_crstate=fs['fx_delay_state'],ed_native=ps['pots_native'],ed_sidechain=0x46835ff0)
  aliases.update(ed_pots_active=ps['pots_slot_active'],ed_pots_gain=ps['pots_slot_gain'],ed_pots_prior=ps['pots_slot_prior'],ed_pots_reset=ps['pots_reset'])
  run('gcc','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-common','-c',root/'tools/machines/fx_menu/delay-eco356.c','-o',out/'delay.o');objects.append(out/'delay.o')
 script=f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) }} sf_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items())
 (out/'sleep.ld').write_text(script);run('ld','-T',out/'sleep.ld','-o',out/'sleep.elf',*objects);run('objcopy','-O','binary',out/'sleep.elf',out/'sleep.bin');blob=(out/'sleep.bin').read_bytes();sy=symbols(out/'sleep.elf');assert CODE+len(blob)<=BSS and sy['sf_end']<=END
 runtime[CODE-base:CODE-base+len(blob)]=blob
 patch(rev,oldrev,b'\x4e\xf9'+struct.pack('>I',sy['sf_reverb'])+b'\x4e\x71'*2);patch(delay_site,olddel,b'\x4e\xf9'+struct.pack('>I',sy['sf_delay']))
 if 'ed_delay_name' in sy:
  for ident,label in [(0,'ed_delay_name'),(5,'ed_ping_name')]:
   at=fs['fx_del_names']+4*ident;patch(at,bytes(runtime[at-base:at-base+4]),struct.pack('>I',sy[label]))
 return dict(code=CODE,code_bytes=len(blob),symbols=sy,hall_code=hc,hall_bytes=len(hb),hall_symbols=hs,hall_sha256=hashlib.sha256(hb).hexdigest(),patches=patches,previous_hall=hall,tail_input_free_blocks=1500,fade_blocks=32,HALL_stereo_shared_combs=2,native_tails_unchanged=not delay,independent_first_input_gates=True,quality_changed=True,hardware_tested=False,voice_first_pressure=pressure,pressure_threshold_ticks=72000 if pressure else None,eco_delay=delay,delay_rate=12000 if delay else 48000)
