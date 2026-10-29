"""Retire Legacy's catalogue/receiver/browser/DSP; keep stable machine IDs."""
import struct
def setup(meta):
 fx=meta['fx_menu']['symbols']
 aliases={'rm_machine_'+k:fx['machine_'+k] for k in ('valid','stamp','result')}
 entries=[('machine_step',fx['fx_machine_step'],'rm_step'),('machine_get',0x4001e318,'rm_machine_get'),('machine_set',0x4001477e,'rm_machine_set')]
 return aliases,entries
def sources(work,out,meta):
 order=[m for m in meta['tiny_extra']['menu_order'] if m!=21]
 (out/'removed-roster.c').write_text('const unsigned char rm_order[]={'+','.join(map(str,order))+'};\nconst unsigned int rm_count='+str(len(order))+';\n')
 return [work/'removed-machines.c',out/'removed-roster.c']
def remove(meta,peek,patch,sy,lite):
 if lite:return dict(already_absent=True,visible_order=list(range(6)))
 legacy=meta['legacy'];old=legacy['symbols'];fx=meta['fx_menu']['symbols'];edits=[]
 # Ordinary DIN/USB MIDI resumes native parsing, without DX bank collection.
 for at,new in [(0x4007f694,'487940f1bf24'),(0x4007f6a8,'4fefffd848d77c7c')]:
  assert peek(at,2)==b'\x4e\xf9',(hex(at),peek(at,8).hex());patch(at,bytes.fromhex(new))
 lo=legacy['code'];hi=lo+legacy['code_bytes'];patch(lo,bytes(hi-lo))
 def jump(at,to):
  assert lo<=at and at+6<=hi,(hex(at),hex(to));patch(at,b'\x4e\xf9'+struct.pack('>I',to));edits.append(hex(at))
 for name in ('dx7_service','dx7_browser_key','dx7_browser_encoder','dx7_browser_draw','dx7_status_draw','dx7_library_load','dx7_library_save','dx7_update','dx7_is_active'):
  if name in old:jump(old[name],sy['rm_noop'])
 jump(old['dx7_render'],sy['rm_silence']);jump(old['dx7_popup'],old['dx7_previous_popup'])
 table=meta['tiny_extra']['data'];n=meta['tiny_extra']['machine_count']
 # Compatibility slot is a safe, silent retired slot; the audio-frame mapper
 # handles saved21 as native Tone, and the picker/getter also normalize to Tone.
 patch(table+4*(n+21),struct.pack('>I',sy['rm_noop']));patch(table+4*(2*n+21),struct.pack('>I',sy['rm_silence']))
 patch(table+4*21,peek(table+4*4,4))
 patch(0x46888000,bytes(0x1000))
 return dict(visible_order=[m for m in meta['tiny_extra']['menu_order'] if m!=21],erased_dsp_code_bytes=hi-lo,erased_art_bytes=0x1000,ordinary_midi_receivers_restored=True,safe_stub_addresses=edits,saved_legacy_audio_fallback='Tone',stable_ids=True)
