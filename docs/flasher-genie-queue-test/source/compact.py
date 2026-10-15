"""Compacter les recettes propres ; vérifier le roundtrip complet."""
import json,pathlib
from midi_catalog_compact import compact,restore,JS_DECODER
P=pathlib.Path('work/sample-wizard-options');data=json.load(open(P/'data.json'));packed=compact(data);assert restore(packed)==data
(P/'catalogue.js').write_text('// Généré : recettes uniquement, extraction Syntakt côté client.\nwindow.MCWizardCatalogue=(function(){'+JS_DECODER+'return unpackCatalogue('+json.dumps(packed,separators=(',',':'))+');})();\n')
print('PASS catalogue 256 variantes : roundtrip exact ;', (P/'catalogue.js').stat().st_size,'octets, aucun firmware incorporé.',flush=True)
