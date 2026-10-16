# Per-track Filter compatibility test

This isolated test flasher keeps the Model-TG option out because its separate filter implementation conflicts with Per-track Filter. Per-track Filter is intended to be selectable with Second LFO, Sample Wizard, Sample Preview, and Synth Attack. The filter controls use k24–27 and save bytes +84/+86; Second LFO keeps k28–32 and +88–91.

The page also includes the prior machine-resolver test for Syntakt, MACRO, and TINY. The updated combination has not yet been hardware verified. Main is unchanged.
