"""Vrai constructeur ScaleMenuView, vraie ligne et handlers DATA natifs."""
from pathlib import Path
exec(Path(__file__).with_name('test_page_length_release.py').read_text(encoding='utf-8').split('# Le vrai writer LED')[0])
view=0x93460000;u.mem_write(view,bytes(1024));bind(0x400802ec,lambda a:0);bind(0x40069df6,lambda a:0);bind(0x400cf044,lambda a:0)
bind(0x40080064,r.new)
r.w32(0x93180000,model+0x800);r.w32(model+0x800-12,0)
print('CTOR',flush=True)
from unicorn import UC_HOOK_MEM_UNMAPPED
u.hook_add(UC_HOOK_MEM_UNMAPPED,lambda uc,access,address,size,value,data:print('UNMAPPED',hex(uc.reg_read(C.UC_M68K_REG_PC)),hex(address),size,flush=True) or False)
r.call(0x4002f338,view)
count=r.call(0x40072514,view);print('COUNT',count,flush=True)
items=[r.r32(r.r32(view+4)+8*i) for i in range(count)]
found=[i for i,it in enumerate(items) if r.r32(it+56)==s['pl_draw']]
assert len(found)==1,found
index=found[0];item=items[index]
assert r.r32(item+72)==s['pl_change']
print('PASS real Page Setup constructor includes Page Len at row',index,'of',count,'with native closures',flush=True)
# Libelle std::string cache dans A0, ABI native du renderer de menu.
result=view+0x1000;u.mem_write(result,bytes(32));u.reg_write(C.UC_M68K_REG_A0,result);r.call(s['pl_label'],item+12)
ptr=r.r32(result);assert r.string(ptr)=='Page Len',(hex(ptr),r.string(ptr))
print('PASS actual label builder returns Page Len through native std::string ABI',flush=True)
# Le natif de selection DATA adresse la nouvelle ligne, puis change sa valeur.
r.w32(view+20,max(0,index-3));r.w32(view+24,min(index,3));tag(16)
r.call(0x400732ec,item,1);assert u.mem_read(item+80,1)==b'\x01'
r.call(s['pl_change'],item+60,0,0xfffffffc);assert r.call(s['pl_length'],h)==12
r.call(0x400732ec,item,0);assert u.mem_read(item+80,1)==b'\0'
print('PASS native Page Len item edit toggle, value change16->12, closure stability and retained Scale/Key/Lock items',flush=True)
led=view+0x2000;bind(0x400cfaf4,lambda a:led);bind(0x4008e942,lambda a:0);bind(0x4008e964,lambda a:0);bind(0x4008e998,lambda a:0)
bind(s['pl_old_led'],lambda a:19)
for n in range(1,17):
 tag(n);u.mem_write(led,bytes(512));r.call(0x4002fd38,view,0,0)
 assert [r.r32(led+40+4*i) for i in range(1,17)]==[2]*n+[1]*(16-n)
print('PASS actual constructed Page Len row is recognized by the native LED callback for1..16steps',flush=True)
