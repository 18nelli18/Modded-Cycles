// Note124 : changer uniquement la boucle de conversion MACRO, taille constante.
window.MCMacroRenderOptimize=(input,b,a,syntakt,stock,saved)=>{
 if(!a.isSelected('macro'))return input;
 const d=window.MCMacroHalfband,hash=x=>b.hex(b.sha256(x));let count=0;
 const result=input.map(t=>{
  if(!t.append?.parts?.some(p=>p.hex?.includes(d.old)))return t;
  const ref=a.REF_MODS[t.id];if(!ref||hash(b.writesBytes(t))!==ref.w||hash(b.buildPayload(t.append,syntakt,stock))!==ref.p)throw Error('MACRO optimization: reference guard');
  const copy=JSON.parse(JSON.stringify(t));
  for(const p of copy.append.parts)if(p.hex){const n=p.hex.split(d.old).length-1;count+=n;p.hex=p.hex.replaceAll(d.old,d.hex);}
  delete copy.append.compressed_hex;delete copy.append.stored;
  if(!saved.has(t.id))saved.set(t.id,{w:ref.w,p:ref.p});
  a.REF_MODS[t.id]={w:ref.w,p:hash(b.buildPayload(copy.append,syntakt,stock))};return copy;
 });
 if(count!==1)throw Error('MACRO optimization: expected exactly one renderer, found '+count);
 return result;
};
