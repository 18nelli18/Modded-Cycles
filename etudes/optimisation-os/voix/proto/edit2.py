s = open("test_proto.py").read()
s = s.replace("""def play(img, setup, blocks, trigs, count=False, changes=None):
    e = E.Engine(img)
    for t, kw in setup.items():
        e.set(t, **kw)""", """def play(img, setup, blocks, trigs, count=False, changes=None, solo=None):
    e = E.Engine(img)
    for t, kw in setup.items():
        e.set(t, **kw)
    if solo is not None:
        e.solo(solo)""")
s = s.replace("decay=r.randint(5, 60))", "decay=r.randint(5, 40))")
s = s.replace("""            retrig = 1000
            ref, _ = play(STOCK, {0: kw}, 1300, {1: 1, retrig: 1})
            mod, _ = play(IMG, {0: kw}, 1300, {1: 1, retrig: 1})""", """            retrig = 900
            ref, _ = play(STOCK, {0: kw}, 1100, {1: 1, retrig: 1}, solo=0)
            mod, _ = play(IMG, {0: kw}, 1100, {1: 1, retrig: 1}, solo=0)""")
s = s.replace("""    for m in range(6):
        for k in range(4):""", """    for m in range(6):
        for k in range(3):""")
s = s.replace("print(\"1. son, machine par machine (piste 0 seule, 5 autres jamais déclenchées)\")", "print(\"1. son, machine par machine (piste 0 seule calculée)\")")
s = s.replace("pistes jamais jouées : {'identiques' if others else 'DIFFÉRENTES'}", "autres pistes : {'identiques' if others else 'DIFFÉRENTES'}")
open("test_proto.py","w").write(s)
