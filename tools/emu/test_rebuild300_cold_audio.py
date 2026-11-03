"""PCM stock apres vrai demarrage complet, sans rejouer les installateurs.

La preuve historique reconstruisait la SRAM puis rejouait un installateur
tardif. Ici les deux entrees utilisent le meme ordre de demarrage materiel.
"""
from pathlib import Path
import hashlib
import json
import os
import sys

capture_cache_base=Path(sys.argv[sys.argv.index('--output')+1]).parent/'cold-reference'
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
from capture_rebuild300_boot import capture


def cold_boot(path):
    path=Path(path);cache=capture_cache_base/hashlib.sha256(path.read_bytes()).hexdigest()
    if not (cache/'capture.json').exists():capture(path.parent,cache)
    return (cache/'native.bin').read_bytes(),[(0x46700000,(cache/'runtime.bin').read_bytes())]


text=Path(__file__).with_name('test_stock_machine_parity.py').read_text()
text=text.replace('real_boot,real_load=boot_candidate.boot,boot_candidate.load','real_boot,real_load=cold_boot,boot_candidate.load')
text=text.replace("if not meta.get('clean_layout'):e.call(","if False:e.call(")
prefix,body=text.split('peaks=[0]*6',1)
blocks=int(os.environ.get('SM_AUDIO_BLOCKS','40'));assert 4<=blocks<=40
body=body.replace('range(40)',f'range({blocks})').replace('blocks=40',f'blocks={blocks}').replace('40 native blocks',f'{blocks} native blocks')
exec(compile(prefix,__file__,'exec'))
cache=capture_cache_base/hashlib.sha256(path.read_bytes()).hexdigest()
e.uc.mem_write(0x80000000,(cache/'sram.bin').read_bytes())
# Le moteur historique decode les instructions EMAC depuis les anciennes
# banques de transit. Le nouveau chargeur les omet : decoder la vraie SRAM
# finale, sinon Unicorn execute certaines MAC sans notre modele ColdFire.
sram_code=args.output.parent/'final-sram.bin'
sram_code.write_bytes((cache/'sram.bin').read_bytes())
e.emac.install(emac.disasm(str(sram_code),0x80000000,0x80001c5c,0x800074b4))
if meta.get('native_fx_unroll'):
    d=meta['native_fx_unroll'];raw=args.output.parent/'native-fx-unroll.bin'
    raw.write_bytes(e.uc.mem_read(d['code'],d['code_bytes']))
    e.emac.install(emac.disasm(str(raw),d['code'],d['code'],d['code']+d['code_bytes']))
if meta.get('delay_static'):
    d=meta['delay_static'];raw=args.output.parent/'delay-static-final.bin'
    raw.write_bytes(e.uc.mem_read(d['code'],d['code_bytes']))
    e.emac.install(emac.disasm(str(raw),d['code'],d['code'],d['code']+d['code_bytes']))

for key in ['chord_second','filter_unroll','filter_half_rate','post_static','output_monitor_fast','native_finish','phase_loop','native_biquad']:
    if meta.get(key):
        d=meta[key];raw=args.output.parent/(key+'-final.bin')
        raw.write_bytes(e.uc.mem_read(d['code'],d['code_bytes']))
        e.emac.install(emac.disasm(str(raw),d['code'],d['code'],d['code']+d['code_bytes']))

if meta.get('output_monitor_fast'):
    for patch in meta['output_monitor_fast']['patches']:
        at=patch['at'];e.emac.fast[at]=lambda:None;e.emac.next[at]=int.from_bytes(bytes.fromhex(patch['new'])[2:],'big')

events=[]
if os.environ.get('SM_TRACE_RETIRED')=='1' and meta.get('clean_layout',{}).get('retirement'):
    from unicorn import UC_HOOK_MEM_READ
    removed=[x for x in meta['clean_layout']['retirement']['edits'] if x['kind']=='remove']
    def read_retired(u,access,address,size,value,data):
        if len(events)>=64:return
        for item in removed:
            if item['address']<=address<item['address']+item['bytes']:
                event=dict(address=hex(address),pc=hex(u.reg_read(C.UC_M68K_REG_PC)),owner=item['owner'])
                if event not in events:events.append(event)
    e.uc.hook_add(UC_HOOK_MEM_READ,read_retired,begin=0x40140000,end=0x469fffff)
    original_mem_read=e.uc.mem_read
    def checked_mem_read(address,size):
        if len(events)<64:read_retired(e.uc,0,address,size,0,None)
        return original_mem_read(address,size)
    e.uc.mem_read=checked_mem_read
try:exec(compile('peaks=[0]*6'+body,__file__,'exec'))
finally:
    (args.output.parent/'retired-reads.json').write_text(json.dumps(events,indent=2)+'\n')
    if events:print('READS FROM RETIRED AREAS',events[:8],flush=True)
