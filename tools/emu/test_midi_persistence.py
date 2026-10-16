#!/usr/bin/env python3
"""MPI1 : vrais corps ColdFire courants, FS simulee et redemarrage de l'emulateur.

python3 tools/emu/test_midi_persistence.py --case build/midi-current/supports-0
API fichier/popup/materiel simules. Aucune preuve de durabilite physique.
"""
import argparse,json,pathlib,struct,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_seq_gen_menu import Rig,RAW,OBJ,STACK,STOP
from test_sdvintage import main_os_from_syx

ROOT=HERE.parents[1]
EXT=0x46800000

def fixture(prefix,files):
    ts=json.loads(prefix.with_suffix('.json').read_text())['tweaks'];bank=next(t for t in ts if t['id']=='midi-out-bank')
    img=main_os_from_syx(str(prefix.with_suffix('.syx')))
    r=Rig(img,{'writes':[]},{'writes':[],'symbols':bank['symbols']});u=r.u
    for at,size in [(0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)]:u.mem_map(at,size)
    for part in bank['append']['parts']:
        if 'hex' in part:u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
    data=json.loads((ROOT/'docs/flasher-midi-save-current-test/midi-persistence-data.js').read_text().split('=',1)[1].rstrip(';\n'))
    origin=int(bank['symbols']['mp_api'],16)-data['symbols']['mp_api'] if 'mp_api' in bank['symbols'] else EXT
    code=bytearray.fromhex(data['hex'])
    for off in data['reloc']:struct.pack_into('>I',code,off,struct.unpack_from('>I',code,off)[0]+origin)
    original=dict(r.s);marker=bytes.fromhex('4ef9f0010096');pos=code.index(marker)
    code[pos:pos+6]=bytes.fromhex('4ef9')+struct.pack('>I',original['ml_repeat_project_hook'])
    built_module=bytes(u.mem_read(origin,len(code))) if 'mp_api' in bank['symbols'] else None
    s={k:v+origin for k,v in data['symbols'].items()};u.mem_write(origin,bytes(code));r.s.update(s)
    for i,name in enumerate(data['api']):r.w32(s['mp_api']+4*i,original.get(name,0) if name!='OLD_LOAD' else original['ml_repeat_project_hook'])
    if built_module is not None:assert built_module==bytes(u.mem_read(origin,len(code))),'module teste different du build navigateur'
    # Appels longs CRC/records : compter assez d'instructions, verifier le retour.
    def call(name,*args):
        fn=r.s[name] if isinstance(name,str) else name
        u.mem_write(STACK,struct.pack('>'+'I'*(len(args)+1),STOP,*args));u.reg_write(mk.UC_M68K_REG_A7,STACK)
        try:u.emu_start(fn,STOP,count=30_000_000)
        except Exception:
            pc=u.reg_read(mk.UC_M68K_REG_PC);near=sorted((pc-v,k) for k,v in r.s.items() if v<=pc)[:3]
            print('FAULT',hex(pc),near,'A7',hex(u.reg_read(mk.UC_M68K_REG_A7)),flush=True);raise
        assert u.reg_read(mk.UC_M68K_REG_PC)==STOP,('retour',name,hex(u.reg_read(mk.UC_M68K_REG_PC)))
        assert u.reg_read(mk.UC_M68K_REG_A7)==STACK+4,('pile',name)
        return u.reg_read(mk.UC_M68K_REG_D0)
    r.call=call
    state={'id':0x12345678,'slot':9,'pattern':0,'root':False};handles={};fault={};events=[];messages=[]
    def stub(at,fn):
        fresh=at not in r.stubs;r.stubs[at]=fn
        if fresh:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
    stub(0x400cf866,lambda a:OBJ);stub(0x4000eae2,lambda a:state['id'])
    stub(0x400802ec,lambda a:r.free.append(a[0]) or 0)
    stub(0x40044d74,lambda a:state['slot']);stub(0x400d0a10,lambda a:0x93050000)
    stub(0x4008c2c2,lambda a:6);stub(0x4008c324,lambda a:state.get('saved_id',state['id']))
    stub(original['TG_show_popup'],lambda a:messages.append(r.string(a[0])) or 0)
    stub(original['ml_active_pattern_id'],lambda a:state['pattern'])
    def lookup(a):
        parent,name,out=a[:3];name=r.string(name);events.append(('lookup',name))
        if name=='ModdedCycles':
            if not state['root'] and not files:return 0
            u.mem_write(out,struct.pack('>IH',20,1));return 1
        if fault.get('lookup'):return -1
        if '/ModdedCycles/'+name not in files:return 0
        u.mem_write(out,struct.pack('>IH',30,0));return 1
    def mkdir(a):state['root']=True;events.append(('mkdir',r.string(a[0])));return 0
    def opened(a):
        path,mode,handle=a[:3];path=r.string(path);mode=r.string(mode);events.append(('open',mode,path))
        if fault.get('open'):return -1
        if mode=='r' and path not in files:return -1
        if mode=='w':files[path]=bytearray()
        handles[handle]=[path,mode,0];u.mem_write(handle,struct.pack('>4I',30,0,int(mode=='w'),1));return 0
    def prealloc(a):
        handle,offset,count=a[:3];assert offset==0 and count==14304
        if fault.get('alloc'):return -1
        files[handles[handle][0]]=bytearray(count);return 0
    def write(a):
        src,count,handle=a[:3];assert count<=512;h=handles[handle]
        if fault.get('write'):return 0
        if fault.get('change'):r.w32(s['mp_serial'],r.r32(s['mp_serial'])+1);fault.pop('change');return 0
        n=min(count,fault.get('partial',count));files[h[0]][h[2]:h[2]+n]=u.mem_read(src,n);h[2]+=n;return n
    def read(a):
        dst,count,handle=a[:3];assert count<=512;h=handles[handle];raw=files[h[0]][h[2]:h[2]+count]
        if fault.get('read'):return -1
        if fault.get('corrupt') and raw:raw=bytearray(raw);raw[-1]^=1
        u.mem_write(dst,bytes(raw));h[2]+=len(raw);return len(raw)
    def close(a):handles.pop(a[0]);return -1 if fault.get('close') else 0
    stub(0x4007ad86,lookup);stub(0x4007ac46,mkdir);stub(0x4007bc5e,opened)
    stub(0x4007bb76,prealloc);stub(0x4007bb0a,write);stub(0x4007baaa,read)
    stub(0x4007bc1c,close);stub(0x4007e2f6,lambda a:-1 if fault.get('flush') else 0)
    # Le Save A reste silencieux si B n'a jamais ete ouvert.
    r.call('mp_save_enter');r.call('mp_save_finish',OBJ,9)
    assert not events and not messages
    assert r.call('ml_prepare')==1
    # Seul le boot/UI simulé établit le propriétaire : aucun fichier au constructeur.
    r.call('mp_ui');assert r.r32(s['mp_owner'])==state['id']
    r.call('ml_bank_ui_sync');r.call('mlcc_prepare');r.call('ml_repeat_prepare_ui')
    r.handles=handles
    r.persistence_stub=stub
    return r,state,fault,events,messages

def musical(r):
    table=r.r32(r.s['ml_bank_table']);bank=r.r32(table)
    repeat=r.call('ml_repeat_pattern_prepare',bank);locks=r.call('mlkc_locks_for',bank,1)
    lfo=r.r32(r.s['mlcc_settings']);assert all((bank,repeat,locks,lfo))
    return bank,repeat,locks,lfo

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',required=True);a=p.parse_args();prefix=pathlib.Path(a.case)
    files={};r,state,fault,events,messages=fixture(prefix,files)
    bank,repeat,locks,lfo=musical(r)
    r.u.mem_write(bank+8,bytes((67,110,4,65)));r.u.mem_write(repeat+2,b'\x25')
    assert r.call('mlkc_lock_set',locks,5,63,11,74,119)==1
    r.u.mem_write(r.s['mlkc_state'],b'\x4a\x40');r.u.mem_write(lfo+6,b'\x00\x4a')
    expected=[bytes(r.u.mem_read(at,n)) for at,n in ((bank,1584),(repeat,3120),(locks,9216),(r.s['mlkc_state'],144),(lfo,192))]
    # Formats : validation et CRC aussi executes depuis le corps cible reloge.
    payload=0x93060000;record=payload+16000
    r.u.mem_write(payload,b''.join(expected));assert r.call('mp_values',payload)==1
    assert r.call('mp_encode',record,payload,state['id'],9,0,0xffffffff)==1
    assert r.call('mp_decode',record,state['id'],9,0)==1
    for off in (0,12,44,48,48+1584+3120,14303):
        old=bytes(r.u.mem_read(record+off,1));r.u.mem_write(record+off,bytes([old[0]^1]))
        assert r.call('mp_decode',record,state['id'],9,0)==0
        r.u.mem_write(record+off,old)
    print('PASS codec ColdFire : notes live, retrigger/chance, locks CC, mappings et deux LFO ; corruption totale refusee',flush=True)
    def save():r.call('mp_save_enter');r.call('mp_save_finish',OBJ,9)
    save();assert messages[-1]=='MIDI SAVED',messages
    assert len(files)==1 and not r.handles
    print('PASS premier Save natif annexe, 14304 octets, fichier A relu et valide',flush=True)
    fault['partial']=127;save();assert messages[-1]=='MIDI SAVED';assert len(files)==2;fault.clear()
    original={k:bytes(v) for k,v in files.items()}
    for failure in ('write','alloc','flush','close','corrupt','read','lookup','open','change'):
        files.clear();files.update({k:bytearray(v) for k,v in original.items()});fault[failure]=1;save()
        assert messages[-1].startswith('MIDI SAVE E'),(failure,messages[-1]);assert not r.handles;fault.clear()
        assert any(bytes(files[k])==v for k,v in original.items()),failure
    files.clear();files.update({k:bytearray(v) for k,v in original.items()})
    print('PASS ecritures partielles ; write/alloc/flush/close/readback/lookup/open echoues sans perdre les deux copies',flush=True)
    # Redemarrage reel : nouvelle RAM, seuls les fichiers subsistent.
    r2,st2,f2,e2,m2=fixture(prefix,files);got=musical(r2)
    restored=[bytes(r2.u.mem_read(at,n)) for at,n in ((got[0],1584),(got[1],3120),(got[2],9216),(r2.s['mlkc_state'],144),(got[3],192))]
    assert restored==expected
    print('PASS redemarrage emulateur : toutes donnees musicales restaurees depuis fichiers',flush=True)
    # Regression materielle : Load renouvelle l'UUID live apres conversion.
    st2['saved_id']=st2['id'];r2.call('mp_load_notice',st2['saved_id'],9)
    st2['id']=0x34567890;r2.call('mp_ui');r2.call('ml_bank_ui_sync')
    assert bytes(r2.u.mem_read(musical(r2)[0],1584))==expected[0]
    assert r2.r32(r2.s['mp_owner'])==st2['id'] and r2.r32(r2.s['mp_key'])==st2['saved_id']
    r2.call('mp_ui');assert bytes(r2.u.mem_read(musical(r2)[0],1584))==expected[0]
    # Working96 au boot : la fiche disque garde l'ancienne identite.
    r2.call('mp_load_notice',st2['id'],96);st2['id']=0x45678901
    r2.call('mp_ui');r2.call('ml_bank_ui_sync')
    assert bytes(r2.u.mem_read(musical(r2)[0],1584))==expected[0]
    print('PASS Load UUID live renouvele et working96 : cle sauvegardee stable, B restauree et conservee aux drains suivants',flush=True)
    # La plus recente est corrompue : revenir a l'autre copie valide.
    files[next(k for k in files if k.endswith('-B'))][-1]^=1
    r3,st3,f3,e3,m3=fixture(prefix,files);assert bytes(r3.u.mem_read(musical(r3)[0],1584))==expected[0]
    print('PASS recuperation A apres corruption B',flush=True)
    damaged={k:bytearray(v) for k,v in files.items()}
    for v in damaged.values():v[-1]^=2
    bad,bs,bf,be,bm=fixture(prefix,damaged);assert bm[-1].startswith('MIDI LOAD E')
    count=len(be);bad.call('mp_save_enter');bad.call('mp_save_finish',OBJ,9)
    assert bm[-1]=='MIDI SAVE E23' and not any(e[0]=='open' and e[1]=='w' for e in be[count:])
    print('PASS deux copies invalides : aucun Save ne remplace silencieusement les fichiers',flush=True)
    # Projet distinct : aucune donnee de l'ancien projet ne doit etre adoptee.
    st3['id']=0x87654321;r3.call('mp_load_notice',st3['id'],st3['slot']);r3.call('mp_ui');r3.call('ml_bank_ui_sync')
    assert bytes(r3.u.mem_read(musical(r3)[0]+8,4))==bytes((60,100,1,0))
    assert bytes(r3.u.mem_read(r3.s['mlkc_state'],144))==b'\xff\x40'*72
    print('PASS changement de projet : notes, CC et LFO precedents retires sans sauvegarde croisee',flush=True)
    st3['id']=0;r3.call('mp_load_notice',0,96);r3.call('mp_ui');r3.call('ml_bank_ui_sync')
    new_bank=musical(r3)[0];assert r3.call('ml_edit',new_bank,0,0,0,72)==1
    r3.call('mp_save_enter');st3['id']=0x23456789;r3.call('mp_save_finish',OBJ,9)
    assert m3[-1]=='MIDI SAVED',m3
    print('PASS projet neuf non sauvegarde : edition RAM possible, premier Save adopte seulement identite native confirmee',flush=True)
    for ipl in range(1,8):
        count=len(events);r.u.reg_write(mk.UC_M68K_REG_SR,0x2000|(ipl<<8));r.call('mp_ui');r.call('mp_save_enter');r.call('mp_save_finish',OBJ,9);assert len(events)==count
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2000);r.w32(0x40a7883c,1);count=len(events);save();assert messages[-1]=='STOP TO SAVE MIDI' and len(events)==count
    r.w32(0x40a7883c,0)
    print('PASS IPL1..7 et transport en lecture : aucune E/S fichier',flush=True)
    if 'mp_api' in next(t for t in json.loads(prefix.with_suffix('.json').read_text())['tweaks'] if t['id']=='midi-out-bank')['symbols']:
        # Vrai Save Project natif, avec uniquement cache/conversion/FS simules.
        state['pattern']=0;cache,serialized,callback=0x93010000,0x41400000,0x93012000
        r.u.mem_write(callback,bytes(16));native={'save':1}
        for at,fn in ((0x400cfdaa,lambda a:cache),(0x4006a216,lambda a:serialized),(0x4005d18a,lambda a:1),(0x4006a4d6,lambda a:native['save']),(0x400d0aae,lambda a:0),(0x400cf044,lambda a:0)):r.persistence_stub(at,fn)
        fault.clear();files.clear();before=len(messages)
        assert r.call(0x4000f762,OBJ,9,callback)&255==1
        assert messages[-1]=='MIDI SAVED' and len(messages)==before+1
        native['save']=0;count=len(events);before=len(messages)
        assert r.call(0x4000f762,OBJ,9,callback)&255==0
        assert len(events)==count and messages[before:]==['MIDI: SAVE A FAILED']
        assert r.r32(r.s['mp_saving'])==0
        print('PASS vrai Save Project natif : detours entree/epilogue, resultat et pile conserves ; aucun sidecar apres echec A',flush=True)
        dest=0x93011000;loaded={'ok':1}
        def convert(a):r.w32(a[0]+8,state['id']);return loaded['ok']
        r.persistence_stub(0x4006a3ac,lambda a:serialized);r.persistence_stub(0x4005d3dc,convert)
        serial=r.r32(r.s['mp_serial']);count=len(events)
        assert r.call(0x4006a5a0,cache,9,dest,callback)==1
        assert r.r32(r.s['mp_serial'])==serial+1 and r.r32(r.s['ml_bank_table'])==0
        assert len(events)==count
        r.call('mp_ui');assert r.r32(r.s['ml_bank_table'])!=0
        loaded['ok']=0;serial=r.r32(r.s['mp_serial']);count=len(events)
        assert r.call(0x4006a5a0,cache,9,dest,callback)==0
        assert r.r32(r.s['mp_serial'])==serial and len(events)==count
        print('PASS vrai Load Project natif : slot/identite transmis, retrait immediat de B sans E/S, restauration UI ; echec A inerte',flush=True)
        # Save Project vers destination vide : callbacks UI pendant le Save.
        fresh={};rs,ss,fs,es,ms=fixture(prefix,fresh)
        bs=musical(rs)[0];rs.u.mem_write(bs+8,bytes((73,111,3,1)))
        ss['slot']=10;ss['saved_id']=0
        rs.u.mem_write(callback,bytes(16))
        for at,fn in ((0x400cfdaa,lambda a:cache),(0x4006a216,lambda a:serialized),(0x4005d18a,lambda a:1),(0x4006a4d6,lambda a:1),(0x400d0aae,lambda a:0),(0x400cf044,lambda a:0)):rs.persistence_stub(at,fn)
        # La garde est verifiee avec la vraie fonction de drain pendant les
        # deux etats des metadonnees d'un slot nouvellement cree.
        rs.call('mp_save_enter');count=len(es)
        rs.call('mp_ui');assert len(es)==count and rs.r32(rs.s['ml_bank_table'])!=0
        ss['saved_id']=ss['id'];rs.call('mp_ui')
        assert bytes(rs.u.mem_read(bs+8,4))==bytes((73,111,3,1)) and len(es)==count
        rs.call('mp_save_result',OBJ,10,1)
        assert ms[-1]=='MIDI SAVED' and any('MPI1-10-' in k for k in fresh)
        # La vraie entree/sortie native fonctionne egalement sur ce slot neuf.
        assert rs.call(0x4000f762,OBJ,10,callback)&255==1 and ms[-1]=='MIDI SAVED'
        rs.call('mp_load_notice',ss['saved_id'],10);ss['id']=0x56789012
        rs.call('mp_ui');rs.call('ml_bank_ui_sync')
        assert bytes(rs.u.mem_read(musical(rs)[0]+8,4))==bytes((73,111,3,1))
        print('PASS Save Project destination vide : garde UI avant/apres creation fiche, hooks natifs, rechargement B sous UUID renouvele',flush=True)
    print('LIMITES : backend fichier et objets OS simules ; persistance physique non prouvee')

if __name__=='__main__':main()
