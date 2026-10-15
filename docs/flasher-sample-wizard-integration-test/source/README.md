# Sample Wizard — full Supermodel integration test

Experimental combined profile. Standalone Sample Wizard was verified by the user; the combination awaits hardware testing. The page supplies recipes and MIT code, and requires the user’s official Model:Cycles 1.13 and Syntakt 1.42 files. No user samples or firmware images are supplied.

Sampler source: TinyGregAudio/Model-TG 70b39dd6787770ebefc7a2d78dea1678ec012679 (MIT). Slice varispeed: roterodamus/Model-TG 0c567d8c9e3d0c61837e1d91ac2f5c747ea9763f (MIT). WAVE and ACID fade fix: Kevin Shallvari; see the adjacent WAVE/Kevin licenses. ChordKeys: Nico Heuser; see LICENSE-ChordKeys.txt. MACRO/Braids and ACID/Open303 license texts are included. Control All Config: durchgemacht. Integration and own wizard-hat bitmaps: A.V. fork.

The assembler retains unused TG routines but installs no Model-TG master FX or replacement stock-voice DSP. Local slide and scale-lock hooks are enabled for the integration profile. The sampler and WAVE share transfer identity/browser routing, while machine buffers remain separate.

The ChordKeys bootstrap reserves the new complete Wizard code range; seven filesystem cache blocks are excluded from the LRU. Syntakt code is extracted only in the client from the user's official file. Source scripts reference development fixtures and are supplied for review; the flasher contains generated recipes and guarded hashes.
