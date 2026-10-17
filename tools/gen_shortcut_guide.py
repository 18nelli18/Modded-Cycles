"""Guide des nouveaux gestes, EN/FR, HTML imprimable et telechargements Markdown."""
import argparse,html,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
EN="""# New feature shortcut guide

A.V.’s Supermodel Edition · 16 October 2026

Added gestures only; stock-style transport, copy, clear and paste actions are omitted.

Install the relevant feature first. Hold the first button while pressing or turning the next control. TRIG means a step key; pad means a track pad; DATA means LEVEL/DATA. MACHINES is the physical button sometimes called PRESET in sampler instructions.

## Performance and sound

| Feature | Gesture | Result |
|---|---|---|
| Control All Config | TRACK + TRIG 1–6 | Include or exclude tracks from Control All. The active track follows the native active-track exception. Choices reset on power-off. |
| Control All Beat Repeat | Hold TRACK + RETRIG, then hold TRIG 1–16 | Repeat the included audio tracks. The newest held TRIG chooses the division and shows a brief popup. Release the division pad or either modifier to stop. Both modifiers must stay held. |
| Latching mute | Hold TRACK, tap FUNC | Keep mute mode open. Tap FUNC to leave. |
| Trig preview | While stopped or paused, hold TRIG + PAGE | Audition that step with its note and locks. |
| Audio slide trigs | SETTINGS + TRIG | Toggle a parameter slide on the step. |
| Synth Attack | MACHINES + DECAY | Set the added attack control on supported synth/drum tracks. |
| Per-track filter | MACHINES + SWEEP / CONTOUR | Cutoff / resonance. Hold TRACK as well for Control All over included audio tracks. Neutral is maximum cutoff and zero resonance. |
| MACRO lo-fi | FUNC + PITCH on a MACRO track | Left reduces sample rate; right reduces bit depth. |

### Beat repeat divisions

| TRIG | Division | TRIG | Division |
|---|---|---|---|
| 1 | 1/64 | 9 | 3/16 |
| 2 | 1/48 | 10 | 1/4 |
| 3 | 1/32 | 11 | 1/3 |
| 4 | 1/24 | 12 | 3/8 |
| 5 | 1/16 | 13 | 1/2 |
| 6 | 1/12 | 14 | 2/3 |
| 7 | 1/8 | 15 | 3/4 |
| 8 | 1/6 | 16 | 1 bar |

Long audio slices halve at slow tempos to fit the history buffer. The released audio repeat does not repeat outgoing MIDI notes; the MIDI test below adds B-note retriggering.

## Sequence Genie, SCRAMBLE and modulation

| Feature | Gesture | Result |
|---|---|---|
| Sequence Genie | SETTINGS + PAGE | Open the generator for the selected audio track or B MIDI lane. DATA selects; click, turn, click to edit. Queue chooses Loop or Page boundaries. |
| A-side SCRAMBLE | SETTINGS + TRACK | Randomize four synthesis controls. Sampler tracks are excluded. |
| A-side step SCRAMBLE | Hold TRIG(s), then SETTINGS + TRACK | Toggle fresh randomized values on those steps each pass, retaining the base sound. |
| B-side SCRAMBLE | SETTINGS + TRACK | Randomize the selected lane’s assigned MIDI CC values. |
| Second LFO | Press LFO twice | Open LFO 2. On its page, LFO SPEED edits LFO 2. |
| LFO 2 quick assignment | On A-side LFO 2, hold LFO and turn a parameter knob | Select that destination; further turning adjusts signed depth. |
| Scale Lock | FUNC + PAGE | Access added scale/key settings with the performance support installed. |
| Arpeggiator / ChordKeys settings | FUNC + RETRIG | Access the added direction/octave or ChordKeys options, according to the installed feature. |
| Arpeggiator performance | Hold RETRIG while holding notes | Play the held notes through the arpeggiator; A.On provides its latch option. |
| ChordKeys | On a CHORD track, play TRIG 1–16 | 1–7: I–VII; 8–14: one octave up; 15–16: I–II two octaves up. |

## Sample Wizard and sample preview

| Feature | Gesture | Result |
|---|---|---|
| Sample lock | Hold a step TRIG + MACHINES | Choose a sample lock for that step on a Wizard track. |
| Playback modes | SETTINGS + MACHINES | Open the sampler’s playback-mode controls. |
| Mode options | SETTINGS + PUNCH | Open the selected sampler mode’s options. |
| Resampling | SETTINGS + REC | Open resampling controls. |
| Sample Preview — hardware tested | FUNC + MACHINES; highlight a sample, then play its track pad or keyboard TRIG | Audition the highlighted sample in the Wizard browser. Scrolling alone is silent. Compatible with ChordKeys and WAVE. |
| Slice editor: upper slices | Hold FUNC + TRIG 1–16 | Play slices 17–32 while the slice editor is open. |
| Slice editor: zero crossing | FUNC + marker knobs 1 / 2 | Snap the respective slice marker to a zero crossing. |
| Slice editor: remove marker | FUNC + click DATA | Remove a slice marker. DATA alone splits; PUNCH controls tap slicing. |

## MIDI B-side and routing

| Feature | Gesture | Result |
|---|---|---|
| Enter / leave MIDI B-side | FUNC + SETTINGS + TRACK | Open or close the six parallel MIDI tracks. Use the combo from B home to exit; BACK there also exits. |
| MIDI CC assignment | SETTINGS + a gray knob | Assign that knob to a MIDI CC on the selected B lane. |
| MIDI CC lock | Hold TRIG + an assigned knob | Add a CC parameter lock to that MIDI step. |
| MIDI note / CC slide | SETTINGS + TRIG | Enable or disable a slide. Notes overlap for legato; CCs glide toward the marked step’s values. |
| MIDI keyboard setup | FUNC + TRACK | Set keyboard transpose and Pad Note. |
| MIDI CC LFO 2 | Press LFO twice on B-side | Open the second MIDI CC LFO. In Dst, click DATA, choose OFF or CC0–127, then click DATA to confirm; BACK cancels. |
| Combined MIDI OUT + THRU | Set CONFIG → MIDI → PORTS → OUT/THRU to THR, then FUNC + click DATA | Toggle the Cycles’ own outgoing MIDI while retaining incoming MIDI Thru. |

Saved MIDI loads only when entering B-side while playback is stopped. Stop before Save Project and wait for MIDI SAVED. Sidecar MIDI files are outside Elektron SysEx backups.

## Separate MIDI performance test

These two additions are experimental and available only on the [MIDI performance test page](../flasher-midi-performance-test/?v=2026-10-16-midi-performance-test-1), currently using the fixed six-voice 909 profile and four local WAVs.

| Feature | Gesture | Result |
|---|---|---|
| MIDI beat repeat | Hold TRACK + RETRIG, then hold a division TRIG | Retrigger each included B lane’s latest sequenced note, using its current MIDI channel and port. Release stops the repeated notes. This repeats notes rather than capturing a MIDI phrase; native A-side MIDI output is outside this test. |
| B-side Control All filter: audio + MIDI | In B-side, hold TRACK + MACHINES and turn SWEEP / CONTOUR | Update included internal audio filters and send CC74 / CC71 to the configured B instruments. MIDI-muted lanes receive no CC; their internal audio filters still change. |
"""
FR="""# Guide des raccourcis des nouvelles fonctions

A.V.’s Supermodel Edition · 16 octobre 2026

Gestes ajoutes uniquement ; transports, copies, effacements et collages calques sur le stock omis.

Installez la fonction correspondante. Maintenez le premier bouton pendant le second geste. TRIG : touche de pas ; pad : touche de piste ; DATA : LEVEL/DATA. MACHINES est le bouton parfois nomme PRESET dans les instructions du sampler.

## Performance et son

| Fonction | Geste | Resultat |
|---|---|---|
| Control All Config | TRACK + TRIG 1–6 | Inclure ou exclure les pistes de Control All. L exception native de la piste active reste applicable. Choix remis a zero a extinction. |
| Control All Beat Repeat | Tenir TRACK + RETRIG, puis un TRIG 1–16 | Repeter les pistes audio incluses. Dernier TRIG tenu prioritaire, division en popup bref. Relacher le TRIG ou un modificateur arrete. Garder les deux modificateurs tenus. |
| Mute verrouille | Tenir TRACK, taper FUNC | Garder le mode mute ouvert. Taper FUNC pour sortir. |
| Preecoute d un pas | A l arret ou en pause, tenir TRIG + PAGE | Ecouter le pas et ses locks. |
| Slides audio | SETTINGS + TRIG | Activer/desactiver le slide de parametres du pas. |
| Attack synth | MACHINES + DECAY | Regler l attaque ajoutee sur les pistes synth/drum compatibles. |
| Filtre par piste | MACHINES + SWEEP / CONTOUR | Coupure / resonance. Ajouter TRACK pour Control All des pistes audio incluses. Neutre : coupure maximale et resonance nulle. |
| Lo-fi MACRO | FUNC + PITCH sur MACRO | A gauche : frequence d echantillonnage ; a droite : profondeur en bits. |

### Divisions du beat repeat

| TRIG | Division | TRIG | Division |
|---|---|---|---|
| 1 | 1/64 | 9 | 3/16 |
| 2 | 1/48 | 10 | 1/4 |
| 3 | 1/32 | 11 | 1/3 |
| 4 | 1/24 | 12 | 3/8 |
| 5 | 1/16 | 13 | 1/2 |
| 6 | 1/12 | 14 | 2/3 |
| 7 | 1/8 | 15 | 3/4 |
| 8 | 1/6 | 16 | 1 mesure |

Les longues boucles audio sont divisees par deux aux tempos lents selon la capacite du buffer. Le repeat audio publie ne repete pas les notes MIDI ; le test ci-dessous ajoute les notes B.

## Sequence Genie, SCRAMBLE et modulation

| Fonction | Geste | Resultat |
|---|---|---|
| Sequence Genie | SETTINGS + PAGE | Generateur de la piste audio ou voie B selectionnee. DATA choisit ; clic, tourner, clic pour editer. Queue choisit les frontieres Loop/Page. |
| SCRAMBLE A | SETTINGS + TRACK | Randomiser quatre parametres de synthese. Sampler exclu. |
| SCRAMBLE de pas A | Tenir des TRIG, puis SETTINGS + TRACK | Basculer des valeurs aleatoires fraiches a chaque passage, son de base conserve. |
| SCRAMBLE B | SETTINGS + TRACK | Randomiser les valeurs CC assignees de la voie MIDI selectionnee. |
| Second LFO | Appuyer deux fois sur LFO | Ouvrir LFO 2. Dans cette page, LFO SPEED regle LFO 2. |
| Assignation rapide LFO 2 | Sur LFO 2 cote A, tenir LFO et tourner un parametre | Choisir la destination, puis regler sa profondeur signee. |
| Scale Lock | FUNC + PAGE | Acceder aux reglages ajoutes de gamme/tonalite avec le support performance installe. |
| Arpege / reglages ChordKeys | FUNC + RETRIG | Options ajoutees direction/octaves ou ChordKeys selon la fonction installee. |
| Jeu de l arpege | Tenir RETRIG avec des notes tenues | Arpeger les notes ; option A.On pour le verrouillage. |
| ChordKeys | Sur CHORD, jouer TRIG 1–16 | 1–7 : I–VII ; 8–14 : octave superieure ; 15–16 : I–II deux octaves plus haut. |

## Sample Wizard et preecoute

| Fonction | Geste | Resultat |
|---|---|---|
| Sample lock | Tenir TRIG + MACHINES | Choisir un sample lock de ce pas sur une piste Wizard. |
| Modes de lecture | SETTINGS + MACHINES | Ouvrir les modes du sampler. |
| Options du mode | SETTINGS + PUNCH | Ouvrir les options du mode sampler choisi. |
| Reechantillonnage | SETTINGS + REC | Ouvrir le resampling. |
| Sample Preview — teste sur machine | FUNC + MACHINES ; choisir un sample puis jouer pad ou TRIG clavier | Preecoute du sample dans le navigateur Wizard. Defilement seul silencieux. Compatible ChordKeys/WAVE. |
| Editeur slices : slices hautes | FUNC + TRIG 1–16 | Jouer les slices 17–32 dans l editeur. |
| Editeur slices : passage zero | FUNC + potards marqueurs 1 / 2 | Caler le marqueur correspondant au passage zero. |
| Editeur slices : retirer marqueur | FUNC + clic DATA | Retirer un marqueur. DATA seul divise ; PUNCH controle le tap slicing. |

## MIDI B et routage

| Fonction | Geste | Resultat |
|---|---|---|
| Entrer / sortir de B | FUNC + SETTINGS + TRACK | Ouvrir/fermer les six pistes MIDI paralleles. Sortie depuis l accueil B ; BACK y sort aussi. |
| Assignation CC MIDI | SETTINGS + potard gris | Assigner un CC au potard sur la voie B choisie. |
| Lock CC MIDI | Tenir TRIG + potard assigne | Ajouter un lock CC sur le pas MIDI. |
| Slides notes / CC | SETTINGS + TRIG | Activer/desactiver le slide : notes chevauchees en legato, CC glisses vers le pas marque. |
| Reglages clavier MIDI | FUNC + TRACK | Transposition clavier et Pad Note. |
| Second LFO CC MIDI | Appuyer deux fois sur LFO cote B | Ouvrir LFO CC 2. Dst : clic DATA, OFF ou CC0–127, clic DATA pour confirmer ; BACK annule. |
| MIDI OUT + THRU combines | CONFIG → MIDI → PORTS → OUT/THRU : THR, puis FUNC + clic DATA | Basculer la sortie MIDI propre du Cycles tout en gardant le Thru entrant. |

Le MIDI sauvegarde charge uniquement en entrant cote B, lecture arretee. Arreter avant Save Project et attendre MIDI SAVED. Les fichiers MIDI annexes ne sont pas inclus dans les backups SysEx Elektron.

## Test MIDI performance separe

Ces deux ajouts experimentaux sont uniquement sur la [page de test MIDI performance](../flasher-midi-performance-test/?v=2026-10-16-midi-performance-test-1), profil fixe six voix 909 et quatre WAV locaux.

| Fonction | Geste | Resultat |
|---|---|---|
| Beat repeat MIDI | Tenir TRACK + RETRIG, puis TRIG division | Repeter la derniere note sequencee des voies B incluses, canal/port actuels. Relacher arrete les notes. Pas de capture de phrase ; sortie MIDI native A hors de ce test. |
| Filtre Control All depuis B : audio + MIDI | Cote B, tenir TRACK + MACHINES et tourner SWEEP / CONTOUR | Filtres audio internes inclus et CC74 / CC71 aux instruments B configures. Voies MIDI muettes sans CC ; filtres audio toujours modifies. |
"""
def inline(s):
 s=html.escape(s);return re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',s)
def render(text):
 out=[];table=False
 for line in text.splitlines():
  if line.startswith('|'):
   cells=[s.strip() for s in line.strip('|').split('|')]
   if all(re.fullmatch(r'[-: ]+',c) for c in cells):continue
   tag='td' if table else 'th'
   if not table:out.append('<div class="table-wrap"><table>');table=True
   out.append('<tr>'+''.join('<'+tag+'>'+inline(c)+'</'+tag+'>' for c in cells)+'</tr>');continue
  if table:out.append('</table></div>');table=False
  if not line:continue
  m=re.match(r'(#{1,3}) (.*)',line)
  if m:out.append('<h'+str(len(m[1]))+'>'+inline(m[2])+'</h'+str(len(m[1]))+'>')
  else:out.append('<p>'+inline(line)+'</p>')
 if table:out.append('</table></div>')
 return '\n'.join(out)
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();dest=ROOT/'docs/flasher'
 css='body{margin:0;background:#f4f2eb;color:#20241f;font:16px/1.6 system-ui,sans-serif}main,nav{max-width:1100px;margin:auto;padding:24px}nav{display:flex;gap:16px;align-items:center}button,a{color:inherit}button{padding:8px 16px;border:1px solid #777;border-radius:5px;background:white;cursor:pointer}h1{font-size:clamp(30px,5vw,52px);line-height:1.1}h2{margin-top:48px;border-bottom:2px solid #39493b;padding-bottom:10px}h3{margin-top:30px}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;border-bottom:1px solid #bbb;padding:12px;vertical-align:top}th{background:#dfe7dc}td:nth-child(2){font-weight:650;min-width:190px}html[lang=en] [data-l=fr],html[lang=fr] [data-l=en]{display:none}@media print{nav{display:none}body{background:white;font-size:10pt}main{padding:0}h2{break-after:avoid;margin-top:20px}tr{break-inside:avoid}table{font-size:9pt}a{color:inherit;text-decoration:none}}'
 page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>New feature shortcuts — Supermodel</title><style>'+css+'</style><nav><a href="./">Flasher</a><button onclick="document.documentElement.lang=\'en\'">English</button><button onclick="document.documentElement.lang=\'fr\'">Francais</button><button onclick="window.print()">Print / Imprimer</button></nav><main><article data-l="en">'+render(EN)+'</article><article data-l="fr">'+render(FR)+'</article></main></html>\n'
 outputs={'shortcut-guide.html':page,'quick-reference.md':EN.rstrip()+'\n','quick-reference-fr.md':FR.rstrip()+'\n'}
 for name,text in outputs.items():
  if a.check:assert (dest/name).read_text(encoding='utf-8')==text,name
  else:(dest/name).write_text(text,encoding='utf-8')
 print('PASS guide raccourcis EN/FR, HTML et Markdown')
if __name__=='__main__':main()
