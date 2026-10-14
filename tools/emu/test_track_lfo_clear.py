#!/usr/bin/env python3
"""Clear/Undo A : vraies routines OS, record partagé, son et phases sélectionnés.

Getters d'objets et frontières d'affichage/notification simulés ; clear, Undo,
RTTI, copie, allocation des records et comptage shared_ptr s'exécutent dans l'OS.
--cycles OS1.13 --catalog work/integration-catalog.json --tweak work/a-clear-lfo-undo.json
"""
import argparse
import json
import pathlib
import random
import struct

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

import build
import test_arp as ta
import test_lfo_plus as codec
from test_sdvintage import main_os_from_syx

REGS = tuple(getattr(mk, 'UC_M68K_REG_'+k) for k in
             ['D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6'])
DEFAULT1=struct.pack('>8H',0x7000,0x400,0x4000,0,0,0,0,0x4000)
DEFAULT2=struct.pack('>5H',0x7000,0x400,0,0,0x4000)
DEFAULTR=struct.pack('>8H',0x7000,0x400,0x4000,0x7f00,0,0,0,0x4000)


class Fixture(ta.Emu):
    def __init__(self, image, tweak, catalog, context=True):
        self.custom={};self.notices=[];self.native_returns=[];self.notify_action=None
        super().__init__(image)
        self.uc.mem_write(build.BASE,image)
        self.s={k:int(v,16) for k,v in tweak['symbols'].items()}
        self.imp={k:int(v,16) for k,v in tweak['imports'].items()}
        self.uc.mem_write(int(tweak['raw']['dest'],16),bytes.fromhex(tweak['raw']['hex']))
        self.tracks=[ta.Track(self,0x93400000+i*0x10000) for i in range(6)]
        self.pool=ta.Track(self,0x93300000)
        self.ctx=0x93800000 if context else 0
        self.owner=0x93700000;self.root=0x93110000;self.sound_owner=0x93110100
        self.sel=0;self.sound_ptr_shift=0
        self.sounds=[0x93120000+0x1000*i for i in range(6)]
        self.sound_objs=[0x93130000+0x1000*i for i in range(6)]
        self.access=0x93140000
        self.custom[0x400cf866]=lambda a:self.root
        self.custom[0x4000eb9c]=lambda a:self.sound_owner
        self.custom[0x400097f0]=self.get_access
        self.custom[0x400cf9a8]=lambda a:0x93170000
        self.custom[0x4006b978]=lambda a:1
        self.custom[0x4000f23e]=lambda a:self.tracks[self.sel].obj
        self.custom[0x4006bbd8]=lambda a:0
        # Frontières popup uniquement : le vrai sélecteur clear/Undo est exécuté.
        for p in (0x400f980c,0x400747c0,0x40076220,0x400f7d5c):
            self.custom[p]=lambda a:0
        self.w32(0x40fe4218,0x93171000)
        self.w32(self.imp['A_LF2_context'],self.ctx)
        self.w32(self.imp['A_LF2_epoch'],23)
        self.w32(self.imp['A_audio_owner'],self.owner)
        rnd=random.Random(87)
        for i,tr in enumerate(self.tracks):
            self.w32(tr.obj+44,self.pool.obj);self.w32(tr.obj+56,i);self.w32(tr.obj+60,0)
            data=bytearray(rnd.randrange(256) for _ in range(722))
            struct.pack_into('>H',data,713,16)
            self.uc.mem_write(tr.data,bytes(data))
            p=bytearray(b'\xff'*4352+bytes(33))
            struct.pack_into('>H',p,68*3,0x2100+i*128)
            struct.pack_into('>H',p,68*11+4,0x3700-i*128)
            p[4352]=10;p[4354]=12
            self.uc.mem_write(self.pool.data+4385*i,bytes(p))
            obj,vt,getter,notify=self.sound_objs[i],0x93150000+0x1000*i,0x93160000+0x100*i,0x93160010+0x100*i
            self.w32(obj,vt);self.w32(vt+40,getter);self.w32(vt+16,notify)
            self.custom[getter]=lambda a,i=i:self.sounds[i]+self.sound_ptr_shift
            self.custom[notify]=lambda a,i=i:self.notice(i,a)
            snd=bytearray(codec.sound_bytes(rnd,[0x5a80+i*128,0xb00,0x300,0xe00,0x2380]))
            struct.pack_into('>8H',snd,22,0x3180,0x900,0x1280,0xc00,0x500,0x1480,0x300,0x2800)
            self.uc.mem_write(self.sounds[i],bytes(snd))
            self.uc.mem_write(0x40fde838+32*i,bytes(0x11+i+j for j in range(32)))
            cfg=struct.pack('>8H',0x5a80+i*128,0xb00,0x1280,0xe00,0x300,0x1480,0x300,0x2380)
            self.uc.mem_write(self.owner+4896+16*i,cfg)
            if self.ctx:
                self.uc.mem_write(self.ctx+32*i,bytes(0x41+i+j for j in range(32)))
                self.uc.mem_write(self.ctx+192+16*i,cfg)
        self.uc.reg_write(mk.UC_M68K_REG_SR,0x2000)

    def _hook(self,uc,addr,size,ud):
        if addr in (0x40019702,0x40018dca):
            self.native_returns.append((addr,uc.reg_read(mk.UC_M68K_REG_D0),uc.reg_read(mk.UC_M68K_REG_SR)))
        if addr in self.custom:
            sp=uc.reg_read(mk.UC_M68K_REG_A7)
            args=struct.unpack('>8I',uc.mem_read(sp+4,32))
            result=self.custom[addr](args)
            if result is not None:self._pop(uc,result)
            return
        super()._hook(uc,addr,size,ud)

    def get_access(self,args):
        assert args[:2]==(self.sound_owner,args[1]) and 0<=args[1]<6,args
        self.w32(self.access+4,self.sound_objs[args[1]]);return self.access

    def notice(self,lane,args):
        assert args[0]==self.sound_objs[lane]
        assert self.r32(args[1])==0x400fd0ac
        assert self.uc.reg_read(mk.UC_M68K_REG_SR)&0x700==0
        self.notices.append((lane,self.r32(args[1]+4)))
        if self.notify_action:
            return self.notify_action(self)
        return 0

    def observing_setter(self,pair):
        """Observateur simulé -> vrai setter shared_ptr OS, sans appel Unicorn imbriqué."""
        # Comme une callback de son, ce trampoline remplace/retire le record.
        # L'exécution continue nativement avec la pile et le return de notify.
        trampoline=0x93602000
        code=(bytes.fromhex('487800014879')+struct.pack('>I',pair)+
              bytes.fromhex('2f3940fe41d84eb94006e0e64fef000c4e75'))
        self.uc.mem_write(trampoline,code)
        self.uc.reg_write(mk.UC_M68K_REG_PC,trampoline)
        return None

    def rd(self,address,n):return bytes(self.uc.mem_read(address,n))

    def all_state(self):
        return dict(seq=[self.rd(t.data,722) for t in self.tracks],
                    pool=self.rd(self.pool.data,4385*6),
                    sound=[self.rd(x,100) for x in self.sounds],
                    phase1=self.rd(0x40fde838,192),
                    phase2=self.rd(self.ctx,192) if self.ctx else None,
                    cfg=self.rd(self.ctx+192,96) if self.ctx else None,
                    owner=self.rd(self.owner+4896,96))

    def invoke(self,fn,*args,sr=0x2000):
        expected={r:0x5a110000+i*256 for i,r in enumerate(REGS)}
        for r,v in expected.items():self.uc.reg_write(r,v)
        self.uc.reg_write(mk.UC_M68K_REG_SR,sr)
        result=self.call(fn,*args)
        assert all(self.uc.reg_read(r)==v for r,v in expected.items()),'ABI callee-saved'
        assert self.uc.reg_read(mk.UC_M68K_REG_A7)==ta.t7.STACK-0x400+4,'pile'
        if fn in (self.s['avcl_clear'],self.s['avcl_undo']):
            assert result==self.native_returns[-1][1], 'D0 natif intégral'
            # Unicorn expose parfois des CCR paresseux au hook RTS ; MOVE SR
            # dans le code les matérialise. d1 contient ce SR réellement relu.
            assert self.uc.reg_read(mk.UC_M68K_REG_SR)==self.uc.reg_read(mk.UC_M68K_REG_D1)&0xffff,'SR natif matérialisé'
        assert not self.bad,self.bad
        return result&255

    def clear(self,lane):return self.invoke(self.s['avcl_clear'],self.tracks[lane].obj,1)
    def undo(self,lane):return self.invoke(self.s['avcl_undo'],self.tracks[lane].obj,1)
    def ui(self,lane):
        self.sel=lane;return self.invoke(0x40021bf0,0x93172000)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True)
    ap.add_argument('--catalog',required=True);ap.add_argument('--tweak',required=True)
    ap.add_argument('--integrated',action='store_true',help='hooks et RAW A déjà intégrés dans le catalogue')
    a=ap.parse_args()
    stock=main_os_from_syx(a.cycles);cat=json.loads(pathlib.Path(a.catalog).read_text())
    tweak=json.loads(pathlib.Path(a.tweak).read_text());baseline=build.apply_writes(stock,cat['tweaks'])[0]
    # Charger les propres runtimes natifs TG et B comme après boot ; le banc
    # historique tronque sinon l'image à la taille officielle. Pas de DSP Syntakt
    # exécuté par ces chemins UI/codec, aucune copie de son OS n'est nécessaire.
    full=bytearray(baseline)
    for t in cat['tweaks']:
        ap=t.get('append')
        if not ap or ap.get('syntakt'):continue
        raw=build.payload_runtime(t,stock,None);off=int(ap['dest'],16)-build.BASE
        if len(full)<off+len(raw):full.extend(bytes(off+len(raw)-len(full)))
        full[off:off+len(raw)]=raw
    baseline=bytes(full)
    if a.integrated:
        for w in tweak['writes']:
            off=w['off'];new=bytes.fromhex(w['new'])
            assert baseline[off:off+len(new)]==new,'hook A intégré différent'
        off=int(tweak['raw']['dest'],16)-build.BASE;own=bytes.fromhex(tweak['raw']['hex'])
        assert baseline[off:off+len(own)]==own,'RAW A intégré différent'
        patched=baseline;native=bytearray(baseline)
        for w in tweak['writes']:native[w['off']:w['off']+len(bytes.fromhex(w['old']))]=bytes.fromhex(w['old'])
        baseline=bytes(native)
    else:
        patched=build.apply_writes(baseline,[tweak])[0]
    def fresh(context=True):return Fixture(patched,tweak,cat,context)
    for lane in range(6):
        r=fresh();before=r.all_state()
        native=Fixture(baseline,tweak,cat);assert native.ui(lane)==1
        native_clear=native.all_state()
        assert native_clear['sound']==before['sound'] and native_clear['cfg']==before['cfg']
        assert r.ui(lane)==1
        after=r.all_state();snd=after['sound'][lane]
        assert after['seq']==native_clear['seq'] and after['pool']==native_clear['pool']
        assert snd[22:38]==DEFAULT1 and snd[76:86]==DEFAULT2
        assert snd[:22]+snd[38:76]+snd[86:]==before['sound'][lane][:22]+before['sound'][lane][38:76]+before['sound'][lane][86:]
        assert after['cfg'][lane*16:lane*16+16]==DEFAULTR
        assert after['owner'][lane*16:lane*16+16]==DEFAULTR
        for key in ('phase1','phase2'):assert after[key][32*lane:32*lane+32]==bytes(32)
        for other in range(6):
            if other==lane:continue
            assert after['seq'][other]==before['seq'][other]
            assert after['sound'][other]==before['sound'][other]
            for key,stride in [('pool',4385),('phase1',32),('phase2',32),('cfg',16),('owner',16)]:
                assert after[key][stride*other:stride*(other+1)]==before[key][stride*other:stride*(other+1)],key
        assert r.notices==[(lane,k) for k in list(range(1,9))+list(range(28,33))]
        state=r.s['avcl_state'];manager=r.r32(0x40fe41d8)
        assert r.r32(state)==1 and r.r32(state+36)==r.r32(manager+12)
        assert r.r32(state+40)==r.r32(manager+16)
        control=r.r32(state+40);assert r.r32(control+4)==2,'manager + snapshot'
        assert r.ui(lane)==1
        assert r.all_state()==before,'Undo séquence+locks+LFO+phases exact'
        assert r.r32(state)==0 and r.r32(state+40)==0
        assert r.r32(control+4)==1,'snapshot libéré, record seulement détenu par manager'
        print(f'ok : vrais deux sites UI, A{lane+1} clear/Undo séquence722 + pool4385, deux LFO/phases, cinq voisines intactes')
    print('ok : D0/SR natifs, pile et onze registres callee-saved gardés sur chaque chemin')
    r=fresh();before=r.all_state();assert r.clear(2)==1
    # Sauvegarde native du son : valeurs modifiées présentes dans le codec existant.
    sound=codec.Rig(patched,[]);sound.uc.mem_write(build.BASE,patched);sound.uc.mem_write(codec.SOUND,r.rd(r.sounds[2],100))
    try:
        assert sound.call(codec.SND_SAVE2,codec.REC,codec.SOUND)&255==1
    except Exception:
        print('codec PC',hex(sound.uc.reg_read(mk.UC_M68K_REG_PC)),sound.bad);raise
    assert int.from_bytes(sound.rd(codec.REC+88,4),'big')==codec.packed(list(struct.unpack('>5H',DEFAULT2)))
    assert r.undo(2)==1
    sound.uc.mem_write(codec.SOUND,r.rd(r.sounds[2],100));sound.call(codec.SND_SAVE2,codec.REC,codec.SOUND)
    assert int.from_bytes(sound.rd(codec.REC+88,4),'big')==codec.packed(list(struct.unpack('>5H',before['sound'][2][76:86])))
    print('ok : cinq champs LFO2 du vrai son se sauvegardent aux défauts puis aux valeurs Undo ; extras RAM indépendants')
    r=fresh(False);before=r.all_state();assert r.clear(1)==1;assert r.undo(1)==1
    assert r.all_state()==before
    print('ok : contexte LFO2 nul, aucun accès nul ni allocation secondaire, son natif/phase1 Undo exacts')
    for reason,sr,kind in [('IPL7',0x2700,1),('kind hors contrat UI',0x2000,0)]:
        r=fresh();before=r.all_state();assert r.invoke(r.s['avcl_clear'],r.tracks[1].obj,kind,sr=sr)==1
        after=r.all_state()
        for key in ('sound','phase1','phase2','cfg','owner'):assert before[key]==after[key],reason
        assert not r.notices and r.r32(r.s['avcl_state'])==0
        print('ok : garde '+reason+', aucun setter/notification LFO ajouté au chemin natif')
    r=fresh();before=r.all_state()
    r.custom[r.tracks[1].f4]=lambda a:r.w32(r.imp['A_LF2_epoch'],24) or 0
    assert r.clear(1)==1
    assert r.all_state()['sound']==before['sound'] and not r.notices
    print('ok : Load notifié pendant le clear natif, identités revérifiées avant mutation LFO')
    # Invalidation des identités, sans jamais toucher à nouveau aux LFO.
    for reason,mutate in [
        ('projet',lambda r:setattr(r,'root',r.root+4)),
        ('son remplacé',lambda r:setattr(r,'sound_ptr_shift',128)),
        ('epoch Load',lambda r:r.w32(r.imp['A_LF2_epoch'],24)),
        ('owner pattern',lambda r:r.w32(r.imp['A_audio_owner'],r.owner+0x10000)),
        ('contexte LFO',lambda r:r.w32(r.imp['A_LF2_context'],r.ctx+0x10000)),
        ('raw piste',lambda r:r.custom.__setitem__(r.tracks[2].f10,lambda a:r.tracks[2].data+0x1000)),
    ]:
        r=fresh();assert r.clear(2)==1;mutate(r);snd=r.rd(r.sounds[2],100);notices=len(r.notices)
        r.undo(2)
        assert r.rd(r.sounds[2],100)==snd and len(r.notices)==notices,reason
        assert r.r32(r.s['avcl_state'])==0,reason
        print('ok : garde Undo périmé — '+reason)
    r=fresh();assert r.clear(2)==1;assert r.clear(3)==1
    snd=r.rd(r.sounds[2],100);r.undo(2)
    assert r.rd(r.sounds[2],100)==snd
    print('ok : record remplacé par clear d’une autre piste, aucune restauration LFO stale')
    r=fresh();assert r.clear(2)==1;state=r.rd(r.s['avcl_state'],156)
    r.custom[r.tracks[3].f10]=lambda a:0
    assert r.clear(3)==0 and r.rd(r.s['avcl_state'],156)==state
    assert r.undo(2)==1
    print('ok : clear natif refusé garde le record/snapshot précédent et son Undo fonctionne')
    r=fresh();assert r.clear(5)==1;manager=r.r32(0x40fe41d8);pair=0x93601000
    r.w32(pair,r.r32(manager+12));r.invoke(0x400cfae0,pair+4,manager+16)
    assert r.clear(2)==1
    original_record=r.r32(manager+12);r.w32(pair,original_record)
    r.invoke(0x4006e0e6,manager,pair,1)
    snd=r.rd(r.sounds[2],100);notices=len(r.notices)
    assert r.undo(2)==1 and r.rd(r.sounds[2],100)==snd and len(r.notices)==notices
    assert r.r32(r.s['avcl_state'])==0
    print('ok : même adresse record avec un autre control block, Undo LFO refusé indépendamment du pointeur objet')
    # Les vrais setters/retains/releases s'exécutent dans les observateurs.
    r=fresh();before=r.all_state();empty=0x93601000;r.uc.mem_write(empty,bytes(8))
    r.notify_action=lambda r:r.observing_setter(empty)
    assert r.clear(4)==1
    state=r.s['avcl_state'];manager=r.r32(0x40fe41d8)
    assert r.r32(state)==1 and r.r32(state+36)==r.r32(manager+12)
    assert r.r32(r.r32(state+40)+4)==2
    assert r.undo(4)==1 and r.all_state()==before
    print('ok : observateurs son vident réellement le record natif ; strong ref gardée, record republié, Undo exact')
    r=fresh();assert r.clear(5)==1;manager=r.r32(0x40fe41d8);pair=0x93601000
    r.w32(pair,r.r32(manager+12));r.invoke(0x400cfae0,pair+4,manager+16)
    r.notify_action=lambda r:r.observing_setter(pair)
    assert r.clear(2)==1
    assert r.r32(manager+12)==r.r32(pair) and r.r32(manager+16)==r.r32(pair+4)
    assert r.r32(r.s['avcl_state'])==0 and r.r32(r.s['avcl_state']+40)==0
    print('ok : un observateur publie un autre record ; aucune republication ni Undo LFO périmé, ref privée libérée')
    r=fresh();before=r.all_state()
    # Un observer appelle à nouveau le clear A : l'adapter nested est natif,
    # aucune cellule globale n'est réécrite pendant le premier apply.
    def nested(r):
        r.notify_action=None
        trampoline=0x93603000
        r.uc.mem_write(trampoline,bytes.fromhex('487800014879')+struct.pack('>I',r.tracks[5].obj)+
                       b'\x4e\xb9'+struct.pack('>I',r.s['avcl_clear'])+bytes.fromhex('508f4e75'))
        r.uc.reg_write(mk.UC_M68K_REG_PC,trampoline)
        return None
    r.notify_action=nested
    assert r.clear(2)==1 and r.r32(r.s['avcl_busy'])==0
    assert r.rd(r.sounds[5],100)==before['sound'][5]
    assert r.r32(r.s['avcl_state'])==0
    print('ok : clear réentrant depuis observer, chemin natif sans écraser snapshot privé ni LFO voisin')
    print('Limite : matériel non testé ; frontières getter/affichage/observateurs simulées, E/S disque absentes.')


if __name__=='__main__':main()
