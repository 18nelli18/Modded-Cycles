// Ajouter TINY sans imposer Wizard ; conserver le support UI choisi par les autres options.
function composeTinyNormal(data,mask,out,b,refs){
 const clone=x=>JSON.parse(JSON.stringify(x)),hash=t=>b.hex(b.sha256(b.writesBytes(t))),entry=data.normal[mask];
 if(!entry)throw Error('TINY: missing machine combination '+mask);
 const e=clone(entry.engine),support=out.find(t=>['supermodel-support-independent','supermodel-wave-support'].includes(t.id));
 const oldEngine=out.find(t=>t.append&&t!==support),result=out.filter(t=>t.id!=='tiny'&&t!==oldEngine&&t!==support);
 const er=data.refs.n[mask];if(hash(e)!==er.w)throw Error('TINY: engine reference guard');
 refs[e.id]={w:er.w,p:er.p};
 if(support){
  const ref=refs[support.id];if(hash(support)!==ref.w||b.hex(b.sha256(b.buildPayload(support.append,null,null)))!==ref.p)throw Error('TINY: trusted support reference mismatch');
  const n=clone(support),oldSource=parseInt(n.append.at,16),source=0x401f8f76,mapping=new Map([[oldSource,source]]);
  if(parseInt(e.append.at,16)+er.size>source||parseInt(n.append.dest,16)+n.append.size>source)throw Error('TINY: support source reservation exceeded');
  if(entry.wave&&oldEngine){
   const ns=entry.wave.gsyms;
   for(const [name,value] of Object.entries(oldEngine.symbols||{}))if(ns[name]!==undefined)mapping.set(parseInt(value,16),Number(ns[name]));
  }
  function remap(hex){let s=hex;for(let i=0;i+8<=hex.length;i+=4){const value=mapping.get(parseInt(hex.slice(i,i+8),16));if(value!==undefined)s=s.slice(0,i)+value.toString(16).padStart(8,'0')+s.slice(i+8);}return s;}
  n.writes.forEach(w=>w.new=remap(w.new));
  const tail='4feffff048d700f04ef9400004ba';let oldTail=n.writes.find(w=>w.old===tail);
  if(!oldTail){const root=n.writes.find(w=>w.off===0x130);if(!root?.new.startsWith('4ef9'))throw Error('TINY: support startup guard');n.writes=n.writes.filter(w=>w!==root);oldTail={off:0,old:tail,new:root.new.slice(0,12)+'4e714e714e714e71'};n.writes.push(oldTail);}
  if(oldTail){
   const stub=e.writes.find(w=>w.new.includes(tail));if(!stub)throw Error('TINY: missing native startup tail');
   oldTail.off=stub.off+stub.new.indexOf(tail)/2;
  }
  const led=new Set([0x400ff9b8,0x400ffa78,0x40103070,0x401031b4,0x40107e18]);
  e.writes=e.writes.filter(w=>{
   const overlap=n.writes.find(v=>w.off<v.off+v.new.length/2&&v.off<w.off+w.new.length/2);
   if(!overlap||overlap===oldTail)return true;
   if(w.new===overlap.new&&w.off===overlap.off)return true;
   if(!led.has(w.off+0x40000400)||w.off!==overlap.off)throw Error('TINY: unexpected support overlap '+w.off.toString(16));
   if(w.old!==overlap.old){const old=oldEngine?.writes.find(v=>v.off<=w.off&&w.off+w.old.length/2<=v.off+v.new.length/2);const i=old?(w.off-old.off)*2:0;if(!old||old.new.slice(i,i+w.old.length)!==overlap.old)throw Error('TINY: prior LED guard');overlap.old=w.old;}
   return false;
  });
  n.append.at='0x'+source.toString(16);n.requires=[e.id];
  let changed=false;for(const p of n.append.parts||[]){if(p.hex){const hex=remap(p.hex);if(hex!==p.hex){p.hex=hex;changed=true;}}}
  if(changed)delete n.append.compressed_hex;
  refs[n.id]={w:hash(n),p:b.hex(b.sha256(b.buildPayload(n.append,null,null)))};result.push(n);
  refs[e.id]={...refs[e.id],w:hash(e)};
 }
 return result.concat(e).sort((x,y)=>x.order-y.order);
}
if(typeof module!=='undefined')module.exports=composeTinyNormal;
