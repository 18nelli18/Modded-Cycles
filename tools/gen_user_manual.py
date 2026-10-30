"""Manuel imprime2.64 : contenu present, couverture vectorielle et controle PDF."""
from pathlib import Path
import json,re,copy
from html import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1];W=R/'output/manual264';W.mkdir(parents=True,exist_ok=True)
OUT=R/'output/pdf/Supermodel-2.64-Manual.pdf';OUT.parent.mkdir(parents=True,exist_ok=True)
DATA=json.loads((R/'tools/shortcut_guide_content.json').read_text(encoding='utf-8'))
assert DATA['release']=='2.64'
for name,file in [('Body','calibri.ttf'),('Bold','calibrib.ttf'),('Italic','calibrii.ttf'),('Light','calibril.ttf')]:
 pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Italic',boldItalic='Bold')
INK=colors.HexColor('#182621');GREEN=colors.HexColor('#305c4b');MUTED=colors.HexColor('#53635b');LINE=colors.HexColor('#c4cfc8');PALE=colors.HexColor('#eef2ef')
WIDTH=510
styles={
 'lead':ParagraphStyle('lead',fontName='Light',fontSize=13,leading=17,textColor=MUTED,spaceAfter=15),
 'body':ParagraphStyle('body',fontName='Body',fontSize=11.2,leading=15.1,textColor=INK,spaceAfter=8),
 'h2':ParagraphStyle('h2',fontName='Bold',fontSize=13,leading=16,textColor=GREEN,spaceBefore=12,spaceAfter=6,keepWithNext=True),
 'h1':ParagraphStyle('h1',fontName='Bold',fontSize=27,leading=31,textColor=INK,spaceAfter=9),
 'kicker':ParagraphStyle('kicker',fontName='Bold',fontSize=9,leading=12,textColor=GREEN,spaceAfter=6),
 'cell':ParagraphStyle('cell',fontName='Body',fontSize=10.7,leading=13.5,textColor=INK),
 'small':ParagraphStyle('small',fontName='Body',fontSize=9.5,leading=12.3,textColor=MUTED,spaceAfter=7),
 'call':ParagraphStyle('call',fontName='Body',fontSize=11,leading=14.5,textColor=INK),
}
pages=[]
def P(s):return ('p',s)
def H(s):return ('h',s)
def T(head,rows,widths=None):return ('t',(head,rows,widths))
def S(*items):return ('steps',items)
def C(title,text):return ('call',(title,text))
def page(group,title,lead,*blocks):pages.append(dict(group=group,title=title,lead=lead,blocks=list(blocks)))

page('START HERE','Contents & conventions','A practical reference for Supermodel 2.64 on Model:Cycles.',
 P('Use the chapter list below for a complete walkthrough, or turn to the shortcut reference when you need a particular gesture. The machine chapters describe the Full library. Machine Optional controls are grouped in their own chapter.'),
 ('contents',None),
 H('How to read the controls'),
 T(['Notation','Meaning'],[
 ['TRACK + RETRIG','Hold the first button while pressing the second.'],
 ['TRACK + turn TIME','Keep TRACK held while turning the TIME knob.'],
 ['Tap / hold','Tap means press and release promptly. Hold means keep the button pressed.'],
 ['TRIG / track pad','TRIG means one of the 16 step keys. Track pad means T1–T6.'],
 ['DATA','The LEVEL/DATA encoder. “Click DATA” means press it.'],
 ['Global > FX','Navigate to Global, then the FX row.'],
 ['Parameter lock','A value stored on a step. Hold that step and adjust the relevant control.']],[137,373]),
 H('Editions'),
 P('<b>Full</b> includes the full machine library and the shared performance, effects, filter, modulation and MIDI functions. <b>Lite</b> uses the six Model:Cycles audio machines with the shared functions. <b>Machine Optional</b> lets you choose the machines you want; the relevant chapters apply when those machines are enabled.'),
 P('This manual focuses on Supermodel’s controls and workflows. Model:Cycles’ normal pattern, sound and configuration operations remain part of everyday use.'))

page('GETTING STARTED','Your first session','Build a small pattern, shape it, and save the result.',
 H('A simple starting workflow'),
 S('Choose an audio track with a track pad. To select its machine, press <b>MACHINES</b>, then turn <b>DATA</b>.',
 'Create or load a pattern using the normal recording controls. For note-by-note entry while stopped, press <b>REC twice</b> to enter Step Recorder.',
 'Play notes to enter steps. <b>PLAY</b> advances one step; <b>STOP</b> moves back. Press <b>REC</b> again to leave Step Recorder.',
 'Adjust the machine’s sound controls. For the track filter, hold <b>MACHINES</b> and turn <b>SWEEP</b> for cutoff or <b>CONTOUR</b> for resonance.',
 'Add an effect with the track’s <b>REVERB SEND</b> or <b>DELAY SEND</b>. To choose an effect, hold <b>TRACK</b> and turn <b>SIZE</b> or <b>TIME</b>; release TRACK to apply.',
 'Use <b>Save Project</b> to preserve the project and its pattern-specific settings. Stop playback and allow saving to finish before switching off.'),
 H('Open Mod Setup'),
 P('Tap <b>SETTINGS + TRACK</b> and release both buttons. Choose <b>Global</b>, <b>Track</b> or <b>Song</b>. Turn DATA to select a row; click to edit, turn to change the value, and click again to finish. BACK leaves editing before returning to the previous level.'),
 C('Tap and hold do different jobs','A quick SETTINGS + TRACK tap opens Mod Setup. Holding the same combination runs SCRAMBLE once. With a step held, a quick tap toggles that step’s Scramble mark.'),
 H('A useful habit'),
 P('Keep track pads and TRIG keys distinct. For example, <b>TRACK + TRIG 1–6</b> changes Control All participation; it uses the step keys, not the six track pads.'))

page('SETTINGS','Global preferences','Tap SETTINGS + TRACK, choose Global, then select a row.',
 T(['Row','Choices and operation'],[
 ['Pad','Stk: a pad selects and plays. SIL: a pad selects silently; TRACK + pad selects and plays. Default: Stk.'],
 ['USB','2ch: stereo mix to the computer. 6ch: six separate mono tracks. Stop playback before changing. Default: 2ch.'],
 ['Num','Off or On. On displays numeric volume and pan values as you adjust them. Default: Off.'],
 ['Mute','Stk: momentary mute controls. LTC: TRACK + tap FUNC latches mute mode. Default: Stk.'],
 ['Dly','Stk: normal Delay Time. Div: musical divisions, including dotted and triplet positions. Default: Stk.'],
 ['DX','Off or On. Enables the diagnostic display gesture. Default: Off.'],
 ['QntM','Enable quantized mute/solo and choose its time division. Default: Off.'],
 ['Grv','Groove On/Off and Type, plus CHORD Strum. Swing sets groove strength.'],
 ['LFOs','Choose 1, 2, 3 or 4 audio LFOs per track. Default: 2.'],
 ['FX','MST shares effect selection. TRK follows the selected track for light effects; heavy effects stay shared.'],
 ['ACID','A: amp envelope. F: filter envelope. AF: both. Applies to every ACID track when ACID is installed. Default: F.']],[65,445]),
 H('Save global preferences'),
 P('BACK closes Mod Setup and saves global preferences. If playback is running, the save waits until it stops. Stop playback and allow the save to finish before powering off.'),
 C('Pattern settings use Save Project','Sidechain, Scramble checklists, FX choices and their pattern-specific controls are saved with the project. Closing Mod Setup alone does not save those project changes.'))

page('PERFORMANCE','Tracks, mute & repeat','Select and perform tracks while keeping the controls close at hand.',
 H('Mute and solo'),
 P('Set <b>Global > Mute > LTC</b>. Hold <b>TRACK</b> and tap <b>FUNC</b> to latch mute mode. Tap track pads to mute or unmute them. Tap FUNC again to leave.'),
 P('While mute mode is latched, hold <b>FUNC</b> and press a track pad to solo it. Press that pad again, or leave mute mode, to restore the previous mute state. Tracks that were already muted stay muted.'),
 P('<b>Global > QntM</b> controls quantized mute and solo. Enable it and choose a time division to place those actions on the selected timing grid.'),
 H('Choose Control All tracks'),
 P('Hold <b>TRACK</b> and press <b>TRIG 1–6</b> to toggle the audio tracks that follow Control All. The selected track always participates. To control filters across those tracks, hold <b>TRACK + MACHINES</b> and turn SWEEP or CONTOUR.'),
 H('Momentary audio beat repeat'),
 S('Hold <b>TRACK + RETRIG</b>.','Hold a <b>TRIG 1–16</b> to choose a repeat division for the included audio tracks.','Release the division key or either modifier to stop repeating.'),
 H('Latch repeat mode'),
 P('Hold <b>TRACK</b> and double-tap <b>RETRIG</b>, then release both. Hold a TRIG to repeat; release it to stop. <b>BACK</b> exits the mode. PLAY/STOP and temporary save/reload remain available.'),
 C('Stop the music and tails','One STOP preserves effect tails. Press STOP twice to invoke All Sound Off and clear reverb and delay tails.'))

page('SEQUENCING','Notes, scales & page length','Use step entry, parameter movement and musical pitch rules.',
 T(['Task','Controls and behavior'],[
 ['Step Recorder','While stopped, press REC twice. Play notes; PLAY advances and STOP moves back one step. REC leaves the mode.'],
 ['Preview a step','Hold TRIG + PAGE while stopped or paused. The step plays with its note and parameter locks.'],
 ['Parameter slide','SETTINGS + TRIG toggles a parameter slide on the step.'],
 ['Arpeggiator','FUNC + RETRIG opens its settings. Octave 0 cycles through the notes you are holding.'],
 ['Page length','FUNC + PAGE > Page Len sets 1–16 active steps per page.'],
 ['Warp','On spreads those active steps across the normal page duration. Off keeps normal step speed. The setting follows PTN or TRK scope and saves with the pattern.']],[102,408]),
 H('Scale Lock'),
 P('Open <b>FUNC + PAGE</b> and use <b>Lock</b>, <b>Scl</b> and <b>Key</b>. Choose one of 19 whole-semitone scales and a key.'),
 T(['Lock mode','Pitch behavior'],[
 ['Off','Pitch passes without scale locking.'],
 ['ORGN','Successive input notes map to successive scale degrees.'],
 ['BRDS','Pitch snaps to the nearest in-scale note. An exact tie chooses the lower note.']],[102,408]),
 P('Lock mode, scale and key save globally while playback is stopped.'),
 C('Page length example','With Page Len set to 8, Warp On stretches the eight active steps across the normal page duration. Warp Off plays those eight steps at the normal step speed.'))

page('PATTERN DESIGN','Generate, Scramble & Humanize','Three ways to shape a pattern with different amounts of control.',
 H('Sequence Genie'),
 P('Press <b>SETTINGS + PAGE</b> to open the generator for the selected track. Use DATA to navigate. Choose <b>Generate</b> to generate, or <b>Queue</b> to schedule generation. Set <b>Loop/Page</b> timing to choose when queued generation occurs.'),
 H('Set the Scramble checklist'),
 S('Select a track and tap <b>SETTINGS + TRACK</b>.','Open <b>Track > SCRM</b>.','Use DATA to toggle Pitch, Decay, Color, Shape, Sweep and Contour. Pitch/Decay default Off; the four sound controls default On.'),
 P('Each pattern keeps six track checklists. Use <b>Save Project</b> to keep them after reloading. For Sample Wizard, Scramble can use Pitch and Decay; the sample and playback-mode controls are outside its checklist.'),
 H('Scramble a sound or step'),
 P('Hold <b>SETTINGS + TRACK</b> to randomize the checked parameters once. Keeping the combination held does not keep rerolling the sound.'),
 P('To mark a step, hold its <b>TRIG</b> and quickly tap <b>SETTINGS + TRACK</b>. Marked steps use the track’s checklist without changing the base sound. Deleting the trig clears its mark and locks.'),
 H('Humanize Apply / Undo'),
 P('Open <b>Track > Human</b>. Choose a track or <b>All</b>, set <b>Tim</b> and <b>Vel</b> from 0–100, then stop playback and choose <b>Apply</b>. The timing and velocity changes are written into the pattern. <b>Undo</b> restores the previous values.'),
 C('Controlled variation','Use a short checklist when the basic sound should remain recognizable. For timing variation, Humanize writes a result into the pattern; it does not reroll notes during playback.'))

page('RHYTHM & DYNAMICS','Groove, Strum & Sidechain','Shape rhythmic feel and let one track control the level of others.',
 H('Groove and CHORD Strum'),
 P('Open <b>Global > Grv</b>. Enable Groove, then choose <b>Boom Bap, Disco, Reggae, Bongo, Caixixi, Highlife</b> or <b>Kuduro</b>. <b>SWING</b> controls its strength. With Groove Off, SWING uses the normal swing behavior and the selected groove type is remembered.'),
 P('<b>Str</b> spaces CHORD voices from <b>−80 to +80 ms</b>. The sign reverses strum direction; 0 plays the voices together. Strum works independently of Groove On/Off. Four voices spaced 80 ms apart span 240 ms.'),
 H('Set up Sidechain'),
 S('Select the source track whose trigs will drive the ducking.','Tap <b>SETTINGS + TRACK</b>, then open <b>Track > S.Chn</b>.','Check destination tracks and/or <b>Rev.</b> and <b>Del.</b> to duck effect returns. Click DATA to toggle a target.','Scroll below the targets and set Depth, Attack, Hold and Release. Save the project.'),
 T(['Control','Range and role'],[
 ['Dpt','Depth: 0–100%, in 16 levels.'],['Atk','Attack: 0–160 ms.'],['Hld','Hold: 0–120 ms.'],['Rel','Release: 10 ms–3 s.'],
 ['Mute','On: muting the source stops its Sidechain action, including exclusion by solo. Off: the source keeps driving Sidechain while muted. Default: Off.']],[65,445]),
 P('All checked targets use the source’s settings. Multiple sources apply the deepest duck on each destination. Untick every target to disable a source. Routing and controls save per source and pattern.'),
 C('Starting point','Use a four-on-the-floor source, Depth 60%, Attack 0 ms, Hold 0 ms and Release 150 ms. Sidechain routing and the DUCK delay are separate controls.'))

page('SOUND SHAPING','Filters & attack','Shape a track, or apply the same gesture across your Control All selection.',
 H('Track filter'),
 T(['Gesture','Parameter'],[
 ['MACHINES + SWEEP','Filter cutoff on the selected audio track.'],
 ['MACHINES + CONTOUR','Filter resonance on the selected audio track.'],
 ['TRACK + MACHINES + SWEEP / CONTOUR','Cutoff or resonance across the included Control All audio tracks.'],
 ['SETTINGS, then MACHINES + turn SWEEP','Choose HIGH, LOW, BAND or LO/HI. Release the modifiers to apply the filter type.'],
 ['MACHINES + DECAY','Attack on supported machines.']],[225,285]),
 H('Choose a filter for the job'),
 P('<b>LOW</b> reduces high frequencies as you lower cutoff. <b>HIGH</b> removes low frequencies. <b>BAND</b> emphasizes a band around cutoff. <b>LO/HI</b> provides the combined low/high response. Use resonance to emphasize the area around the cutoff.'),
 P('A cleared or freshly initialized sound starts at LOW, cutoff 127 and resonance 0. A saved sound keeps its stored filter type and settings. Sample Wizard uses its own internal filter.'),
 H('Modulate filter or attack'),
 P('On an LFO page, hold <b>LFO + MACHINES</b> and turn <b>DECAY</b>, <b>SWEEP</b> or <b>CONTOUR</b> to select Attack, Filter or Resonance as the destination.'),
 C('If a track is unexpectedly quiet','Check mute and solo state, volume, filter type and cutoff, then the machine’s own controls. A high-pass setting with a high cutoff can remove much of a bass sound.'))

page('MODULATION','Audio LFOs','Each audio track can use up to four LFOs.',
 H('Choose how many LFOs are active'),
 P('Open <b>Global > LFOs</b> and choose <b>1, 2, 3</b> or <b>4</b>. The default is 2. Press <b>LFO</b> repeatedly to cycle through the enabled pages. LFO3 and LFO4 use the same control layout as LFO2. Disabled LFOs stop running and keep their settings.'),
 H('Assign a destination quickly'),
 S('Open the LFO page you want to edit.','Hold <b>LFO</b> and turn the knob for the destination.','For Attack, Filter or Resonance, also hold <b>MACHINES</b> and turn DECAY, SWEEP or CONTOUR.'),
 H('Polarity and trigger mode'),
 T(['Setting','Operation'],[
 ['Bi','Bipolar modulation, moving to both sides of the destination’s base value.'],
 ['Uni','Unipolar modulation, following the sign of Depth.'],
 ['Mode','Choose FRE, TRG, HLD, ONE or HLF in the LFO menu.']],[75,435]),
 P('All enabled LFO banks participate in sound copy, sound clear and sound Undo.'),
 H('Keep your modulation'),
 P('<b>Save Project</b> preserves the pattern and track LFO settings, including the complete LFO2 setup and the LFO3/4 banks. Stop playback and allow saving to finish before powering off.'),
 C('Sound exports and project storage','Ordinary Elektron sound and SysEx exports do not carry every LFO bank setting. Use Save Project for the complete pattern setup.'),
 H('MIDI tracks'),
 P('MIDI Out has its own two LFOs that send MIDI CC values. Their destinations and editing workflow are described in the MIDI chapters.'))

page('EFFECTS','Choose & route effects','Each pattern has a reverb slot and a delay slot. Track sends set how much signal reaches them.',
 H('Choose an effect'),
 S('Hold <b>TRACK</b> and turn <b>REVERB SIZE</b> for the reverb slot, or <b>DELAY TIME</b> for the delay slot.','Turn left to move up the list; turn right to move down. Browse while keeping TRACK held.','Release <b>TRACK</b> to apply the highlighted choice. Press <b>BACK</b> to cancel.'),
 T(['Reverb slot','Delay slot'],[[a,b] for a,b in zip(['GATED','HALL','ROOM','PS1','REVERB','CHORUS 1','CHORUS 2','RING MOD'],['PHASER','DUCK','DUB','POTS','PING PONG','DELAY','CRUSH 1','CRUSH 2'])],[255,255]),
 H('MST and TRK'),
 P('Open <b>Global > FX</b>. <b>MST</b> uses shared effect selection. <b>TRK</b> lets the same selection gestures follow the selected track for light effects. Heavy reverbs and delays remain shared, including POTS. Use each track’s SEND to set its amount.'),
 H('Save the pattern’s effects'),
 P('Use <b>Save Project</b> to keep selected types, effect controls and extra sends. Blank patterns use standard Reverb and Delay. A queued pattern applies its effect choices when it begins playing.'),
 P('Track send controls support parameter locks. Effect-specific controls do not all have parameter-lock or LFO destinations; use the track sends when you need per-step effect amounts.'),
 C('Tails','One STOP leaves tails playing. Double STOP clears reverb and delay tails, including PS1 and POTS.'))

page('EFFECTS / REVERB SLOT','Reverb, chorus & ring modulation','Use REVERB SEND for the amount from each track.',
 T(['Effect','SIZE','FUNC + SIZE'],[
 ['REVERB','Size; INF at maximum','Tone: −64 to +63'],
 ['GATED','Gate time','Pre-delay'],
 ['HALL','Decay','Tone'],
 ['ROOM','Decay','Tone'],
 ['PS1','Decay','Tone'],
 ['CHORUS 1 / 2','Speed','Depth'],
 ['RING MOD','Frequency','Depth']],[119,192,199]),
 H('Choose a space'),
 P('<b>REVERB</b> provides the standard size and tone controls, with INF at maximum Size. <b>HALL</b> has a wide stereo tail with long reflections. <b>ROOM</b> gives compact stereo ambience. <b>PS1</b> has a dark, grainy, PlayStation-inspired character.'),
 H('GATED'),
 P('SIZE sets a gate time of about <b>40 ms–6.7 s</b> after the input falls quiet. <b>FUNC + SIZE</b> sets pre-delay from <b>0–568 ms</b>; <b>SETTINGS + SIZE</b> sets tone. For a snare, try gate time 16–32 and pre-delay around 25–40 ms.'),
 H('Chorus and Ring Mod'),
 P('<b>CHORUS 1</b> and <b>CHORUS 2</b> use Speed and Depth from 0–127. <b>RING MOD</b> gives metallic sine-wave ring modulation. Its Frequency and Depth are shared by tracks in the pattern; automate track amounts with REVERB SEND locks.'),
 C('Another way to reach tone','For HALL, ROOM, PS1 and RING MOD, SETTINGS + SIZE also accesses the secondary control. GATED uses SETTINGS + SIZE specifically for Tone.'))

page('EFFECTS / DELAY SLOT','Delay, phaser & crusher','Use DELAY SEND for the track amount; Time and its modifier control the selected effect.',
 T(['Effect','TIME','FUNC + TIME'],[
 ['DELAY','Time','Feedback'],['PING PONG','Time','Feedback'],['DUB','Time','Feedback'],['POTS','Time','Feedback'],['DUCK','Time','Feedback'],['PHASER','Rate','Depth'],['CRUSH 1 / 2','Rate: 0–127','Bits: 2–16']],[119,192,199]),
 H('Echo character'),
 P('<b>DELAY</b> is the standard delay. <b>PING PONG</b> alternates echoes left and right; listen through both outputs or headphones. <b>DUB</b> produces strongly filtered stereo echoes that narrow progressively in the feedback loop.'),
 P('<b>POTS</b> produces telephone-style mono echoes on both output channels. Use Time, Feedback and the track’s Delay Send normally. It is one shared delay in MST and TRK. Save Project keeps the selection; double STOP clears its tail.'),
 H('DUCK'),
 P('The wet signal ducks while the send input plays and swells back afterward. Hold <b>FUNC first, then TRACK</b>: TIME sets <b>Amount</b> and DELAY SEND sets <b>Release</b>. Try Amount 127 and Release 32–64 on sparse notes. Amount 0 gives standard Delay behavior.'),
 H('Phaser and crushers'),
 P('<b>PHASER</b> is a two-stage stereo phaser. TIME sets Rate; FUNC + TIME sets Depth. For Feedback, hold <b>FUNC first, then TRACK + TIME</b>, or use <b>SETTINGS + TIME</b>.'),
 P('<b>CRUSH 1</b> leaves direct sound clean. <b>CRUSH 2</b> blends direct clean and crushed sound. DELAY SEND becomes Crush Send; these modes produce no delay echoes. Lower Rate or Bits makes the texture rougher. Rate spans about 750 Hz–48 kHz.'),
 P('<b>Global > Dly > Div</b> shows musical divisions for Delay, including dotted and triplet values. Matching positions follow exact tempo divisions; other positions retain their continuous timing.'))

catalog=[
 ['KICK / SNARE / METAL / PERC / TONE / CHORD','The six Model:Cycles audio machines.'],
 ['Sample Wizard','Sample playback, slicing, granular, stretch, pluck and wavetable modes.'],
 ['SD Vintage','Tunable snare with a metallic body.'],['Clap Vintage','Clap synthesis with body and attack spacing.'],['SY Toy','Tuned percussion with impact and evolving partials.'],['SY Bits','Digital oscillators, detune and rate/bit reduction.'],['Swarm','Three detuned saws for leads and basses.'],['MACRO','47 synthesis models, from classic tones to textures.'],['ACID','Resonant bass synthesis with envelope and drive.'],['WAVE','Wavetable scanning and custom table import.'],['Feral','Ten synthesis models for characterful electronic sounds.'],['ELDER','Chip-style synthesis for melodies, basses and percussion.'],['TINY','52 synthesis models with Tone, Mod and Excite.'],['Shadow','Pulsar/noise synthesis with Grain, Density, Spread and Chaos.'],['SPEAK','128-word speech synthesis.'],['RETROSYN','Six chip oscillator styles, fixed arpeggios and four-bit PUNCH.'],['PUNCH','Twelve FM percussion models.'],['ESTUS','Eight drum engines with sound-shaping and advanced controls.'],['MIDI Out','Notes, chords, CC controls and two MIDI LFOs for external instruments.']]
page('MACHINES','Machine library','Press MACHINES, then turn DATA to choose a machine.',
 T(['Machine','Sound and purpose'],catalog,[159,351]),
 P('Full includes this library. Lite uses the six Model:Cycles audio machines and the shared performance, effects and modulation functions. Machine Optional follows your enabled machine selection.'),
 P('Numeric sound controls commonly span 0–127, with 64 as the midpoint. PITCH and FINE are centered: displayed 0 means no pitch offset. Model selectors and ratio controls use their own scales.'))

page('MACHINES / SYNTHESIS','MACRO, ACID & WAVE','Three approaches to pitched sounds: multi-model synthesis, resonant bass and wavetable motion.',
 H('MACRO'),
 P('Choose among <b>47 models, numbered 0–46</b>; the display shows the model name and number. Different models respond differently to the sound controls, so explore one model at a time.'),
 T(['Gesture','Function'],[['SETTINGS + PITCH','Fine pitch adjustment.'],['FUNC + PITCH','Lo-Fi: left reduces sample rate; right reduces bit depth; center is OFF.']],[180,330]),
 H('ACID'),
 T(['Knob','Function'],[['COLOR','Cutoff'],['SHAPE','Resonance'],['SWEEP','Envelope modulation amount'],['CONTOUR','Drive'],['DECAY','Envelope decay']],[100,410]),
 P('In <b>Global > ACID</b>, choose <b>A</b> for amp envelope, <b>F</b> for filter envelope, or <b>AF</b> for both. This one setting applies to every ACID track and saves globally; F is the default. With A/AF, Gate Off allows amp decay during a held note; Gate On sustains until note-off.'),
 P('Velocities <b>97–127</b> add progressive filter and level accent. Velocities 0–96 use the unaccented response. Velocity also controls note volume.'),
 H('WAVE'),
 P('<b>AV-WAVE-Morph</b> supplies 16 morphable frames as a starting table. <b>COLOR</b> selects table position; <b>SHAPE</b> adds envelope movement. Import custom tables for individual tracks. In the browser, BACK goes up one folder; at <b>/Wavetables</b>, BACK closes the selector.'))

page('MACHINES / CHARACTER','ELDER, TINY, Shadow & Feral','Choose a model or texture, then shape its movement.',
 T(['Machine','COLOR','SHAPE','SWEEP','CONTOUR'],[
 ['ELDER','Wave','Warp','Noise','Motion'],['TINY','Tone','Model 0–51','Mod','Excite'],['Shadow','Grain','Density','Spread','Chaos']],[80,104,114,104,108]),
 H('ELDER'),
 P('A chip-style synth inspired by Junior by Fors. Pitch, Fine, Decay, PUNCH and Gate are available. A simple starting point is Wave 0, Warp 0, Noise 0, Motion 0 and Decay 50.'),
 H('TINY'),
 P('Explore its 52 models with SHAPE. Tone, Mod and Excite shape the selected model. Start with Tone 64, Model 0, Mod 64, Excite 32 and Decay 60, then vary one control at a time.'),
 H('Shadow'),
 P('A pulsar/noise synth inspired by Opal Dust by Fors. Grain, Density, Spread and Chaos control its texture. PUNCH adds distortion and a ratcheting attack. Pitch, Fine, Decay and Gate remain available.'),
 H('Feral'),
 P('Feral by Glycinate provides ten synthesis models for unusual electronic sounds. Choose a model and use its sound controls to explore its character. Use the track filter, LFOs and sends to shape the result further.'),
 H('RETROSYN'),
 P('A chip synth with six SHAPE models, fixed arpeggios and four-bit PUNCH. COLOR, SWEEP and CONTOUR shape the chosen sound. Pitch, Decay and Gate are available.'),
 C('Starting values','The minimum position is not a universal clean-sound setting. A model selector, a ratio control and a continuous timbre control each have their own meaning.'))

page('MACHINES / PERCUSSION','PUNCH, ESTUS & SY Bits','Use dedicated sound engines for tuned percussion, drums and digital textures.',
 H('PUNCH'),
 P('SHAPE chooses <b>KIK, TOM, BNG, CNG, TAI, TIM, MAR, DJB, BLK, GNG, BUB</b> or <b>ZAP</b>. COLOR controls timbre; SWEEP chooses the ratio, and <b>FUNC + SWEEP</b> adjusts between ratios. CONTOUR and DECAY shape the sound.'),
 P('A starting point: Color 64, KIK, ratio 4:1, Contour 40 and Decay 50.'),
 H('ESTUS'),
 P('SHAPE selects <b>KICK, TOM, PERC, SNARE, CLAP, CL HAT, OP HAT</b> or <b>CYMBAL</b>. The display labels follow the engine.'),
 T(['Engine group','COLOR / SWEEP / CONTOUR'],[
 ['KICK, TOM, PERC','Pitch Amount / Pitch Decay / FM Drive'],['SNARE','Noise Mix / Noise Tone / Snap'],['CLAP','Spread / Tone / Claps'],['CL HAT, OP HAT, CYMBAL','Tune / Noise / Brightness']],[172,338]),
 P('Hold <b>SETTINGS</b> and turn <b>COLOR / SHAPE / SWEEP / CONTOUR</b> for <b>Waveform / FM Ratio / Drive / Transient</b>. You can edit during playback or hold a step with the same gesture to lock the setting. Some engines do not use every advanced control.'),
 H('SY Bits'),
 P('Plain <b>COLOR</b> adjusts whole-semitone detune. <b>FUNC + COLOR</b> adjusts the fractional part in <b>0.01-semitone</b> steps across <b>−24.00 to +24.00</b>. These values support sound saving and parameter locks.'),
 P('<b>SD Vintage</b>, <b>Clap Vintage</b> and <b>SY Toy</b> offer snare, clap and tuned-percussion starting points. <b>Swarm</b> provides three detuned saws for pitched parts.'))

page('MACHINES / SAMPLING','Sample Wizard','Audition, lock and transform samples from the track’s browser.',
 H('Preview and sample locks'),
 S('Press <b>FUNC + MACHINES</b> to open sample selection.','Highlight a sample. Press the track pad or a keyboard TRIG to audition it; scrolling alone stays silent.','To lock it to a step, keep the browser open with the desired sample highlighted, then hold that step’s <b>TRIG + MACHINES</b>.'),
 H('Playback modes'),
 P('<b>SETTINGS + MACHINES</b> selects <b>One-Shot, Loop, Slice, Granular, Stretch, Pluck</b> or <b>Wavetable</b>. <b>SETTINGS + PUNCH</b> opens options for the current mode.'),
 H('Slice editing'),
 P('Use <b>FUNC + a step key</b> to play upper slices. <b>FUNC + click DATA</b> removes a slice marker. Marker knobs can snap to zero crossings.'),
 H('Resample'),
 P('On a Sample Wizard track, press <b>SETTINGS + REC</b> to open Resample. Choose recording options and save the resulting take from that menu.'),
 H('Read the display'),
 P('The home screen shows the sample name, a wide waveform, the selected track, duration and rectangular volume segments. The segments show the track’s volume setting; they are not an audio-level meter. A Start/Position marker appears where the playback mode uses it.'),
 C('Before locking a sample','Open the sample browser first and highlight the exact sample you want. The lock gesture uses the highlighted browser entry.'))

page('MACHINES / VOICE','SPEAK','Build phrases from a 128-word library while controlling pitch and delivery.',
 T(['Control','Function'],[['COLOR','Voice / formant character'],['SHAPE','Word index 0–127; display shows the word and index'],['SWEEP','Speed: 64 is normal, lower is slower'],['CONTOUR','Articulation']],[110,400]),
 P('Word changes take effect at the next trig. Voice, Speed and Articulation remain live. Pitch changes independently of word speed. Decay, Fine, PUNCH, Gate, Attack, filters and FX sends are available.'),
 H('Program a phrase'),
 S('Choose SPEAK and begin with <b>Decay 127</b> so complete words can play. A useful level starting point is <b>Vol+Dist 60</b>, with PUNCH off.','Place trigs with enough space for each word. Hold each trig and turn <b>SHAPE</b> to lock its word.','Lock Pitch and other controls as needed. If words run together, leave more space or increase Speed.'),
 H('Example sentence'),
 T(['Word','Index'],[['HELLO','31'],['I','0'],['AM','62'],['A','17'],['ROBOT','113'],['I','0'],['LOVE','35'],['MUSIC','106']],[255,255]),
 P('Word and the ordinary sound parameters support locks and LFO destinations. COLOR, SHAPE, SWEEP and CONTOUR use MIDI CC 16, 17, 18 and 19. The complete indexed word list appears in the reference pages.'))

page('MIDI OUT / NOTES','Connect & sequence MIDI','Use MIDI Out as a silent track for an external instrument.',
 H('Set the destination'),
 S('Choose <b>MIDI Out</b> in MACHINES.','Press <b>FUNC + TRACK</b> to open Track Setup.','Select a row with DATA, click before editing, turn to change it, then click again. BACK exits.'),
 T(['Setting','Choices'],[['Channel','1–16 or Global. This is the outgoing channel.'],['Output','Global, Off, USB, DIN or Both.'],['KbT','Keyboard transpose.'],['Pad Note','The note sent by the track pad.']],[102,408]),
 H('Play from an external keyboard'),
 P('In <b>CONFIG > MIDI</b>, enable note reception and use the track receive channel or auto channel. Incoming notes follow the chosen Output. Track Setup’s Channel sets the outgoing destination, not the receive channel.'),
 P('Live recording captures notes, velocity and length. For step entry, stop playback, press <b>REC twice</b>, then play and release notes to advance. Normal note/grid controls and <b>FUNC + PAGE</b> pattern-length editing are available.'),
 H('Arpeggiate and change machines'),
 P('Open <b>FUNC + RETRIG > Arp</b>. Enable <b>A. On</b>, or hold RETRIG, to arpeggiate incoming notes. When you choose an audio machine, held and sequenced MIDI notes are released on their original channel and port.'),
 C('OUT and THRU together','Set CONFIG > MIDI > PORTS > OUT/THRU to THR. FUNC + click DATA toggles the Cycles’ own outgoing MIDI while retaining incoming MIDI Thru.'))

page('MIDI OUT / CONTROL','CC knobs & MIDI LFOs','Assign nine knobs and two LFOs to MIDI controller numbers.',
 H('Assign and record CC controls'),
 S('On MIDI Out, hold <b>SETTINGS</b> and turn one of the <b>nine gray knobs</b>. Choose <b>OFF</b> or <b>CC 0–127</b>.','Turn the assigned knob alone to send its value, from 0–127.','Hold a <b>TRIG</b> and turn the assigned knob to store a lock. An empty step becomes lock-only. Live recording captures knob movement.'),
 P('Every lock retains both its CC number and its value. Chance and Swing keep their usual controls. The LFO Speed knob edits the currently open MIDI LFO.'),
 H('Edit the two MIDI LFOs'),
 P('Press <b>LFO</b> to cycle through <b>LFO 1</b>, <b>LFO 2</b> and the track screen. Use DATA to select a field, click to edit, and BACK to leave.'),
 T(['Field order','Controls'],[['1–4','Wav, Mul, Dst, Dep'],['5–8','Speed, Fade, Phase, Mode']],[120,390]),
 P('<b>Dst</b> is OFF or CC 0–127. Editing the destination suspends that LFO’s output until you leave the field. Other assigned knobs continue sending CC.'),
 H('Quick LFO assignment'),
 P('Hold <b>LFO</b> and turn an assigned CC knob to choose its destination. Continue turning for depth.'),
 H('Save'),
 P('Use the normal project or permanent quick-save operation to preserve MIDI settings and locks. Temporary save/reload is available for performance snapshots.'))

page('STORAGE & CONNECTIONS','Saving, USB & diagnostics','Match the save operation to the settings you want to keep.',
 T(['Operation','What it does'],[
 ['Save Project','Keeps the project, including pattern FX choices, Sidechain routing, Scramble checklists and the pattern/track LFO setup.'],
 ['Hold FUNC + SETTINGS','Opens the permanent pattern-save action.'],
 ['Short FUNC + SETTINGS','Stores a temporary pattern snapshot.'],
 ['FUNC + PATTERN','Reloads the temporary snapshot. Available in latched repeat mode.'],
 ['BACK from Mod Setup','Saves global preferences; a pending save waits for playback to stop.']],[173,337]),
 H('USB audio'),
 P('In <b>Global > USB</b>, choose <b>2ch</b> for the stereo mix or <b>6ch</b> for six separate mono tracks. The six tracks are sent before pan and without stereo effect returns. Stereo audio from the computer to Cycles is available in either mode.'),
 P('Stop playback before changing USB mode. The audio device reconnects; select the resulting channel layout in your DAW if needed.'),
 H('Delay divisions'),
 P('<b>Global > Dly > Div</b> displays musical divisions for Delay. It includes dotted and triplet values; only matching positions use exact divisions of the tempo.'),
 H('DX diagnostics'),
 P('Set <b>Global > DX > On</b>. Tap FUNC, press it again within <b>350 ms</b>, hold for at least <b>0.5 seconds</b>, then release. Other controls cancel the gesture. The display shows/resets <b>A/P/O/N</b>: average CPU, peak CPU, overruns and governor voice drops.'),
 C('Before powering off','Stop playback, save the project when needed, and allow pending preference saves to finish. Temporary snapshots are for performance recall, not a substitute for a permanent save.'))

page('MACHINE OPTIONAL','Optional controls','These controls apply when their corresponding Machine Optional choices are enabled.',
 H('LEGACY'),
 P('A six-operator FM machine using a shared <b>32-voice bank</b>. The active bank is shared by all LEGACY tracks.'),
 S('On LEGACY, press <b>FUNC + MACHINES</b>.','Turn DATA to choose a stored DX7 bank.','Click DATA to load it, or press BACK to cancel.'),
 P('Use the Machine Optional flasher’s bank importer to import banks.'),
 H('ChordKeys'),
 P('On CHORD, open <b>FUNC + RETRIG</b> and set <b>Keys On</b>. Outside grid recording, <b>TRIG 1–16</b> plays scale-based chord voicings. <b>TRACK + a track pad</b> changes track.'),
 P('In grid recording, hold a <b>TRIG</b> and press <b>T1–T6</b> to lock harmony. Repeat the same pad to restore the base harmony.'),
 H('Vinyl'),
 T(['Gesture','Parameter'],[['REVERB SEND','Vinyl amount from the track'],['SIZE','Crackle'],['FUNC + SIZE','Warble Amount'],['Hold FUNC first, then TRACK + SIZE','Warble Speed']],[263,247]),
 C('Modifier order','For Warble Speed, hold FUNC before TRACK. This keeps the gesture distinct from entering latching mute mode.'))

quick=[
 ['Mod Setup','Tap SETTINGS + TRACK','Global preferences and track tools'],['Machine selection','Press MACHINES, then turn DATA','Choose a machine'],['Step Recorder','Stopped: REC twice','PLAY forward; STOP back; REC exit'],['Step preview','TRIG + PAGE','Audition with note and locks'],['Parameter slide','SETTINGS + TRIG','Toggle slide'],['Sequence Genie','SETTINGS + PAGE','Generate or queue'],['Scramble sound','Hold SETTINGS + TRACK','Use track checklist'],['Scramble step','TRIG + quick SETTINGS + TRACK','Toggle step mark'],['Mute latch','TRACK + tap FUNC','Requires Mute: LTC'],['Solo','Latched mute: FUNC + track pad','Press again to restore mutes'],['Control All tracks','TRACK + TRIG 1–6','Toggle participation'],['Audio repeat','TRACK + RETRIG, then TRIG','Hold the repeat division'],['Repeat latch','TRACK + double-tap RETRIG','BACK exits'],['Filter cutoff / resonance','MACHINES + SWEEP / CONTOUR','Add TRACK for Control All'],['Filter type','SETTINGS, then MACHINES + SWEEP','Release to apply'],['Attack','MACHINES + DECAY','Supported machines'],['Reverb / delay choice','TRACK + SIZE / TIME','Release to apply; BACK cancel'],['LFO destination','LFO + destination knob','Add MACHINES for filter/attack'],['Arpeggiator','FUNC + RETRIG','Open Arp settings'],['Scale / page length','FUNC + PAGE','Lock, scale, key, Page Len, Warp'],['Permanent quick save','Hold FUNC + SETTINGS','Pattern-save action'],['Temporary save / reload','Short FUNC + SETTINGS / FUNC + PATTERN','Performance snapshot'],['Silence effect tails','STOP twice','All Sound Off']]
page('REFERENCE','Everyday shortcuts','Hold the first button while pressing the second button or turning the knob.',T(['Task','Gesture','Result'],quick,[125,220,165]))

page('REFERENCE / SPEAK','Word library','Choose the index with SHAPE, or parameter-lock a word on each step.',
 ('words',None),P('For speech controls and an example phrase, see the SPEAK chapter.'))

page('REFERENCE','Find it quickly','An alphabetical guide to the manual.',('index',None),
 H('A saving reminder'),P('Use Save Project for pattern settings. Global preferences save while stopped. Temporary save/reload is a performance snapshot.'),
 H('About this edition'),P('Supermodel 2.64 • Model:Cycles • English print edition • 30 October 2026.'),
 P('Engine acknowledgments include Glycinate (Feral), Fors (inspiration for ELDER and Shadow), Emilie Gillet (MACRO/Braids and scale quantization), 100demons (PUNCH), and durchgemacht and Claude (POTS). POTS uses the MIT-licensed model27 DSP.'),
 P('Control names in this manual follow the machine’s panel and display. Machine-specific chapters apply when that machine is installed.'))

conventions=pages[0]['blocks'][3:]
pages[0]['blocks']=pages[0]['blocks'][:2]
pages.insert(1,dict(group='START HERE',title='Buttons & editions',lead='Read gestures consistently and find the chapters that apply to your build.',blocks=conventions+[
 H('Acknowledgments'),P("Glycinate, Fors.Fm, PPPCCC, DavidCaruso, Emilie Gillet, Durchgemacht, 18nelli18, and every member of the Modded-Cycles Discord server who rode with me through this. Y'all rule.")]))
pages[-1]['blocks']=[pages[-1]['blocks'][0],P('Supermodel 2.64 • Model:Cycles • English print edition • 30 October 2026.')]
at=next(i for i,p in enumerate(pages) if p['title']=='MACRO, ACID & WAVE')
pages[at]['title']='ACID & WAVE';pages[at]['lead']='Resonant bass synthesis and wavetable motion.'
pages[at]['blocks']=pages[at]['blocks'][3:]
pages[at]['blocks'].insert(4,P('<b>PUNCH</b> selects the oscillator waveform: Off is saw, On is square. For pitch slides, use overlapping note lengths so the sound moves into the following note.'))
pages.insert(at,dict(group='MACHINES / MULTI-MODEL',title='MACRO',lead='Explore 47 synthesis models with four sound controls, fine tuning and Lo-Fi.',blocks=[
 P('Choose MACRO in MACHINES, then turn <b>SHAPE</b> to select a model from <b>0–46</b>. The screen shows the model name and number. Model choice supports step parameter locks.'),
 T(['Panel knob','Displayed function','Use'],[
 ['COLOR','Timbre','Sets the model’s principal timbre parameter.'],
 ['SHAPE','Model','Chooses one of the 47 synthesis models.'],
 ['SWEEP','Color','Sets the model’s second sound parameter.'],
 ['CONTOUR','Env Timbre','Sets the amount of envelope movement applied to Timbre. At 0, this envelope amount is zero.']],[100,120,290]),
 H('Pitch and envelope'),P('Use PITCH and note entry to tune the sound. Hold <b>SETTINGS + turn PITCH</b> for fine pitch. DECAY, Gate and PUNCH are available for shaping the note.'),
 H('Lo-Fi'),P('Hold <b>FUNC + turn PITCH</b>. The center position is <b>OFF</b>. Turn left to reduce sample rate, or right to reduce bit depth. Choose the side according to the texture you want.'),
 H('A useful way to explore'),S('Pick a model with SHAPE.','Keep CONTOUR low while exploring COLOR and SWEEP.','Raise CONTOUR and adjust DECAY to hear envelope movement in the timbre.','Use Lo-Fi for rate or bit-depth texture, then add track filter or effects as needed.'),
 C('Model behavior','Different models use their timbre parameters differently. A knob’s minimum position is not a universal neutral setting.')]))


# Chapitres2.64 : operations presentes, sans historique des corrections.
by_title={p['title']:p for p in pages}
by_title['Global preferences']['blocks'][0][1][1].append(['JUMP','Off / On. With On, PATTERN then FUNC + TRIG jumps immediately and keeps playback position. Default: Off. Saves globally.'])
for p in pages:
 for i,(kind,value) in enumerate(p['blocks']):
  if kind=='p' and 'For pitch slides, use overlapping' in value:
   p['blocks'][i]=P('<b>PUNCH</b> selects the oscillator waveform: Off is saw, On is square. Overlapping note lengths link ordinary notes according to the track glide and legato settings. See ACID articulation for the physical controls.')
  if kind=='p' and 'The home screen shows the sample name' in value:
   p['blocks'][i]=P('The home screen shows the sample name, waveform, track and duration. Volume segments show the track volume setting. During playback, pitch, start, end and other parameter locks take priority over CTRL-ALL; CTRL-ALL still edits the base sound for unlocked notes.')

def add_after(title,chapter):
 pages.insert(next(i for i,p in enumerate(pages) if p['title']==title)+1,chapter)
def chapter(group,title,lead,*blocks):return dict(group=group,title=title,lead=lead,blocks=list(blocks))
add_after('Notes, scales & page length',chapter('SEQUENCING / LIVE EDITING','Pattern jumps & trig selection','Choose patterns and edit groups of existing steps.',
 H('Direct Pattern Jump'),
 S('Open Mod Setup with <b>SETTINGS + TRACK</b>. Choose <b>Global &gt; JUMP &gt; On</b>.','Press <b>PATTERN</b>, then <b>FUNC + the pattern TRIG</b> to jump immediately while keeping playback position.'),
 P('With JUMP Off, pattern changes use normal timing. The preference saves globally while stopped; Off is the default.'),
 H('Select trigs without holding them'),
 S('Press <b>TRACK + PAGE</b>, then release both buttons.','Tap existing note trigs, lock trigs or steps containing parameter locks to select or deselect them. Selected steps blink.','Use the usual held-step editing controls on the selection. <b>PAGE</b> changes page while keeping the selection.','In selection mode, <b>FUNC + PAGE</b> selects all eligible trigs or clears the selection. Press <b>TRACK + PAGE</b> again to leave and clear it.'),
 C('TRACK is momentary','Track selection is active only while TRACK is physically held. Releasing TRACK leaves trig selection available. Empty steps are not created by selecting; steps hidden by Page Len are excluded. Selection mode starts Off after power-up.')))
add_after('Pattern jumps & trig selection',chapter('SONG / EDITOR','Build a song','An arrangement of patterns, repeats and six track mutes.',
 S('Tap <b>SETTINGS + TRACK</b> to open Mod Setup.','Choose <b>Song</b> beside Global and Track, then press <b>DATA</b>.','While stopped, turn <b>DATA</b> to select a row in the four-row grid.'),
 T(['Control','Action'],[['PITCH','Choose the row pattern, A01-F16.'],['DECAY','Set the row repeats, 1-64.'],['TRIG 1-6','Toggle each track mute for the selected row.'],['PAGE','Insert a copy after the selected row.'],['FUNC + PAGE','Delete the selected row; at least one row remains.'],['Click DATA','Choose STOP or LOOP at the end. FUNC + DATA also works.'],['BACK','Leave the Song editor.']],[135,375]),
 C('Stop before editing','Row changes are available while playback is stopped and Song is inactive. If a song is active or paused, press STOP twice to cancel it before editing. Song is not inside Global.')))
add_after('Build a song',chapter('SONG / PLAYBACK','Play and save a song','Use native pattern-chain playback for the arrangement.',
 H('A simple arrangement'),
 P('Set row 1 to <b>A01 x4</b>. Press PAGE to insert a copy, then set row 2 to <b>A02 x2</b>. Set row 3 to <b>A03 x2</b>. These rows use eight expanded pattern plays.'),
 S('Choose <b>STOP</b> to end after the last row, or <b>LOOP</b> to repeat the arrangement.','Press <b>PLAY from the Song editor</b> to begin at the first row. The display follows the playing row.','Press <b>STOP</b> to pause using native transport. Press PLAY to continue. <b>STOP twice</b> cancels Song and clears reverb/delay tails.','Use <b>Save Project</b> to preserve the arrangement and the six tracks ACID glide/legato settings.'),
 H('Length and mutes'),
 P('The complete arrangement must fit <b>64 expanded pattern plays</b>: add the repeats across all rows. For example, four rows repeated 16 times each use the limit. A song that exceeds it does not start and shows the 64-play limit.'),
 P('Song mutes combine with existing track mutes. A track muted outside Song remains muted when the row permits it. Choosing a pattern chain manually cancels Song playback.'),
 C('Pattern length matters','Song follows each pattern native chain timing. An infinite chain length can hold a row indefinitely. Set a finite chain length when you want the song to advance.')))
add_after('ACID & WAVE',chapter('MACHINES / ACID','ACID articulation','Separate pitch glide, legato and envelope destination.',
 H('Set the selected track'),
 T(['Gesture','Setting'],[['SETTINGS + PITCH','Glide: OFF, or values 1-127 for approximately 50-360 ms. Default is about 50 ms.'],['SETTINGS + DECAY','Legato: left OFF, right ON. Default ON.']],[192,318]),
 P('These settings apply only to the selected ACID track and save with the project. They are track settings, not per-step parameter locks. Release SETTINGS after editing.'),
 H('Link notes with LEN'),
 P('Set a note length so it overlaps the following note. With legato On, the envelope continues across those ordinary linked notes. Glide controls how quickly pitch moves. With glide Off and legato On, pitch changes immediately without an envelope restart.'),
 P('With legato Off, ordinary notes restart the envelope. Glide can still be active. Detached notes restart the envelope regardless of legato.'),
 H('Choose the envelope destination'),
 P('<b>Global &gt; ACID</b> selects <b>A</b> for amp, <b>F</b> for filter or <b>AF</b> for both. This choice applies to all ACID tracks and saves globally; F is the default. In A/AF, Gate Off permits amp decay during a held note; Gate On sustains until note-off.'),
 C('Arpeggiator and retrig','Each arpeggiator/retrig note restarts the selected A/F/AF envelope, including when note lengths overlap. Ordinary linked notes still follow the track glide/legato settings.')))
add_after('Optional controls',chapter('MACHINE OPTIONAL / DRUMS','Machinedrum engines','TRX-B2, TRX-SD and TRX-CH are optional machine choices.',
 P('Enable the desired engines in Machine Optional and supply your own <b>Machinedrum UW OS 1.63</b> file in the flasher. Press MACHINES, then turn DATA to choose an enabled engine. The other Optional choices remain available.'),
 T(['Engine','Panel controls'],[['TRX-B2','Bass drum: PITCH = pitch; DECAY = decay; COLOR = distortion; SHAPE = dirt; SWEEP = pitch ramp; CONTOUR = hold; PUNCH = tick.'],['TRX-SD','Snare: PITCH = pitch; DECAY = decay; COLOR = snap; SHAPE = tone; SWEEP = bump; CONTOUR = bump envelope; PUNCH = clip.'],['TRX-CH','Closed hi-hat: PITCH = resonator low-pass/tuning; DECAY = decay; COLOR = metal; SHAPE = high-pass; SWEEP = resonance; CONTOUR = gap.']],[83,427]),
 P('These controls belong to the installed machine. Shared track filtering, modulation, sends and sequencing remain available. Lite contains the six stock audio machines.')))
add_after('Everyday shortcuts',chapter('REFERENCE / SEQUENCING','Song and articulation shortcuts','Physical controls for arrangement and linked notes.',
 T(['Task','Gesture','Result'],[['Song editor','SETTINGS + TRACK > Song > DATA','Open the arrangement grid.'],['Song row / pattern / repeats','DATA / PITCH / DECAY','Select row and its contents.'],['Song row mutes','TRIG 1-6','Toggle track mutes for the row.'],['Song insert / delete','PAGE / FUNC + PAGE','Copy-insert or delete a row.'],['Song end behavior','Click DATA','STOP / LOOP.'],['ACID glide / legato','SETTINGS + PITCH / DECAY','Selected ACID track only.'],['Trig selection','TRACK + PAGE','Toggle selection mode.'],['Selection all / none','Selection active: FUNC + PAGE','Select all eligible trigs or clear.'],['Pattern jump','Global JUMP On; PATTERN then FUNC + TRIG','Jump at the current position.']],[120,235,155]),
 P('Use Save Project for the song and per-track ACID settings. JUMP and the ACID A/F/AF envelope destination save globally.'),
 P('Bug reports: <link href="https://aveycole.github.io/Supermodel/bugs/" color="#305c4b">aveycole.github.io/Supermodel/bugs/</link>. Reports and follow-up discussion are collected in the shared inbox.')))

def para(text,style='body'):return Paragraph(text,styles[style])
def table(head,rows,widths=None,small=False):
 if widths is None:widths=[WIDTH/len(head)]*len(head)
 sty=ParagraphStyle('words',fontName='Body',fontSize=10.2,leading=12.2,textColor=INK) if small else styles['cell']
 data=[[para('<b>'+escape(str(x))+'</b>','cell') for x in head]]+[[Paragraph(escape(str(x)),sty) for x in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 commands=[('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,0),.7,GREEN),('LINEBELOW',(0,1),(-1,-1),.35,LINE),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]
 if small:commands.extend([('TOPPADDING',(0,1),(-1,-1),1.5),('BOTTOMPADDING',(0,1),(-1,-1),1.5)])
 t.setStyle(TableStyle(commands));return t

def cover(c):
 c.setFillColor(GREEN);c.rect(51,706,42,5,fill=1,stroke=0)
 c.setFont('Bold',10);c.drawString(51,675,'MODEL:CYCLES  /  USER MANUAL')
 c.setFillColor(INK);c.setFont('Light',52);c.drawString(48,588,'SUPERMODEL')
 c.setFont('Body',23);c.drawString(51,548,'Make it yours.')
 c.setFillColor(MUTED);c.setFont('Body',13);c.drawString(51,500,'Sounds • sequencing • performance • control')
 c.setFont('Bold',12);c.setFillColor(GREEN);c.drawString(51,469,'RELEASE 2.64')
 c.setStrokeColor(LINE);c.line(51,442,561,442)
 patterns=[{0,4,8,12},{4,12},{0,2,4,6,8,10,12,14},{3,7,11,15},{0,5,10,13},{1,6,9,14}]
 for track,pattern in enumerate(patterns):
  y=377-track*31;c.setFont('Bold',9);c.setFillColor(MUTED);c.drawString(51,y+6,f'{track+1:02}')
  for step in range(16):
   x=87+step*29.5;c.setStrokeColor(LINE);c.setFillColor(GREEN if step in pattern else colors.white)
   c.roundRect(x,y,19,19,3,stroke=1,fill=1)
 c.setFillColor(MUTED);c.setFont('Body',11);c.drawString(51,100,'A practical guide to the current controls and workflows.')
 c.setFont('Body',9);c.drawString(51,78,'English • Full / Lite / Machine Optional')
 c.drawRightString(561,78,'30 OCTOBER 2026')

def chrome(c,doc):
 c.saveState();c.bookmarkPage('page'+str(doc.page))
 if doc.page==1:cover(c);c.restoreState();return
 index=doc.page-2
 group=pages[index]['group'] if index<len(pages) else 'SUPERMODEL'
 c.setFillColor(GREEN);c.setFont('Bold',8);c.drawString(51,759,'SUPERMODEL 2.64')
 c.setFillColor(MUTED);c.setFont('Body',8);c.drawRightString(561,759,group)
 c.setStrokeColor(LINE);c.line(51,749,561,749);c.line(51,38,561,38)
 c.setFont('Body',8);c.drawString(51,24,'MODEL:CYCLES  /  USER MANUAL');c.drawRightString(561,24,str(doc.page))
 if index<len(pages):c.addOutlineEntry(pages[index]['title'],'page'+str(doc.page),level=0)
 c.restoreState()

def page_number(title):return next(i+2 for i,p in enumerate(pages) if p['title']==title)
def link(title):return f'<link href="#page{page_number(title)}" color="#305c4b">{escape(title)}</link>'
index_items=[('ACID','MACRO, ACID & WAVE'),('Arpeggiator','Notes, scales & page length'),('Attack','Filters & attack'),('Beat repeat','Tracks, mute & repeat'),('CC assignments','CC knobs & MIDI LFOs'),('ChordKeys','Optional controls'),('Control All','Tracks, mute & repeat'),('Delay divisions','Delay, phaser & crusher'),('Diagnostics','Saving, USB & diagnostics'),('Effects routing','Choose & route effects'),('ELDER','ELDER, TINY, Shadow & Feral'),('ESTUS','PUNCH, ESTUS & SY Bits'),('Filters','Filters & attack'),('Global preferences','Global preferences'),('Groove','Groove, Strum & Sidechain'),('Humanize','Generate, Scramble & Humanize'),('LEGACY','Optional controls'),('LFOs, audio','Audio LFOs'),('LFOs, MIDI','CC knobs & MIDI LFOs'),('MACRO / Lo-Fi','MACRO, ACID & WAVE'),('Machines, list','Machine library'),('MIDI input / output','Connect & sequence MIDI'),('Mute and solo','Tracks, mute & repeat'),('Page Len / Warp','Notes, scales & page length'),('POTS','Delay, phaser & crusher'),('PUNCH','PUNCH, ESTUS & SY Bits'),('Resample','Sample Wizard'),('Sample locks','Sample Wizard'),('Saving','Saving, USB & diagnostics'),('Scale Lock','Notes, scales & page length'),('Scramble','Generate, Scramble & Humanize'),('Sequence Genie','Generate, Scramble & Humanize'),('Sidechain','Groove, Strum & Sidechain'),('SPEAK','SPEAK'),('Step Recorder','Notes, scales & page length'),('Strum','Groove, Strum & Sidechain'),('TINY','ELDER, TINY, Shadow & Feral'),('USB audio','Saving, USB & diagnostics'),('Vinyl','Optional controls'),('WAVE','MACRO, ACID & WAVE'),('Word indexes','Word library')]
index_items=[(label,('MACRO' if label.startswith('MACRO') else 'ACID & WAVE') if title=='MACRO, ACID & WAVE' else title) for label,title in index_items]

index_items+= [('Song mode','Build a song'),('Song playback / saving','Play and save a song'),('ACID glide / legato','ACID articulation'),('Direct Pattern Jump','Pattern jumps & trig selection'),('Trig selection','Pattern jumps & trig selection'),('Machinedrum engines','Machinedrum engines')]
index_items.sort(key=lambda x:x[0].lower())

def build_flow():
 flow=[Spacer(1,1),PageBreak()]
 for p in pages:
  flow.extend([para(p['group'],'kicker'),para(escape(p['title']),'h1'),para(p['lead'],'lead')])
  for kind,value in p['blocks']:
   if kind=='p':flow.append(para(value))
   elif kind=='h':flow.append(para(escape(value),'h2'))
   elif kind=='t':flow.extend([table(*value),Spacer(1,8)])
   elif kind=='steps':
    for i,item in enumerate(value,1):flow.append(para(f'<b>{i:02}.</b>  '+item))
   elif kind=='call':
    title,body=value;t=Table([[para('<b>'+escape(title)+'</b><br/>'+body,'call')]],colWidths=[WIDTH]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('LINEBEFORE',(0,0),(0,-1),2,GREEN),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]));flow.extend([Spacer(1,5),t,Spacer(1,10)])
   elif kind=='contents':
    groups=[('Your first session','Start here'),('Global preferences','Settings'),('Tracks, mute & repeat','Performance'),('Notes, scales & page length','Sequencing'),('Generate, Scramble & Humanize','Pattern design'),('Groove, Strum & Sidechain','Rhythm and dynamics'),('Filters & attack','Sound shaping'),('Audio LFOs','Modulation'),('Choose & route effects','Effects'),('Machine library','Machines'),('Sample Wizard','Sampling'),('SPEAK','Voice'),('Connect & sequence MIDI','MIDI'),('Saving, USB & diagnostics','Storage and connections'),('Optional controls','Machine Optional'),('Everyday shortcuts','Reference'),('Word library','SPEAK word list')]
    groups=[(p['title'],p['group']) for p in pages[1:]]
    n=(len(groups)+1)//2;rows=[]
    for i in range(n):
     row=[]
     for j in (i,i+n):
      if j<len(groups):
       t,g=groups[j];row.extend([Paragraph(link(t),styles['cell']),Paragraph(str(page_number(t)),styles['cell'])])
      else:row.extend(['',''])
     rows.append(row)
    t=Table(rows,colWidths=[225,30,225,30]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),('LINEBELOW',(0,0),(-1,-1),.25,LINE)]));flow.extend([t,Spacer(1,6)])
   elif kind=='words':
    rows=[]
    for i in range(32):
     row=[]
     for j in range(4):row.extend([i+32*j,DATA['speak_words'][i+32*j]])
     rows.append(row)
    flow.extend([table(['#','Word']*4,rows,[30,97.5]*4,small=True),Spacer(1,12)])
   elif kind=='index':
    n=(len(index_items)+1)//2;left=index_items[:n];right=index_items[n:];rows=[]
    for i in range(n):
     row=[]
     for items in (left,right):
      if i<len(items):label,title=items[i];row.extend([Paragraph(escape(label),styles['cell']),Paragraph(f'<link href="#page{page_number(title)}">{page_number(title)}</link>',styles['cell'])])
      else:row.extend(['',''])
     rows.append(row)
    t=Table(rows,colWidths=[210,45,210,45]);t.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LINEBELOW',(0,0),(-1,-1),.25,LINE)]));flow.extend([t,Spacer(1,12)])
  flow.append(PageBreak())
 return flow[:-1]

def markdown():
 lines=['# SUPERMODEL','## User manual · Release 2.64','','Model:Cycles · Full / Lite / Machine Optional','']
 for p in pages:
  lines+=['# '+p['title'],'',p['lead'],'']
  for kind,value in p['blocks']:
   if kind in ('p','h'):lines+=[('## ' if kind=='h' else '')+re.sub('<[^>]+>','',value),'']
   elif kind=='steps':lines +=[f'{i}. '+re.sub('<[^>]+>','',v) for i,v in enumerate(value,1)]+['']
   elif kind=='call':lines+=['**'+value[0]+'** — '+re.sub('<[^>]+>','',value[1]),'']
   elif kind=='t':
    head,rows,_=value;lines+=['| '+' | '.join(head)+' |','| '+' | '.join('---' for _ in head)+' |']+['| '+' | '.join(row)+' |' for row in rows]+['']
 return '\n'.join(lines)

if __name__=='__main__':
 doc=SimpleDocTemplate(str(OUT),pagesize=letter,leftMargin=51,rightMargin=51,topMargin=63,bottomMargin=53,title='Supermodel 2.64 — User Manual',author='Supermodel',subject='Current features and controls for Model:Cycles')
 doc.build(build_flow(),onFirstPage=chrome,onLaterPages=chrome)
 r=PdfReader(OUT);expected=len(pages)+1
 print('Pages:',len(r.pages),'expected:',expected)
 for i,p in enumerate(r.pages):print(i+1,' '.join((p.extract_text() or '').split())[:105])
 (W/'Supermodel-2.64-Manual.md').write_text(markdown(),encoding='utf-8',newline='\n')
 (W/'layout.json').write_text(json.dumps(dict(expected_pages=expected,actual_pages=len(r.pages),chapters=[dict(page=i+2,title=p['title']) for i,p in enumerate(pages)]),indent=2)+'\n')
 assert len(r.pages)==expected, 'A chapter overflowed its intended page'
 for ch in [dict(page=i+2,title=p['title']) for i,p in enumerate(pages)]:assert ch['title'] in r.pages[ch['page']-1].extract_text(),ch
 import shutil
 for folder in ('flasher','flasher-optional'):
  shutil.copyfile(OUT,R/'docs'/folder/'user-manual.pdf');shutil.copyfile(W/'Supermodel-2.64-Manual.md',R/'docs'/folder/'user-manual.md')
 print('PDF:',OUT)
