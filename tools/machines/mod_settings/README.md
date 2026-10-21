# Mod Setup persistence, fixed main 2.07

Private v3 behavior was confirmed by AveyCole on 20 October 2026. The v4 layout places this helper at `0x467b0000`, in Model-TG’s reserved last MiB (notes/31), and preserves all 1040 bytes of the shared display mask at `0x40154ae4`. The tail copy count includes the extension; native bootstrap and UI proofs exercise the final addresses.

The nine API entries are stock pad selection, USB state, numeric-display byte, latch mute, delay divisions, USB setter, original key handler, original draw handler, menu pointer. BACK schedules a save to `/ModSetup.cfg`. Reads and writes run only in the UI draw path with playback stopped and storage ready. The eight-byte format is `MS01`, five flag bits, complemented flags, `A5 5A`; corrupt or missing files retain defaults.

Native proofs: `output/firmware/prove_usb_mod_settings_v4.py`, `prove_delay_settings_v4.py`, `prove_no_filter_pon_v4.py`, `prove_harmony_preview_v5.py`. Tests cover both USB transitions, all flag combinations, bad files, save/reload, playback deferral, delay timing, filter removal, diagnostics and harmony/slice regression. The corrected layout still needs hardware verification.
