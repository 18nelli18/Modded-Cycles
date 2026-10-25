"""Tables PUNCH deployees, arithmetique et PCM inchanges ; source MIT conservee."""
import re

def source(src, build):
    fast = build / 'punch-fast'
    fast.mkdir(exist_ok=True)
    tables = (src / 'punch_tables.h').read_text()
    def values(name):
        body = re.search(r'\b' + name + r'\[\d+\]\s*=\s*\{(.*?)\}', tables, re.S)[1]
        return [int(x, 0) for x in re.findall(r'0x[0-9a-fA-F]+|\d+', body)]
    logs, powers = values('FM_LOGSIN'), values('FM_POW')
    expanded = logs + list(reversed(logs))
    amplitudes = [powers[i & 255] >> (i >> 8) for i in range(3328)]
    def array(name, data):
        return 'static const u16 ' + name + '[' + str(len(data)) + '] = {\n' + ',\n'.join(','.join(map(str, data[i:i+16])) for i in range(0, len(data), 16)) + '\n};\n'
    (fast / 'punch_fast_tables.h').write_text(array('FM_LOGFULL', expanded) + array('FM_AMPLITUDE', amplitudes))
    dsp = (src / 'punch_dsp.h').read_text()
    dsp = dsp.replace('#include "punch_tables.h"', '#include "punch_tables.h"\n#include "punch_fast_tables.h"')
    old = 's = FM_LOGSIN[(p & 0x100) ? (~p & 0xff) : (p & 0xff)];'
    assert old in dsp
    dsp = dsp.replace(old, 's = FM_LOGFULL[p & 0x1ff];')
    old = 's = FM_POW[tot & 0xff] >> (tot >> 8);'
    assert old in dsp
    dsp = dsp.replace(old, 's = FM_AMPLITUDE[tot];')
    dsp = dsp.replace('out[i] = (x + fm_op_out(pc >> 22, bc + (ac >> 16))) * 2;', 'out[i] = (s32)((u32)(x + fm_op_out(pc >> 22, bc + (ac >> 16))) << 16);')
    dsp = dsp.replace('out[i] = fm_op_out((pc >> 22) + (u32)(x >> 2), bc + (ac >> 16)) * 4;', 'out[i] = (s32)((u32)fm_op_out((pc >> 22) + (u32)(x >> 2), bc + (ac >> 16)) << 17);')
    old = '\tu8 click;               /* blocks of mallet click left */'
    assert old in dsp
    dsp = dsp.replace(old, old + '\n\tu32 cache_note, cache_sweep, cache_knobs, cache_state;\n\tu8 params_valid;')
    old = '\tparams(v, in);'
    assert old in dsp
    dsp = dsp.replace(old, '''\t/* Recalculer au moindre changement utile, y compris le clic MAR. */
\t{
\t\tu32 knobs = ((u32)in->color << 24) | ((u32)in->contour << 16) | ((u32)in->decay << 8) | in->punch;
\t\tu32 state = in->vel | ((u32)v->model << 8) | ((u32)v->click << 16);
\t\tif (!v->params_valid || v->cache_note != (u32)in->note || v->cache_sweep != (u32)in->sweep || v->cache_knobs != knobs || v->cache_state != state) {
\t\t\tparams(v, in);
\t\t\tv->cache_note = (u32)in->note; v->cache_sweep = (u32)in->sweep;
\t\t\tv->cache_knobs = knobs; v->cache_state = state; v->params_valid = 1;
\t\t}
\t}''')
    (fast / 'punch_dsp.h').write_text(dsp)
    for name in ('punch.c', 'punch_tables.h', 'punch_icons.h'):
        (fast / name).write_bytes((src / name).read_bytes())
    bridge = (fast / 'punch.c').read_text()
    old = '\tfor (i = 0; i < FM_BLOCK; i++)                   /* Q15 -> Q31 / 2 */\n\t\tout[i] <<= 15;'
    assert old in bridge
    bridge = bridge.replace(old, '\t/* Conversion Q31 fusionnee avec le rendu des operateurs. */')
    bridge = bridge.replace('struct track *tr = &trk[TRACK_OF(v)];\n\tint i;', 'struct track *tr = &trk[TRACK_OF(v)];')
    (fast / 'punch.c').write_text(bridge)
    return fast / 'punch.c'
