// Extraire les catalogues de recettes ; aucun firmware n'est lu ou exporte.
const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.resolve(__dirname,'..'),ctx={window:{}};
for(const file of ['catalogue.js','tiny-data.js'])vm.runInNewContext(fs.readFileSync(path.join(root,'docs/flasher',file),'utf8'),ctx);
fs.mkdirSync(path.join(root,'firmware'),{recursive:true});
for(const [file,key] of [['wizard-catalogue.json','MCWizardCatalogue'],['tiny-catalogue.json','MCTinyCatalogue']])fs.writeFileSync(path.join(root,'firmware',file),JSON.stringify(ctx.window[key]));
console.log('ok catalogues de recettes extraits localement');
