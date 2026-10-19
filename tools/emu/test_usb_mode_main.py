"""Model the published main USB 2ch/6ch Pad Setup switch against the actual OS image."""
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
from midi_safety_load import load
from unicorn import UC_HOOK_CODE, m68k_const as mk

ROOT = HERE.parents[1]
BASE = 0x40000400


def main():
    case = "build/usb-mode-main/main"
    r, _ = load(case)
    meta = json.loads((ROOT / (case + ".json")).read_text())
    tweaks = meta["tweaks"]
    assert any(t["id"] == "wizard-continuous-filter" for t in tweaks)
    assert not any("diagnostic" in t["id"] for t in tweaks)
    symbols = {k: int(v, 16) for t in tweaks for k, v in t.get("symbols", {}).items()}
    r.s = symbols
    u = r.u
    tweak = json.loads((ROOT / "tweaks/model-cycles_OS1.13/11-6ch-usbup.json").read_text())
    patches = []
    for write in tweak["writes"]:
        at = write["off"] + BASE
        if (at < 0x40003000 or at >= 0x4019B000) and isinstance(write["old"], str) and isinstance(write["new"], str):
            patches.append({"at": at, "two": write["old"], "six": write["new"]})
    assert len(patches) == 15

    messages, modes, cache = [], [], []

    def bind(at, fn):
        if at not in r.stubs:
            u.hook_add(UC_HOOK_CODE, r.stub, begin=at, end=at)
        r.stubs[at] = fn

    bind(r.r32(symbols["wf_usb_popup"]), lambda a: messages.append(bytes(u.mem_read(a[0], 48)).split(b"\0")[0].decode()) or 0)

    def mode_entry(uc, pc, size, data):
        modes.append(r.r32(uc.reg_read(mk.UC_M68K_REG_A7) + 4))

    u.hook_add(UC_HOOK_CODE, mode_entry, begin=0x40004E04, end=0x40004E04)
    bind(0x40004D9A, lambda a: 0)
    bind(0x40004DB4, lambda a: 0)
    r.w32(0x404A09C8, 5)
    r.w32(0x40FE4178, 0)
    r.w32(0x40A7883C, 0)

    def check(which):
        for patch in patches:
            assert bytes(u.mem_read(patch["at"], len(patch[which]) // 2)).hex() == patch[which], hex(patch["at"])

    check("six")
    assert r.r32(symbols["wf_usb_six"]) == 1
    r.w32(0x40A7883C, 1)
    assert r.call("wf_usb_set", 0) == 0
    check("six")
    assert not modes
    r.w32(0x40A7883C, 0)
    for _ in range(4):
        assert r.call("wf_usb_set", 0) == 1
        check("two")
        assert r.r32(symbols["wf_usb_six"]) == 0
        assert r.call("wf_usb_set", 1) == 1
        check("six")
        assert r.r32(symbols["wf_usb_six"]) == 1
    assert modes == [2, 5] * 8

    # Enter the actual Pad Setup menu, select USB, and edit only after DATA.
    event = 0x93010000
    keyevent = event + 128

    def key(code, flags):
        u.mem_write(keyevent, struct.pack(">6I", 0, 0, 0, code, flags, 0))
        return r.call("wf_key", keyevent)

    key(13, 1)
    key(2, 1)
    key(2, 33)
    key(2, 0)
    key(13, 0)
    assert r.call("wf_menu_edit") == 0
    delta = [1]
    bind(0x4006F73A, lambda a: delta[0])
    u.mem_write(event, struct.pack(">6I", 0x400FBEBC, 0, 0, 1, 1, 0))
    assert r.call("wf_menu_encoder", event) == 1
    assert r.call("wf_menu_row") == 1
    key(32, 16)
    delta[0] = -1
    assert r.call("wf_menu_encoder", event) == 1
    check("two")
    assert r.r32(symbols["wf_usb_six"]) == 0
    key(12, 1)
    assert r.call("wf_menu_encoder", event) == 0
    print("PASS main real-boot image: 6ch default; 15 exact USB ranges; stopped-only 2ch/6ch transitions; Pad Setup DATA/BACK; filter included, diagnostics absent")
    print("LIMITS: USB controller, popup pixels, and host re-enumeration remain physical-device behavior; user has already confirmed mode switch on hardware.")


if __name__ == "__main__":
    main()
