"""Dernier CUT piste5 uniquement : cause exacte, autres pistes sans ecrasement."""
from pathlib import Path
src=Path(__file__).with_name('test_complete_irq_accounting.py').read_text().split('rows=[]')[0]
exec(compile(src,__file__,'exec'))
ts=m['track5_cut_cause']['symbols'];rows=[]
def event(initial,previous,current,protect5=False):
 setup(r,m,[0,4,4,2,6 if protect5 else 0,5]);q=initial*256//100
 for off,value in [(0x78,q),(0xf10,q*8),(0xf14,q*256),(0xf04,previous*256//100)]:r.w32(GB+off,value)
 r.w32(m['dx_symbols']['dx_enabled'],1);r.u.mem_write(0x80001858+4*128,struct.pack('>32i',*([100000]*32)));r.w32(GB+0x80,1000000);r.w32(GB+0xf00,1000000-NOM);r.w32(0xfc07000c,1000000+NOM*current//100);r.call(ts['dt_audio_end']);return list(r.u.mem_read(GB+0x58,6))
for name,s,p,l in [('near_deadline',80,100 if m['deadline_headroom']['reserve_q']<3 else 99,100 if m['deadline_headroom']['reserve_q']<3 else 99),('overrun',80,108,108),('sustained',90,90,90)]:
 r.w32(ts['dt_t5_valid'],0);fades=event(s,p,l);assert fades[4] and r.r32(ts['dt_t5_valid']),name
 expected=min(r.r32(GB+0xf10)>>3,r.r32(GB+0xf14)>>8);assert r.r32(ts['dt_t5_s'])==expected and r.r32(ts['dt_t5_l'])==r.r32(GB+0x7c)
 rows.append(dict(case=name,s=r.r32(ts['dt_t5_s']),load=r.r32(ts['dt_t5_l'])))
 before=[r.r32(ts[k]) for k in ('dt_t5_s','dt_t5_l','dt_t5_valid')];other=event(80,108,108,True);assert any(other) and not other[4] and before==[r.r32(ts[k]) for k in ('dt_t5_s','dt_t5_l','dt_t5_valid')]
print('PASS exact track5 cause on sustained/near-deadline/overrun; other-track cuts do not overwrite',rows,flush=True)
old=r.r32(ts['dt_old_popup']);shown=[];bind(old,lambda args:shown.append(r.string(args[0])) or 0)
def fmt(args):
 out,pattern,*values=args;text=r.string(pattern);line=text%tuple(values[:text.count('%u')]);r.u.mem_write(out,line.encode()+b'\0');return len(line)
bind(0x40000e6e,fmt);buf=0x931b2000;r.u.mem_write(buf,b'A75 P106 O1 N3\0');r.w32(ts['dt_t5_s'],204);r.w32(ts['dt_t5_l'],253);r.w32(ts['dt_t5_valid'],1);r.call(ts['dt_popup'],buf)
assert shown[-1]=='T5 S80 L99' and not r.r32(ts['dt_t5_valid']) and not any(r.u.mem_read(ts['dt_cuts'],24)),shown
r.call(ts['dt_popup'],buf);assert shown[-1]=='T5 NO CUT',shown
r.u.mem_write(buf,b'CTRL ALL\0');r.call(ts['dt_popup'],buf);assert shown[-1]=='CTRL ALL',shown
r.w32(ts['dt_t5_valid'],0);r.w32(m['dx_symbols']['dx_enabled'],0);r.call(ts['dt_audio_end']);assert not r.r32(ts['dt_t5_valid'])
r.call(ts['dt_init']);assert r.r32(ts['dt_old_popup'])==old
print('PASS compact rounded popup, atomic reset, no-cut label, ordinary notices, DX-off and repeat init',shown,flush=True)
a.output.write_text(json.dumps(dict(cases=rows,popups=shown,hardware_tested=False),indent=2)+'\n')
