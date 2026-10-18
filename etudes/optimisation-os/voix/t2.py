from prof import *
img = load_stock()
e = E.Engine(img); e.machine_defaults(0, 0); e.solo(0)
cnt = collections.Counter()
e.uc.hook_add(UC_HOOK_CODE, lambda uc,a,s,u: cnt.update([a]))
e.block(1); cnt.clear(); e.block(0)
for a in (0x400a9240,0x400a9244,0x400a9246,0x400a924a,0x400a924c,0x400a9250,0x400aa3a2,0x400aa3a8,0x400aa3ac,0x400aa3be,0x400a7e6c,0x400a7f64,0x400a7e10):
    print(hex(a), cnt[a])
