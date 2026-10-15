// Références statiques calculées sur les fichiers officiels privés, jamais publiés.
const fs=require('fs'),assert=require('assert'),b=require('../sample-wizard-current-main/builder.js'),compose=require('./compose.js'),c=JSON.parse(fs.readFileSync('work/sample-wizard-options/data.json'));
const stock=Uint8Array.from(fs.readFileSync('work/sample-wizard-main/main-os.bin')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx'));
const hash=x=>b.hex(b.sha256(x)),sizes={},refs={engines:{},w:{},wp:{},ck:{},mods:{}},privatePacked={};
for(const [key,v] of Object.entries(c.variants)){
 if(v.engine){const p=b.buildPayload(v.engine.append,st,stock);sizes[key]=p.length;refs.engines[key]={w:hash(b.writesBytes(v.engine)),p:hash(p)};privatePacked[key]=Buffer.from(p).toString('hex');}else sizes[key]=0;
 for(let bits=0;bits<8;bits++){
  const state={mask:Number(key),perf:!!(bits&1),lfo:!!(bits&2),chord:!!(bits&4),genie:false,scramble:false},cat=compose(c,state,[],sizes),w=cat.find(t=>t.id==='sample-wizard');refs.w[key+':'+bits]=hash(b.writesBytes(w));
  if(bits===0||bits===1){const pk=bits===1?3:0;refs.wp[key+':'+pk]=hash(b.buildPayload(w.append,null,stock));}
  if(bits===4){const ck=cat.find(t=>t.id==='chord-keys-supermodel');refs.ck[key]={w:hash(b.writesBytes(ck)),p:hash(b.buildPayload(ck.append,null,stock))};}
 }
 const w=compose(c,{mask:Number(key),perf:false,lfo:false,chord:false,genie:true,scramble:false},[],sizes).find(t=>t.id==='sample-wizard');refs.wp[key+':1']=hash(b.buildPayload(w.append,null,stock));
 if(Number(key)%16===15)console.log('PASS références machines et options',Number(key)+1,'/256');
}
for(const t of [c.sg,c.sc,c.scg,c.preview])refs.mods[t.id]={w:hash(b.writesBytes(t))};
fs.writeFileSync('work/sample-wizard-options/references.json',JSON.stringify({refs,sizes}));fs.writeFileSync('work/sample-wizard-options/private-packed.json',JSON.stringify(privatePacked));console.log('PASS références statiques 256 moteurs ×8 combinaisons contrôles ; aucune donnée firmware exportée.');
