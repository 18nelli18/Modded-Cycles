Supermodel 2.64 native LCD captures

Rendered from the released Full firmware using tools/emu/render_song_top.py and render_song_grid.py. These execute the native ColdFire UI drawing code and capture its 128 x 64 framebuffer. PNGs retain integer pixel enlargement. The Song screen shows example rows and mute states. No screen labels were recreated in HTML.

The `*-lcd.png` files are the same two captures converted for the home page: each 128 x 64 pixel is recoloured to the panel's LCD ink and glass colours and enlarged 2x. The originals stay as the source captures.

Frames supplied by AveyCole from the running firmware (screenshots, 4x enlarged): `startup`, `genie` (Sequence Genie), `scale` (Scale Setup), `scramble`, `lfo`, `home` and `pattern-a03`. Each was cut to its 128 x 64 pixels (every 4 x 4 block was uniform, so no pixel was altered), then recoloured and enlarged 2x like the two frames above. The build they came from is not recorded; the startup frame reads 2.56. `arp` (Retrig Setup) and `settings` (Config Menu) were supplied too and are not used on the home page yet.
