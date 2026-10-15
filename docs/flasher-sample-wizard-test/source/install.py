"""Recette privée Sample Wizard : liste positive des seuls raccords sampler.

Ne réutilise pas le build TG complet : pas de mutes, Scale Lock, slides,
profilage, FX master ni optimisations des six machines stock.
"""
import copy,json,pathlib,struct,hashlib
import build,ref_mainos
from chord_keys_pr87 import load_stock
p=pathlib.Path('work/supermodel-sampler-prototype');stock=load_stock('firmware/model-cycles_OS1.13.syx')
assert hashlib.sha256(stock).hexdigest()=='cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98'
t=copy.deepcopy(json.load(open(p/'varispeed.json')));s={k:int(v,16) for k,v in t['symbols'].items()};manifest=[]
def add(at,new,why,old=None):
 off=at-build.BASE;previous=stock[off:off+len(new)]
 if old is not None:assert previous.hex()==old,(hex(at),previous.hex(),old)
 t['writes'].append(dict(off=off,old=previous.hex(),new=new.hex()));manifest.append(dict(at=hex(at),size=len(new),purpose=why))
def ptr(at,name,why):add(at,struct.pack('>I',s[name]),why)
def jump(at,name,why,nops=0):add(at,b'\x4e\xf9'+struct.pack('>I',s[name])+b'\x4e\x71'*nops,why)
def call(at,name,why,nops=0):add(at,b'\x4e\xb9'+struct.pack('>I',s[name])+b'\x4e\x71'*nops,why)
call(0x40000530,'boot_extra_hook','boot : BSS et tampon filesystem préservés')
for at,old,new in [(0x400147a5,'05','06'),(0x400148ab,'05','06'),(0x400148b3,'05','06'),(0x4001bbd3,'18','1c'),(0x4001bbe5,'18','1c'),(0x4001bbf3,'18','1c'),(0x4005a79d,'05','06'),(0x400a25e1,'05','06'),(0x400a26e9,'06','07'),(0x400a7df5,'05','06'),(0x4010e5e6,'05','06')]:add(at,bytes.fromhex(new),'septième machine uniquement',old)
add(0x400a2615,struct.pack('>I',s['sampler_name_table'])[1:],'noms des sept machines','1177e4')
add(0x40117931,struct.pack('>I',s['sampler_lazy_init_trampoline'])[1:],'icônes des sept machines','0a24ca')
ptr(0x4001bbe8,'page_machine_list','liste des machines')
jump(0x4004df5c,'descr_hook','descripteur sampler / stock inchangé')
jump(0x4004df76,'descr_b_hook','descripteur sampler / LED paramètres')
jump(0x400a7da8,'sampler_pre','prétraitement sampler, chemin natif stock',1)
jump(0x400a7e02,'sampler_dispatch','rendu sampler, chemin natif stock',12)
jump(0x4008171e,'pad_load_hook','rejeu prologue note-on')
ptr(0x400fd148,'fine_hook','Start/End fins sur sampler seulement')
jump(0x4001413e,'mc_commit_hook','valeurs par défaut sampler')
call(0x400081ce,'gm_enc_gate','encodeur menu sampler, fallback natif')
for at in [0x400a2790,0x400a2834]:ptr(at,'restore_hook','restauration machine sauf sampler')
for at,name in [(0x4005a6a6,'sampler_lfo_gate'),(0x4005a6b6,'sampler_amp_gate'),(0x4005a6d0,'sampler_com_gate')]:jump(at,name,'paramètres LFO sampler bornés')
for at,name in [(0x4005afa0,'snd_save2_hook'),(0x4005b054,'snd_save1_hook'),(0x4005aecc,'snd_load_hook')]:jump(at,name,'codec son : état sampler uniquement')
# Attack interne : aucun nouveau contrôle/destination LFO sur les machines stock.
add(0x4010dce0+13*56,struct.pack('>14I',7,23,0,32512,0,0,0xffffffff,0xffffffff,0,0,35,s['str_attack'],0x40129882,s['str_atk']),'Attack du descripteur sampler, invisible dans les listes stock')
ptr(0x401005bc,'wf_popup','forme onde Start/End sampler, fallback natif')
call(0x40059872,'rs_out','sortie native et horloge / capture sampler')
jump(0x40056610,'sx_mix','stéréo sampler sans FX TG',1)
call(0x4005982a,'sx_gain','gain side sampler sans retrig TG')
for at,name in [(0x40084b8e,'id_hook'),(0x40084c14,'id_hook2'),(0x40032aee,'cfg_hook')]:jump(at,name,'transfert de samples CYC/SMP')
ptr(0x40084be2,'id_namebuf','identité du transfert')
call(0x4009249a,'rpc_type','réception des messages sample SMP')
jump(0x40094c9a,'rpc_ot','réponse aux messages sample SMP',1)
jump(0x4007240c,'key_hook','raccourcis sampler seulement')
for at in [0x400551a6,0x40055bfa]:call(at,'sm_seq_capture','capture note au trig sans slides TG',1)
jump(0x4008173c,'sm_live_note_capture','capture note live sans Scale Lock TG')
call(0x400a6732,'preset_fail_hook','chargement sample depuis navigateur')
ptr(0x400a6754,'msg_buf','résultat chargement sample')
call(0x400a6816,'pool_store_hook','verrou sample via Sound Pool')
call(0x400a659e,'getentry_hook','entrée sample dans navigateur')
add(0x4010dce0+2310,b'\x06','borne machine sampler du paramètre Algorithm','05')
ptr(0x400ff9cc,'tick_hook','service clavier natif puis UI sampler protégé')
for at in [0x400ff9b8,0x400ffa78,0x40103070,0x401031b4,0x40107e18]:ptr(at,'led_hook','service UI sampler protégé IPL0')
end=int(t['append']['dest'],16)+t['append']['size'];n=(end-0x401ab750+16383)//16384;assert n==6
add(0x400792f2,struct.pack('>I',0x401eb750+20*n),'cache : code exclu LRU','401eb750')
add(0x400792bc,struct.pack('>I',0x401eb750+20*(n+1)+16),'cache : liens précédents sûrs','401eb774')
t.update(id='sample-wizard',name='Sample Wizard',requires=[],conflicts=[],order=20,cache_blocks=n,description=['Sampler autonome expérimental, septième machine.','Slice varispeed ; sans fonctions globales Model-TG.'],credit={'repo':'TinyGregAudio/Model-TG','commit':'70b39dd6787770ebefc7a2d78dea1678ec012679','license':'MIT'})
# Aucun raccord du profilage, des FX master ou des optimisations DSP stock.
for lo,hi in [(0x400a8906,0x400a890c),(0x400a956c,0x400a9574),(0x400a98c4,0x400a98cc),(0x400a9daa,0x400a9db2),(0x4005966a,0x40059676),(0x400169f0,0x400169f8),(0x40023550,0x40023556)]:
 assert not any(build.BASE+w['off']<hi and lo<build.BASE+w['off']+len(bytes.fromhex(w['new'])) for w in t['writes'])
image,_=build.apply_writes(stock,[t]);payload=build.payload_runtime(t,stock,None);assert len(image)+build.BASE==int(t['append']['at'],16)
ref=dict(w=hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest(),p=hashlib.sha256(build.payload_image(t,payload)).hexdigest())
(p/'installer.json').write_text(json.dumps(t));(p/'hook-manifest.json').write_text(json.dumps(manifest,indent=2));(p/'installer-ref.json').write_text(json.dumps(ref));print('PASS installateur privé :',len(t['writes']),'écritures vérifiées ;',n,'blocs réservés ;',hex(end),'; sans raccords TG globaux')
