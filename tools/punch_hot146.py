"""PUNCH146 : attenuation fixe fusionnee au compteur Q16, puis pas constant."""
from punch_fast143 import source as base_source
def source(src,build,steady=False):
 path=base_source(src,build);dsp=path.with_name('punch_dsp.h');s=dsp.read_text()
 old='u32 am = m->att, ac = c->att, bm = m->base, bc = c->base;'
 assert old in s
 s=s.replace(old,'u32 bm = m->base, bc = c->base;\n\tu32 am = m->att + (bm << 16), ac = c->att + (bc << 16);')
 s=s.replace('bm + (am >> 16)','am >> 16').replace('bc + (ac >> 16)','ac >> 16')
 s=s.replace('m->att = am; c->att = ac;', 'm->att = am - (bm << 16); c->att = ac - (bc << 16);')
 if steady:
  start=s.index('static void render_2op(');end=s.index('\n/* ----',start);body=s[start:end]
  flat=body.replace('render_2op(', 'render_steady(').replace(', dm = m->dinc, dc = c->dinc','').replace(' im += dm; ic += dc;','')
  body=body.replace('fm_op *m = &v->op[0], *c = &v->op[1];', 'fm_op *m = &v->op[0], *c = &v->op[1];\n\tif (!(m->dinc | c->dinc)) { render_steady(v, out); return; }')
  s=s[:start]+flat+'\n'+body+s[end:]
 dsp.write_text(s)
 return path
