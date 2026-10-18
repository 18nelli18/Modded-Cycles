"""Contre-épreuve (piège signalé par l'agent « voix ») : un crochet de lecture ajouté après traduction ne voit pas
les lectures du code déjà traduit. On refait la mesure « six » avec uc.ctl_flush_tb() juste après la pose des
crochets du traceur, et on compare à mesures_six.json.   python3 mesure_flushtb.py"""
import json
import sys
sys.dont_write_bytecode = True
import mesure   # noqa: E402
import trace    # noqa: E402

orig = trace.Tracer.__init__


def init(self, b):
    orig(self, b)
    b.uc.ctl_flush_tb()


trace.Tracer.__init__ = init
res, tr = mesure.run("six")
mesure.table(res)
ref = json.load(open("mesures_six.json"))["rows"]
keys = ("ins", "dmiss", "sram_r_lines", "sram_r_acc", "sdram_r_lines", "sdram_r_acc")
diff = {f: {k: (ref[f][k], round(d[k], 1)) for k in keys if abs(ref[f][k] - d[k]) > 0.5}
        for f, d in res["rows"].items() if f in ref}
print("écarts avec mesures_six.json :", {f: v for f, v in diff.items() if v} or "aucun")
