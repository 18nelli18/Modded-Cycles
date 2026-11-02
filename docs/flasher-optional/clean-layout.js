/* Segments du chargeur lean : overlays gardes, stockage delta16 sans perte. */
(function(){
'use strict';
const B=typeof module!=='undefined'&&module.exports?require('../flasher/builder.js'):window.MCBuilder;
const BASE=0x40000400,START=0x401aa140-BASE;
const be=(a,p)=>new DataView(a.buffer,a.byteOffset,a.byteLength).getUint32(p,false);
const put=(a,p,n)=>new DataView(a.buffer,a.byteOffset,a.byteLength).setUint32(p,n,false);
const eq=(a,b)=>a.length===b.length&&a.every((v,i)=>v===b[i]);
function isClean(main){return String.fromCharCode(...main.subarray(START,START+8))==='SMCLEAN1'}
function view(main){
 if(!isClean(main))throw Error('Lean firmware layout required');
 const source=be(main,START+28)-BASE,payload=main.subarray(source,source+be(main,START+32)),records=[];
 for(let i=0;i<be(payload,0);i++){
  const p=4+12*i,word=be(payload,p+4),delta=!!(word&0x80000000),length=word&0x7fffffff,offset=be(payload,p+8),size=delta?length/2:length;
  if(offset+size>payload.length)throw Error('Lean segment outside payload');
  records.push({at:be(payload,p),length,delta,data:payload.slice(offset,offset+size)});
 }
 function read(at,n){
  const out=new Uint8Array(n),native=at-BASE;
  if(native>=0&&native<START)out.set(main.subarray(native,Math.min(START,native+n)));
  for(const r of records){const lo=Math.max(at,r.at),hi=Math.min(at+n,r.at+r.length);if(lo>=hi)continue;
   let data=r.data;if(r.delta){if(!r.decoded){r.decoded=new Uint8Array(r.length);let value=0;const dv=new DataView(r.data.buffer,r.data.byteOffset,r.data.byteLength);for(let i=0;i<r.length/4;i++){value=(value+dv.getInt16(i*2,false))>>>0;put(r.decoded,i*4,value)}}data=r.decoded}
   out.set(data.subarray(lo-r.at,hi-r.at),lo-at);
  }return out;
 }
 function write(at,data){const lo=at&~3,hi=(at+data.length+3)&~3,raw=read(lo,hi-lo);raw.set(data,at-lo);records.push({at:lo,length:raw.length,delta:false,data:raw})}
 function delta16(at,data,length){if(at%4||data.length*2!==length||length%4)throw Error('Invalid sine delta segment');records.push({at,length,delta:true,data:data.slice()})}
 function patch(p){const old=B.fromHex(p.old),next=B.fromHex(p.new);if(!eq(read(p.at,old.length),old))throw Error('Lean patch guard mismatch: '+p.at.toString(16));write(p.at,next)}
 function serialize(){
  let size=4+records.length*12;for(const r of records)size+=r.data.length;
  if(size>0x400000)throw Error('Lean payload exceeds staging memory');
  const body=new Uint8Array(size);put(body,0,records.length);let offset=4+records.length*12;
  records.forEach((r,i)=>{put(body,4+12*i,r.at);put(body,8+12*i,(r.length|(r.delta?0x80000000:0))>>>0);put(body,12+12*i,offset);r.fileOffset=source+offset;body.set(r.data,offset);offset+=r.data.length});
  const result=new Uint8Array(source+size);result.set(main.subarray(0,source));result.set(body,source);put(result,START+32,size);put(result,START+36,size);put(result,START+40,records.length);return result;
 }
 return {read,write,patch,delta16,serialize,records};
}
function encode(full,stock,state,safePack){
 const main=state.serialize(),stockSection=stock.container.sections.find(s=>s.id===3),ops=B.aplibDepack(stock.container.blob.subarray(stockSection.off,stockSection.off+stockSection.size)).ops;
 const dirty=Uint8Array.from(main,(v,i)=>i>=START?1:+(v!==stock.main[i])),packed=safePack(B.aplibRepack(main,ops,dirty,START)).packed;
 if(!eq(B.aplibDepack(packed,{bootLayout:true}).data,main))throw Error('Lean MAIN packing mismatch');
 const c=full.container,plains=c.sections.map(s=>{try{return B.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data}catch{return new Uint8Array()}}),key=B.findKey(plains,c.blob.subarray(0,c.blob.length-32),c.blob.subarray(c.blob.length-32));if(!key)throw Error('Firmware signature key not found');
 const blob=B.rebuildContainer(c,{3:packed},key);if(blob.length>0x1c0000)throw Error('Optional selection exceeds flash capacity');
 const raw=B.wrap(B.buildStream(blob,101),full.transport.product,full.transport.start_seq);
 return {raw,main,packed,mainOsSha:B.hex(B.sha256(main)),syxSha256:B.hex(B.sha256(raw)),flashBytes:blob.length};
}
const API={isClean,view,encode};if(typeof module!=='undefined'&&module.exports)module.exports=API;else window.MCCleanLayout=API;
})();
