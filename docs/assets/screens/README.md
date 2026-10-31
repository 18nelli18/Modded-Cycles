Supermodel 2.64 native LCD captures

Rendered from the released Full firmware using tools/emu/render_song_top.py and render_song_grid.py. These execute the native ColdFire UI drawing code and capture its 128 x 64 framebuffer. PNGs retain integer pixel enlargement. The Song screen shows example rows and mute states. No screen labels were recreated in HTML.

The `*-lcd.png` files are the same two captures converted for the home page: each 128 x 64 pixel is recoloured to the panel's LCD ink and glass colours and enlarged 2x. The originals stay as the source captures.

Frames supplied by AveyCole from the running firmware (screenshots, 4x enlarged): `startup`, `genie` (Sequence Genie), `scale` (Scale Setup), `scramble`, `lfo`, `home` and `pattern-a03`. Each was cut to its 128 x 64 pixels (every 4 x 4 block was uniform, so no pixel was altered), then recoloured and enlarged 2x like the two frames above. The build they came from is not recorded; the startup frame reads 2.56. `arp` (Retrig Setup) and `settings` (Config Menu) were supplied too. The home page display cycles through all of them in the order of its `data-lcd` list (a duplicate of `home` was left out).


Release 2.75 captures (`source275/` and `*-275-lcd.png`): generated from exact Full SHA-256 9028789da5ca04f29a251a540c1fc83c52d1831d44cd4f2c74db3be830de2762. `render_song_top.py`, `render_song_grid.py`, `render_machine_confirm.py`, and `render_release_features.py` execute the actual ColdFire UI/Bitmap/font routines. Genie uses the dispatcher found and signature-checked in this image, not a recompiled prototype. Song rows are demonstration data. LCD exports preserve each native pixel and use the existing panel colours; no labels are recreated in HTML. Homepage cycle: Mod Setup, Sequence Genie, Song, Global/Mac, POTS selector.
