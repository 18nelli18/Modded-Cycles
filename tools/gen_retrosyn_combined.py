#!/usr/bin/env python3
"""RETROSYN avec toutes les machines actuelles, dont WAVE et TINY (notes/96).

Reprend les corps du catalogue TINY actuel sans les recompiler ; regenere les
interfaces communes et ajoute RETROSYN apres TINY. Aucun octet Elektron fourni.
"""
import argparse
import copy
import hashlib
import json
import pathlib
import struct
import sys
import tempfile
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE/'emu')]
import gen_retrosyn as R
import gen_macro as gm
import gen_syntakt_engines as gs
import gen_sdvintage_7th as g7
import build
import syntakt
import aplib_cost


def generate(stock,st,catalog,wizard=False,wizard_base=None):
    variant=catalog['variants']['511'] if wizard else catalog['normal']['255']
    base=copy.deepcopy(variant['engine'])
    sampler=copy.deepcopy(variant['wizard']) if wizard else None
    if sampler:
        if wizard_base is None: raise ValueError('catalogue Sample Wizard requis')
        sampler['writes']=copy.deepcopy(wizard_base['writes'])
        sampler['writes']=[w for w in sampler['writes'] if w['off'] != gs.gx.CAVE-gs.BASE]
        root=next(w for w in sampler['writes'] if w['off']==gs.BOOT_CALL-gs.BASE)
        root['new']='4eb9'+sampler['symbols']['boot_extra_hook'][2:].zfill(8)
    pay=int(base['append']['dest'],16)
    gs.set_base(pay)
    parts=base['append']['parts']
    def read(addr,size):
        for p in parts:
            if 'hex' not in p: continue
            lo=int(p['dest'],16);b=bytes.fromhex(p['hex'])
            if lo<=addr and addr+size<=lo+len(b): return b[addr-lo:addr-lo+size]
        raise ValueError(hex(addr))
    def u32(addr): return struct.unpack('>I',read(addr,4))[0]
    def string(addr):
        out=bytearray()
        for i in range(64):
            c=read(addr+i,1)
            if c==b'\0': return out.decode('ascii')
            out.extend(c)
        raise ValueError('chaine invalide')
    old_data=pay+0x33800; old_desc=pay+0x33d00; first=7 if wizard else 6;nm=first+9
    assert [string(u32(old_data+4*i)) for i in range(first+5,nm)]==['MACRO','ACID','Wave','TINY']
    codes=['sd','cp','toy','bits','swarm']
    machines=[]
    for j in range(5,9):
        index=first+j;desc=old_desc+(g7.NDESC+5*j)*g7.DSTRIDE
        knobs=[]
        for k in range(4):
            at=desc+k*g7.DSTRIDE
            knobs.append((string(u32(at+44)),string(u32(at+52)),u32(at+16)>>8,u32(at+8)>>8,u32(at+12)>>8))
        name=string(u32(old_data+4*index))
        machines.append(dict(name=name,label=name,image=4,decay=u32(desc+4*g7.DSTRIDE+16)>>8,knobs=knobs,
                             update=u32(old_data+4*(nm+index)),render=u32(old_data+4*(2*nm+index))))
    # Passerelle Syntakt et regulateur : exacts, repris du catalogue actuel.
    an=gs.analyse(st,gs.generation(codes));lay=an['lay']
    syms={k:int(v,16) for k,v in base['gov'].items()}
    for j,c in enumerate(codes):
        en=gs.CATALOG[c]['engine'];i=first+j
        syms[f'bridge_update_{en}']=u32(old_data+4*(nm+i))
        syms[f'bridge_render_{en}']=u32(old_data+4*(2*nm+i))
    hot=[(a,bytes.fromhex(p['hex']),run) for a,run,n in lay['tails'] for p in parts
         if int(p['dest'],16)==a and 'hex' in p]
    bridge=next(p for p in parts if int(p['dest'],16)==pay+0x31000)
    br=dict(bridge=bytes.fromhex(bridge['hex']),hot=hot,syms=syms,gov=base['gov'])
    context=None
    if wizard:
        # Sample Wizard independant garde le meme ABI de passerelle que MACRO.
        # Ce contexte vient exclusivement du catalogue sample-wizard, jamais Model-TG.
        current,_=build.apply_writes(stock,[sampler])
        current=bytearray(current)
        red=gs.sprites.redirect_write(gs.gx.CAVE)
        current[red['off']:red['off']+len(bytes.fromhex(red['old']))]=bytes.fromhex(red['old'])
        ap=sampler['append'];blob=bytes.fromhex(ap['parts'][0]['hex'])
        context={k:int(v,16) for k,v in sampler['symbols'].items()}
        context.update(img=bytes(current),blob=blob,blob_at=int(ap['dest'],16),
                       at=int(ap['at'],16)+ap['size'],id='sample-wizard',symbols_hex=sampler['symbols'])
        stub=bytes.fromhex(next(p['hex'] for p in parts if int(p['dest'],16)==pay+0x32a00))
        needle=bytes.fromhex('2f032f024eb9');at=stub.index(needle)+len(needle)
        syms['voice_done']=int.from_bytes(stub[at:at+4],'big')
    with tempfile.TemporaryDirectory() as d:
        blob,rs,end=R.compile_machine(pathlib.Path(d),None,pay+0x85000,pay+0x87000)
    machines.append(dict(R.MACHINE,label='RETROSYN',update=rs['retrosyn_update'],render=rs['retrosyn_render']))
    reused=[copy.deepcopy(p) for p in parts if int(p['dest'],16)>=pay+0x42000]
    # Les dix ajouts demandent 126 descripteurs. Les rangees vont dans une
    # nouvelle zone libre ; tous les callbacks existants restent a leur place.
    original=dict(gs.LAYOUT);max_extra=gs.MAX_EXTRA;marks_row=gs.MARKS_ROW;marks=dict(gs.MARKS)
    try:
        gs.LAYOUT.update(STUBS=0x32a00,DESCN=0x33c00,ROWSN=0x84000,CCROWSN=0x84400,RECS=0x84800)
        gs.MAX_EXTRA=10;gs.set_base(pay)
        gs.MARKS_ROW=9;gs.MARKS['x']=68
        own=dict(machines=machines,bridge=br,end=end,boot2=((lay['end']+15)&~15,pay+0x42000),
                 parts=reused+[dict(dest=hex(pay+0x85000),hex=blob.hex())])
        out,_=gs.build_tweak(stock,st,codes,tg=context,own=own)
    finally:
        gs.LAYOUT.clear();gs.LAYOUT.update(original);gs.MAX_EXTRA=max_extra;gs.set_base(pay)
        gs.MARKS_ROW=marks_row;gs.MARKS.clear();gs.MARKS.update(marks)
    out.update(id='retrosyn-all-machines-wizard' if wizard else 'retrosyn-all-machines',order=29 if wizard else 28,status='experimental',requires=['sample-wizard'] if wizard else [],
               name='Syntakt, MACRO, ACID, WAVE, TINY et RETROSYN',
               description=['Six machines stock conservees, puis cinq Syntakt, MACRO, ACID, Wave, TINY et RETROSYN.',
                            'Les corps compiles existants restent identiques. Interfaces regenerees pour 16 machines.',
                            'Generateur tools/gen_retrosyn_combined.py ; notes/96. Experimental.'],
               symbols={k:hex(rs[k]) for k in ('retrosyn_update','retrosyn_render','tracks')},
               machine_names=['Kick','Snare','Metal','Perc','Tone','Chord']+(['Sampler'] if wizard else [])+[gs.CATALOG[c]['name'] for c in codes]+[m['name'] for m in machines],
               preserved_callbacks={m['name']:[hex(m['update']),hex(m['render'])] for m in machines[:-1]})
    out['conflicts']=sorted({p['id'] for f in R.DEV.glob('*.json') if f.name!='device.json'
                              and 'append' in (p:=json.loads(f.read_text())) and p['id'] not in {out['id'],'sample-wizard' if wizard else ''}} | gm.other_ids())
    # Garder les crochets propres a WAVE/TINY (pads, navigateur, etc.) qui
    # n'appartiennent pas aux interfaces communes regenerees ci-dessus.
    def intersects(a,b):
        return a['off']<b['off']+len(b['new'])//2 and b['off']<a['off']+len(a['new'])//2
    extras=[w for w in base['writes'] if not any(intersects(w,n) for n in out['writes'])]
    out['writes']=sorted(out['writes']+copy.deepcopy(extras),key=lambda w:w['off'])
    if sampler:
        for w in variant['wizard']['writes']:
            if any(intersects(w,n) for n in out['writes']):continue
            hits=[i for i,n in enumerate(sampler['writes']) if intersects(w,n)]
            if hits:
                rows=[sampler['writes'][i] for i in hits]
                lo=min([w['off']]+[x['off'] for x in rows])
                hi=max([w['off']+len(w['new'])//2]+[x['off']+len(x['new'])//2 for x in rows])
                merged=bytearray(stock[lo:hi])
                for row in rows+[w]:
                    off=row['off']-lo;merged[off:off+len(row['new'])//2]=bytes.fromhex(row['new'])
                sampler['writes']=[x for i,x in enumerate(sampler['writes']) if i not in hits]
                sampler['writes'].append(dict(off=lo,old=stock[lo:hi].hex(),new=merged.hex()))
            else:sampler['writes'].append(copy.deepcopy(w))
    rt=build.payload_runtime(out,stock,st)
    out['append']['compress_cost']=512
    out['append']['stored']=len(aplib_cost.pack(rt,depth=512,lazy=True))
    assert int(out['append']['at'],16)+out['append']['stored']<gs.END_LIMIT
    build.apply_writes(stock,([sampler] if wizard else [])+[out])
    if sampler:
        out['sampler_recipe']=sampler
    return out


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('cycles','syntakt','catalog'):ap.add_argument('--'+k,required=True)
    ap.add_argument('--check',action='store_true');ap.add_argument('--wizard',action='store_true')
    ap.add_argument('--wizard-catalog',default='firmware/wizard-catalogue.json');a=ap.parse_args()
    dev=json.loads((R.DEV/'device.json').read_text())
    assert hashlib.sha256(pathlib.Path(a.cycles).read_bytes()).hexdigest()==dev['stock_syx_sha256']
    wb=json.loads(pathlib.Path(a.wizard_catalog).read_text())['variants']['0']['wizard'] if a.wizard else None
    out=generate(g7.cycles_main(a.cycles),syntakt.dsp_image(a.syntakt),json.loads(pathlib.Path(a.catalog).read_text()),a.wizard,wb)
    path=R.DEV/f"{out['order']}-{out['id']}.json";text=json.dumps(out,indent=1,ensure_ascii=False)+'\n'
    if a.check:assert path.read_text()==text
    else:path.write_text(text,encoding='utf-8')
    print('ok',out['id'],out['append']['stored'],'octets compresses',out['machine_names'])
if __name__=='__main__':main()
