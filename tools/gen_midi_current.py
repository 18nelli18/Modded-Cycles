#!/usr/bin/env python3
"""Banque RAM autonome : backends propres epingles, TEMPO et boot PIC commun.

Reprend les huit backends sans TG/sans Chord du prototype independant ; les
fonctions A actuelles fournissent Chord et leurs propres supports. Aucun
octet de firmware n'est exporte. --mute-feedback active uniquement le candidat LED experimental. Note 97, test materiel confirme par AveyCole.
"""
import argparse,copy,hashlib,json,pathlib,shutil,struct,subprocess,sys,tempfile
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from midi_catalog_compact import compact,restore,JS_DECODER
from gen_seq_gen import symbols
ROOT=HERE.parent

def tempo(row,cross):
    """Meme correction TEMPO que le dernier bundle RAM, sans reserve disque."""
    row=copy.deepcopy(row);b=row['bank'];ap=b['append'];part=ap['parts'][0]
    raw=bytearray.fromhex(part['hex']);origin=int(part['dest'],16)
    s={k:int(v,16) for k,v in b['symbols'].items()}
    lo=s['mlp_menu_key']-origin
    at=raw.find(bytes.fromhex('0c82000000096700'),lo,lo+0x200)
    assert at>=lo and raw[at+10:at+18]==bytes.fromhex('0c820000000d6700')
    target=origin+at+8+struct.unpack('>h',raw[at+8:at+10])[0]
    assert target==origin+at+18+struct.unpack('>h',raw[at+18:at+20])[0]
    start=(origin+len(raw)+15)&~15
    with tempfile.TemporaryDirectory() as d:
        p=pathlib.Path(d)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'t.o'),str(HERE/'machines/midi_lanes/tempo.s')],check=True)
        defs={'mlp_obj':s['mlp_obj'],'ml_settings_native':s['ml_settings_native'],'ml_settings_toggle':s['ml_settings_toggle'],'ml_tempo_global':target,'ml_tempo_bank_continue':s['ml_toggle']+6}
        (p/'link.ld').write_text('\n'.join(k+' = '+hex(v)+';' for k,v in defs.items())+'\nSECTIONS { .dispatch '+hex(origin+at)+' : { *(.text.tempo_dispatch) } .text '+hex(start)+' : { *(.text) } }')
        subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','ml_tempo_present','-o',str(p/'t.elf'),str(p/'t.o')],check=True)
        new=symbols(cross,p/'t.elf')
        for section in ('dispatch','text'):
            subprocess.run([cross+'objcopy','-O','binary','--only-section=.'+section,str(p/'t.elf'),str(p/(section+'.bin'))],check=True)
        dispatch=(p/'dispatch.bin').read_bytes();code=(p/'text.bin').read_bytes()
    assert len(dispatch)==20
    raw[at:at+20]=dispatch
    raw+=bytes(start-origin-len(raw))+code
    raw+=bytes((-len(raw))%16)
    for name,newname in [('ml_settings_present','ml_tempo_present'),('ml_toggle','ml_tempo_bank_guard')]:
        i=s[name]-origin
        assert raw[i:i+6]==(b'\x4a\xb9' if name=='ml_settings_present' else b'\x20\x79')+struct.pack('>I',s['mlp_obj'])
        raw[i:i+6]=b'\x4e\xf9'+struct.pack('>I',new[newname])
    b['writes'].append(dict(off=0x4001c23a-0x40000400,old='4eb940077da8',new='4eb9'+struct.pack('>I',new['ml_tempo_toggle']).hex()))
    b['symbols'].update({k:hex(v) for k,v in new.items() if k.startswith('ml_tempo_')})
    b['symbols']['ML_BANK_END']=hex(origin+len(raw))
    part['hex']=raw.hex();ap['size']=len(raw);ap.pop('compressed_hex',None)
    b['midi_tempo_native']=True;b['status']='tested';b['hardwareTestedByOwner']=True
    return row

def mute_feedback(row,cross):
    """Extension propre du backend epingle, activee uniquement pour le test."""
    b=row['bank'];ap=b['append'];part=ap['parts'][0]
    raw=bytearray.fromhex(part['hex']);origin=int(part['dest'],16)
    sy={k:int(v,16) for k,v in b['symbols'].items()}
    signature=bytes.fromhex('7801b4b9')+struct.pack('>I',sy['mlp_track'])+bytes.fromhex('660000047803')
    pos=raw.find(signature,sy['mlp_led']-origin)
    assert pos>=0 and raw.find(signature,pos+1)<0,'etat pad attendu'
    poll=sy['mlp_led_poll']-origin
    assert raw[poll:poll+2]==bytes.fromhex('4eb9'),'tick LED attendu'
    defs=dict(sy);defs['ml_feedback_old_tick']=int.from_bytes(raw[poll+2:poll+6],'big');defs['ml_feedback_poll_return']=origin+poll+6
    start=(origin+len(raw)+15)&~15
    with tempfile.TemporaryDirectory() as d:
        p=pathlib.Path(d)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'f.o'),str(HERE/'machines/midi_lanes/mute_feedback.s')],check=True)
        (p/'f.ld').write_text('\n'.join(k+' = '+hex(v)+';' for k,v in defs.items())+'\nSECTIONS { .text '+hex(start)+' : { *(.text) } .data : { *(.data) } }')
        subprocess.run([cross+'ld','-T',str(p/'f.ld'),'-o',str(p/'f.elf'),str(p/'f.o')],check=True)
        ns=symbols(cross,p/'f.elf')
        subprocess.run([cross+'objcopy','-O','binary',str(p/'f.elf'),str(p/'f.bin')],check=True)
        payload=(p/'f.bin').read_bytes()
    raw[pos:pos+14]=bytes.fromhex('4eb9')+struct.pack('>I',ns['ml_feedback_pad'])+bytes.fromhex('4e714e714e714e71')
    raw[poll:poll+6]=bytes.fromhex('4ef9')+struct.pack('>I',ns['ml_feedback_poll'])
    raw+=bytes(start-origin-len(raw))+payload;raw+=bytes((-len(raw))%16)
    part['hex']=raw.hex();ap['size']=len(raw);ap.pop('compressed_hex',None)
    b['symbols'].update({k:hex(v) for k,v in ns.items() if k.startswith('ml_feedback_')})
    b['symbols']['ML_BANK_END']=hex(origin+len(raw))
    b['status']='experimental';b.pop('hardwareTestedByOwner',None)
    return row


def generate(cross,feedback=False):
    source=ROOT/'docs/flasher-midi-independent-test/source/midi-independent-matrix.json'
    matrix=restore(json.loads(source.read_text(encoding='utf-8')))
    rows={}
    for sg in (0,1):
        for lfo in (0,1):
            for sc in (0,1):
                key=f'0{sg}{lfo}{sc}0';row=tempo(matrix[key],cross)
                if feedback:row=mute_feedback(row,cross)
                raw=bytes.fromhex(row['bank']['append']['parts'][0]['hex'])
                assert not any('store_save' in name or 'store_disk' in name for name in row['bank']['symbols'])
                row['source_key']=key;row['raw_sha256']=hashlib.sha256(raw).hexdigest()
                rows[f'{sg}{lfo}{sc}']=row
    with tempfile.TemporaryDirectory() as d:
        p=pathlib.Path(d)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'boot.o'),str(HERE/'machines/midi_lanes/current_boot.s')],check=True)
        subprocess.run([cross+'ld','-Ttext=0','-e','midi_current_stage','-o',str(p/'boot.elf'),str(p/'boot.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'boot.elf'),str(p/'boot.bin')],check=True)
        boot={'hex':(p/'boot.bin').read_bytes().hex(),'symbols':symbols(cross,p/'boot.elf')}
    data={'variants':rows,'boot':boot,'provenance':{'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'baseline':'RAM-only optional backends; current native TEMPO fix; no Model-TG installer'}}
    packed=compact(data);assert restore(packed)==data
    return '// Genere par tools/gen_midi_current.py ; aucun firmware.\nwindow.MCMidiCurrent=(()=>{'+JS_DECODER+'return unpackCatalogue('+json.dumps(packed,separators=(',',':'))+');})();\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default='docs/flasher/midi-bank-data.js');p.add_argument('--check',action='store_true');p.add_argument('--mute-feedback',action='store_true');a=p.parse_args()
    cross=next((c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'as')),'m68k-linux-gnu-')
    text=generate(cross,a.mute_feedback);out=pathlib.Path(a.output)
    if a.check:assert out.read_text(encoding='utf-8')==text
    else:out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding='utf-8')
    print('ok huit backends RAM sans Model-TG, TEMPO natif et boot commun',flush=True)

if __name__=='__main__':main()
