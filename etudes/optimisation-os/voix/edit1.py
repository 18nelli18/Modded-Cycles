s = open("prof.py").read()
s = s.replace("""        uc.hook_add(UC_HOOK_CODE, self._code)
        uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, self._mem)
        orig = emac._ea""", """        self.h = [uc.hook_add(UC_HOOK_CODE, self._code), uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, self._mem)]
        orig = self._orig_ea = emac._ea""")
s = s.replace("""        emac._ea = ea
        self.on = True
""", """        emac._ea = ea
        self.on = True

    def close(self):
        for h in self.h:
            self.uc.hook_del(h)
        self.emac._ea = self._orig_ea
        self.on = False
""")
s = s.replace('''    def name(self, f):
        return NAMES.get(f, f"{f:#x}")''', '''    def name(self, f):
        return "voice_loop" if f == 0 else NAMES.get(f, f"{f:#x}")''')
open("prof.py","w").write(s)
m = open("machines.py").read()
m = m.replace("""        p = Prof(e.uc, e.emac, record=False)
        p.on = False
""", "")
m = m.replace("""            if b == nb - 1:
                p.reset(); p.on = True
            o = e.block(trig.get(b, 0))""", """            if b == nb - 1:
                p = Prof(e.uc, e.emac, record=False)
            o = e.block(trig.get(b, 0))""")
m = m.replace("        p.on = False\n        d = dict", "        p.close()\n        d = dict")
open("machines.py","w").write(m)
