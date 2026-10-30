/* Extension Optional MD : donnees utilisateur, IDs25..27 et chargement separe.
 * Aucune table de l'OS Machinedrum n'est distribuee dans la recette. */
(function(){
'use strict';
const B=typeof module!=='undefined'&&module.exports?require('../flasher/builder.js'):window.MCBuilder;
const O=typeof module!=='undefined'&&module.exports?require('./optional-builder.js'):window.MCOptionalBuilder;
const M=typeof module!=='undefined'&&module.exports?require('./machinedrum-reader.js'):window.MDPatch;
const BASE=0x40000400,START=0x401aa140-BASE,RUN=0x46700000,TAIL=0x467ab360,DATA=0x4683c000,DESC=0x4683c800;
const hash=x=>B.hex(B.sha256(x)),be=(a,p)=>new DataView(a.buffer,a.byteOffset,a.byteLength).getUint32(p,false);
const put=(a,p,n)=>new DataView(a.buffer,a.byteOffset,a.byteLength).setUint32(p,n,false);
const join=(...arrays)=>{const a=new Uint8Array(arrays.reduce((n,x)=>n+x.length,0));let p=0;for(const x of arrays){a.set(x,p);p+=x.length}return a};
const eq=(a,b)=>a.length===b.length&&a.every((x,i)=>x===b[i]);
function stored(raw){const a=new Uint8Array(raw.length+8);put(a,0,raw.length);put(a,4,raw.reduce((n,x)=>(n+x)>>>0,0));a.set(raw,8);return a}
function validateMask(mask){if(!Number.isInteger(mask)||mask<0||mask>0x3fffff)throw Error('Invalid machine selection')}
function firmwareParts(raw,recipe){
 const sha=hash(raw);if(![recipe.MD_SYX_sha256,recipe.MD_BIN_sha256].includes(sha))throw Error('Use official Machinedrum UW OS 1.63 (.syx), or the verified 1.63 reference .bin.');
 return M.mdParts(raw,sha);
}
function build(fullRaw,cyclesRaw,mdRaw,mask,recipe,selectionRecipe){
 validateMask(mask);if(!(mask&recipe.md_bits))throw Error('No Machinedrum engine selected');
 if(hash(fullRaw)!==recipe.source_sha256)throw Error('Machinedrum Optional base checksum mismatch');
 if(hash(cyclesRaw)!=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c')throw Error('Official Cycles OS 1.13 required');
 const parts=firmwareParts(mdRaw,recipe),full=O.unpack(fullRaw),stock=O.unpack(cyclesRaw),end=be(full.main,0x40195ad0-BASE)-BASE;
 const prefix=full.main.slice(0,START),decoded=B.aplibDepack(stored(full.main.subarray(START,end))),rt=decoded.data.slice(),tail=full.main.slice(end);
 function area(at){return at<RUN?[prefix,BASE]:at<TAIL?[rt,RUN]:[tail,TAIL]}
 function read(at,n){const [a,b]=area(at),p=at-b;if(p<0||p+n>a.length)throw Error('Machinedrum read outside base');return a.slice(p,p+n)}
 function write(at,raw){const [a,b]=area(at),p=at-b;if(p<0||p+raw.length>a.length)throw Error('Machinedrum patch outside base');a.set(raw,p)}
 function patch(p){const old=B.fromHex(p.old),next=B.fromHex(p.new);if(!eq(read(p.at,old.length),old))throw Error('Machinedrum patch guard mismatch: '+p.at.toString(16));write(p.at,next)}
 for(const p of selectionRecipe.patches)patch(p);
 write(selectionRecipe.mask,new Uint8Array([(mask>>>24)&255,(mask>>>16)&7,(mask>>>8)&255,mask&255]));
 const tables=Array.from({length:4},(_,k)=>Array.from({length:25},(_,i)=>be(read(DATA+100*k+4*i,4),0)));
 const mapping=read(DATA+400,25),descriptors=read(DESC,181*56),template=read(DESC+131*56,280);
 for(const p of recipe.patches)patch(p);
 for(const machine of recipe.machines){
  tables[0].push(machine.name_pointer);tables[1].push(machine.update);tables[2].push(machine.render);tables[3].push(machine.id+1);
  const row=template.slice();machine.descriptor_fields.forEach((fields,k)=>{for(const [off,n] of Object.entries(fields))put(row,k*56+Number(off),n)});descriptors.set(row,(166+5*(machine.id-25))*56);
 }
 put(descriptors,41*56+12,27<<8);write(DESC,descriptors);
 tables.forEach((t,k)=>{const raw=new Uint8Array(112);t.forEach((v,i)=>put(raw,4*i,v));write(DATA+112*k,raw)});write(DATA+448,join(mapping,new Uint8Array([25,26,27])));
 for(const p of recipe.title_edits)patch(p);
 const body=B.fromHex(recipe.module_body),suffix=B.fromHex(recipe.module_suffix),sine=parts.sine;
 for(const p of recipe.parts){
  if(p.name==='sine')continue;const raw=parts[p.name];if(!raw||raw.length!==p.size)throw Error('Machinedrum table size mismatch: '+p.name);
  if(p.offset<recipe.sine_offset)body.set(raw,p.offset);else suffix.set(raw,p.offset-recipe.sine_offset-131072);
 }
 if(hash(join(body,sine,suffix))!==recipe.filled_module_sha256)throw Error('Machinedrum extracted tables differ from the verified module');
 put(body,recipe.symbols.md_mask-recipe.code,mask);
 const deltas=new Uint8Array(65536),sv=new DataView(sine.buffer,sine.byteOffset,sine.byteLength),dv=new DataView(deltas.buffer);let prior=0;
 for(let i=0;i<32768;i++){const value=sv.getInt32(i*4,false),delta=value-prior;if(delta<-32768||delta>32767)throw Error('Machinedrum sine delta overflow');dv.setInt16(2*i,delta,false);prior=value}
 const dirtyRt=Uint8Array.from(rt,(x,i)=>+(x!==decoded.data[i])),packedRt=B.aplibRepack(rt,decoded.ops,dirtyRt);put(prefix,0x40195ad0-BASE,BASE+START+packedRt.length-8);
 const mainBase=join(prefix,packedRt.subarray(8),tail),alignment=new Uint8Array((-mainBase.length)&3),loaderAddress=BASE+mainBase.length+alignment.length,source=loaderAddress+recipe.loader_reserve;
 const loader=B.fromHex(recipe.loader);put(loader,recipe.loader_fixups.source,source);put(loader,recipe.loader_fixups.deltas,source+body.length+suffix.length);
 put(mainBase,0x40195adc-BASE,loaderAddress);const reserve=new Uint8Array(recipe.loader_reserve);reserve.set(loader);
 const main=join(mainBase,alignment,reserve,body,suffix,deltas),stockSection=stock.container.sections.find(s=>s.id===3),stockOps=B.aplibDepack(stock.container.blob.subarray(stockSection.off,stockSection.off+stockSection.size)).ops;
 const dirty=Uint8Array.from(main,(x,i)=>i>=START?1:+(x!==stock.main[i])),packed=O.safePack(B.aplibRepack(main,stockOps,dirty,START)).packed;
 if(!eq(B.aplibDepack(packed,{bootLayout:true}).data,main))throw Error('Machinedrum bootstrap packing mismatch');
 const c=full.container,plains=c.sections.map(s=>{try{return B.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data}catch{return new Uint8Array()}}),key=B.findKey(plains,c.blob.subarray(0,c.blob.length-32),c.blob.subarray(c.blob.length-32));if(!key)throw Error('Firmware signature key not found');
 const blob=B.rebuildContainer(c,{3:packed},key);if(blob.length>0x1c0000)throw Error('Machinedrum selection exceeds flash capacity');
 const raw=B.wrap(B.buildStream(blob,101),full.transport.product,full.transport.start_seq);
 return {raw,mask,edition:'full',release:recipe.release,mainOsSha:hash(main),syxSha256:hash(raw),flashBytes:blob.length,startup_title:recipe.title,machinedrum:true};
}
const API={build,firmwareParts,validateMask,ALL:0x3fffff,MD_BITS:0x380000};if(typeof module!=='undefined'&&module.exports)module.exports=API;else window.MCOptionalMachinedrum=API;
})();
