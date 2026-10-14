#!/usr/bin/env python3
"""Sépare HARMONY de la profondeur LFO2, sans changer le format disque PR87.

Le précompilé MIT PR87 est vérifié par chord_keys_relocate avant ce module.
Neuf instructions propres, nom de fonction + offset + octets exacts : slot
RAM32 ->26, identifiant disque33 conservé. TG emploie26/27 seulement dans
le SON pour son état Sampler ; jamais comme locks ni comme paramètres DSP.
Les buffers de son, leur codec LFO2 et les 33 mots copiés restent inchangés.
"""
import struct

HARMONY_SLOT = 26
HARMONY_ID = 33
# Les offsets restent identiques après relogement (aucune taille changée).
PATCHES = (
    ('ck_plock_save_hook', 0x00, '0c8400000080', '0c8400000068', 'sauvegarde complète : slot*4'),
    ('ck_plock_partial_hook', 0x00, '0c8300000020', '0c830000001a', 'sauvegarde partielle : slot'),
    ('ck_plock_decode_hook', 0x18, '7020', '701a', 'disque33 vers RAM26'),
    ('write_lock', 0x56, '48780020', '4878001a', 'setter natif de lock'),
    ('ck_plock_grid', 0x7e, '48780020', '4878001a', 'lecture du lock tenu'),
    ('chord_audio_update', 0xf0, '71eb0040', '71eb0034', 'lecture HARMONY audio ; copie du mot32 intacte'),
    ('ck_midi_sequence', 0x9a, '71e80040', '71e80034', 'lecture HARMONY MIDI'),
    ('ck_audio_locked_controls', 0x3c, 'd1fc423087fc', 'd1fc423087f8', 'premier mot du bitmap natif'),
    ('ck_audio_locked_controls', 0x42, '082800000003', '082800020000', 'bit26 = bit2 du premier octet BE'),
)


def adapt(compiled, syms):
    """Retourne (clusters copiés/modifiés, audit), sans déplacer un seul octet."""
    symbols = {k: int(v, 0) if isinstance(v, str) else v for k, v in syms.items()}
    result = [(at, bytearray(code)) for at, code in compiled]

    def span(address, size):
        matches = [(at, code) for at, code in result if at <= address and address + size <= at + len(code)]
        if len(matches) != 1:
            raise ValueError(f'Instruction hors cluster propre en {address:#x}')
        return matches[0]

    def verify(name, offset, expected):
        address = symbols[name] + offset
        old = bytes.fromhex(expected)
        at, code = span(address, len(old))
        if code[address - at:address - at + len(old)] != old:
            raise ValueError(f'Contrat PR87 différent : {name}+{offset:#x} en {address:#x}')

    # Ne pas confondre HARMONY avec la copie finale de params[32] : ce dernier
    # mot contient désormais la profondeur LFO2 et doit rester copié à l'identique.
    verify('chord_audio_update', 0x44, '3f6b00400058')
    verify('ck_plock_save_hook', 0x08, '16bc0021')
    verify('ck_plock_partial_hook', 0x08, '287c00000021')
    verify('ck_plock_decode_hook', 0x10, '0c8000000021')
    verify('chord_audio_update', 0xf8, '4eb9' + struct.pack('>I', symbols['ck_audio_locked_controls']).hex())
    verify('ck_midi_sequence', 0xa2, '4eb9' + struct.pack('>I', symbols['ck_audio_locked_controls']).hex())
    sites = []
    for name, offset, old_hex, new_hex, reason in PATCHES:
        verify(name, offset, old_hex)
        address = symbols[name] + offset
        old, new = bytes.fromhex(old_hex), bytes.fromhex(new_hex)
        assert len(old) == len(new)
        at, code = span(address, len(old))
        code[address - at:address - at + len(old)] = new
        sites.append(dict(function=name, offset=offset, at=hex(address), old=old_hex, new=new_hex, reason=reason))
    changed = {int(site['at'], 16) + i for site in sites for i in range(len(bytes.fromhex(site['old'])))}
    for (old_at, old), (new_at, new) in zip(compiled, result):
        assert old_at == new_at and len(old) == len(new)
        assert all(a == b or old_at + i in changed for i, (a, b) in enumerate(zip(old, new)))
    return [(at, bytes(code)) for at, code in result], dict(
        harmony_slot=HARMONY_SLOT, serialized_id=HARMONY_ID,
        native_sound_slots_unchanged=True, sizes_and_symbols_unchanged=True, patches=sites)
