"""Note 98 : promouvoir les octets du candidat confirme par AveyCole.

python tools/promote_midi_persistence.py [--check]
Le noyau compile reste identique au test 2 ; seuls statut et textes changent.
"""
import argparse,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
EN='Hardware tested by AveyCole. Stop playback, then Save Project and wait for MIDI SAVED. Saved MIDI data loads only when you enter B-side and only while playback is stopped. FUNC + SETTINGS + TRACK opens B-side. Includes notes, retrigger/chance, CC assignments/locks and both MIDI CC LFOs. Install alone or alongside your selected machines; Sample Wizard stays optional. Additional MIDI files are outside Elektron project backups and SysEx exports. Unsaved edits are lost on power-off.'
FR='Teste sur machine par AveyCole. Arretez la lecture, faites Save Project et attendez MIDI SAVED. Les donnees MIDI sauvegardees se chargent uniquement en entrant cote B et uniquement lorsque la lecture est arretee. FUNC + SETTINGS + TRACK ouvre B. Notes, retrigger/chance, assignations/locks CC et deux LFO CC MIDI inclus. Seule ou avec les machines choisies ; Sample Wizard facultatif. Fichiers MIDI hors backups projet et exports SysEx Elektron. Editions non sauvegardees perdues a extinction.'
def outputs():
    src=ROOT/'docs/flasher-midi-save-current-test'
    yield 'midi-persistence-data.js',(src/'midi-persistence-data.js').read_text(encoding='utf-8')
    s=(src/'midi-persistence.js').read_text(encoding='utf-8')
    s=s.replace("f.status='experimental';delete f.hardwareTestedByOwner;","f.status='tested';f.hardwareTestedByOwner=true;")
    start=s.index(' a.registerFeatureTexts(');end=s.index(' const cache=',start)
    import json
    texts={'en':{'label':'MIDI OUT Bank','short':'Hardware tested MIDI saving. Enter B-side with playback stopped to load saved MIDI.','desc':EN},'fr':{'label':'Banque MIDI OUT','short':'Sauvegarde MIDI testee. Entrez cote B, lecture arretee, pour charger le MIDI.','desc':FR}}
    s=s[:start]+" a.registerFeatureTexts('midi-out-bank',"+json.dumps(texts,ensure_ascii=False)+');\n'+s[end:]
    s=s.replace("bank.status='experimental';delete bank.hardwareTestedByOwner;delete bank.ram_only_rollback;bank.pending=['hardware_persistence_verification'];","bank.status='tested';bank.hardwareTestedByOwner=true;delete bank.ram_only_rollback;bank.pending=[];")
    yield 'midi-persistence.js',s
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    for name,text in outputs():
        dest=ROOT/'docs/flasher'/name
        if a.check:assert dest.read_text(encoding='utf-8')==text,name
        else:dest.write_text(text,encoding='utf-8')
    print('ok promotion MIDI : octets test 2 identiques, statut confirme par AveyCole')
if __name__=='__main__':main()
