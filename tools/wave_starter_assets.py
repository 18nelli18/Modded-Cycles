"""WAVE115 : precharge explicite, detour direct DSP, BACK remonte les dossiers."""
from pathlib import Path
import hashlib,json,os,shutil,struct,subprocess
CODE=0x46849000;DATA=0x46860000;LIMIT=0x46888000
def apply(root,build,rt,tail,meta,patch,tiny,legacy,prefix):
 from gen_governor_recovery_test import TAIL,RUNTIME
 root=root.resolve();src=root/'tools/machines/wave_starter';wav=root/'docs/flasher/AV-WAVE-Morph.wav';converter=root/'docs/flasher/convert.js'
 node=os.environ.get('NODE_BINARY') or shutil.which('node');assert node,'Set NODE_BINARY to Node.js'
 pcm=build/'wave-starter.pcm';info=json.loads(subprocess.check_output([node,str(src/'bake.js'),str(converter),str(wav),str(pcm)],text=True));raw=pcm.read_bytes()
 assert info==dict(frames=16,samples=68608,perFrame=4288,bytes=137216),info
 assert legacy['code']+legacy['code_bytes']<=DATA and DATA+len(raw)<LIMIT
 assert meta['fundamentals']['end']<=CODE
 table=tiny['data'];nm=tiny['machine_count'];at=table+4*(nm+14);old=bytes(tail[at-TAIL:at-TAIL+4]);original=int.from_bytes(old,'big');assert original==0x46779000
 # Gardes du moteur present : tableaux pointeur/compte et disposition4288.
 for offset,want in [(0x467790dc,'49f94677b2b8'),(0x467790ea,'49f94677b2a0'),(0x467790f4,'283c000010c0')]:assert bytes(rt[offset-RUNTIME:offset-RUNTIME+len(bytes.fromhex(want))])==bytes.fromhex(want)
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');obj=build/'wave-starter.o';elf=build/'wave-starter.elf';binary=build/'wave-starter.bin';ld=build/'wave-starter.ld'
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-c',str(src/'starter.c'),'-o',str(obj)],check=True)
 browser=build/'wave-browser.o';subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-c',str(src/'browser.c'),'-o',str(browser)],check=True)
 pad=build/'wave-pad.o';subprocess.run([cross+'gcc.exe','-mcpu=54418','-c',str(src/'pad.S'),'-o',str(pad)],check=True)
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); wave_starter_code_end = .; .bss 0x4684a000 (NOLOAD) : {{ *(.bss*) *(COMMON) }} wave_starter_end = .; }}\nPROVIDE(wave_previous_update = wave_original_update);\nPROVIDE(wave_factory_pcm = {DATA:#x});')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),str(obj),str(browser),str(pad)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};code=binary.read_bytes();assert CODE+len(code)<0x4684a000 and sy['wave_starter_end']<0x46850000
 assert not any(tail[0x4684a000-TAIL:sy['wave_starter_end']-TAIL]),'browser BSS occupied'
 for address,data in [(CODE,code),(DATA,raw)]:
  before=bytes(tail[address-TAIL:address-TAIL+len(data)]);assert len(before)==len(data) and not any(before),(hex(address),'occupied');patch(address,before,data,tail)
 # Couvrir les pointeurs deja caches autant que la table de dispatch.
 patch(0x46779000,bytes.fromhex('4fefffc048d77cfc'),bytes.fromhex('4ef9')+struct.pack('>I',sy['wave_starter_update'])+bytes.fromhex('4e71'))
 patch(0x4677b2a0,bytes(48),struct.pack('>12I',*([68608]*6+[DATA]*6)))
 patch(0x400a6d5c,bytes.fromhex('4e56ff8c48d73cfc'),bytes.fromhex('4ef9')+struct.pack('>I',sy['wave_browser_key'])+bytes.fromhex('4e71'),prefix)
 patch(0x4677a750,bytes.fromhex('4fefffc448d77fff'),bytes.fromhex('4ef9')+struct.pack('>I',sy['wave_starter_note'])+bytes.fromhex('4e71'))
 # L ancien tampon de la piste1 a46800000 chevauchait les FX ajoutes.
 # Six fenetres3Mo de46900000 a47b00000, sous la pile48000000.
 patch(0x4677a684,bytes.fromhex('068046800000'),bytes.fromhex('068046900000'))
 return dict(code=CODE,code_bytes=len(code),data=DATA,end=DATA+len(raw),symbols=sy,frames=16,samples=68608,bytes=len(raw),source='AV-WAVE-Morph.wav',source_sha256=hashlib.sha256(wav.read_bytes()).hexdigest(),pcm_sha256=hashlib.sha256(raw).hexdigest(),shared_read_only=True,per_track_override=True,extra_audio_buffers=0,custom_buffer=0x46900000,custom_buffer_end=0x47b00000,preloaded_on_boot=True,direct_engine_hook=True,browser_back_parent=True,hardware_tested=False)
