"""Remove feature entry points while preserving later MIDI/FX integrations."""
import json
from pathlib import Path
NAMES=['on','off','on_received','off_received','receive_on','receive_off','encoder_block','pad','reset','visible_chord','step_on']
def setup(meta):
 mi=meta['midi_input_symbols'];aliases={n:mi[n] for n in ('mm_input_on','mm_input_off','mi_lfo_encoder','mi_receive_on_original','mi_receive_off_original')}
 aliases.update({n:meta['playability_symbols'][n] for n in ('mx_arp_wants','mx_arp_on')})
 return aliases,[('no_ck_'+n,mi['mi_'+n],'nc_'+n) for n in NAMES]
def remove(peek,patch):
 audit=json.loads((Path(__file__).parent/'chordkeys-removal-guards.json').read_text())
 retained={0x4005b9c6,0x4005bad2,0x40019ee2,0x40019cba,0x4001d094,0x4001d120,0x4005919e}
 restored=[]
 for row in audit:
  at=int(row['at'],16)
  if at in retained:continue
  old=bytes.fromhex(row['current']);new=bytes.fromhex(row['native'])
  assert peek(at,len(old))==old,(hex(at),peek(at,len(old)).hex(),old.hex())
  patch(at,new);restored.append(at)
 # Later MIDI wrappers use optional previous feature delegates in .data.
 # Clearing these selects their already present native fallback paths.
 for at,old in [(0x467910f8,'4018cc7240190a1c401c4f68401c4fb6'),(0x467911e4,'401908cc')]:
  raw=bytes.fromhex(old);assert peek(at,len(raw))==raw,(hex(at),peek(at,len(raw)).hex())
  patch(at,bytes(len(raw)))
 # The old external harmony-pad helper is private to the removed pad handler.
 # Make any retained compatibility caller return through its existing epilogue.
 assert peek(0x467b101c,6).hex()=='20080c800000'
 patch(0x467b101c,bytes.fromhex('4ef9401602d8'))
 return dict(native_entries_restored=[hex(x) for x in restored],midi_chord_delegates_cleared=True,fx_extended_lock_serialization_preserved=True)
