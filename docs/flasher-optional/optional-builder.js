/* Construction privee : runtime stable, portes et masque de selection.
 * Les quatre octets du masque restent des litteraux dans un layout constant.
 * Aucun fichier de l'editeur principal n'est modifie. */
(function(){
'use strict';
const B=typeof module!=='undefined'&&module.exports?require('../flasher/builder.js'):window.MCBuilder;
const BASE=0x40000400,START=0x401aa140-BASE,RUNTIME=0x46700000,TAIL=0x467ab360,ALL=0x7ffff;
const hash=x=>B.hex(B.sha256(x)),eq=(a,b)=>a.length===b.length&&a.every((x,i)=>x===b[i]);
const be=(a,p)=>new DataView(a.buffer,a.byteOffset,a.byteLength).getUint32(p,false);
const put=(a,p,v)=>new DataView(a.buffer,a.byteOffset,a.byteLength).setUint32(p,v,false);
function join(...a){const out=new Uint8Array(a.reduce((n,x)=>n+x.length,0));let pos=0;for(const x of a){out.set(x,pos);pos+=x.length}return out}
function section(c,id){const s=c.sections.find(x=>x.id===id);if(!s)throw Error('Missing firmware section');return c.blob.subarray(s.off,s.off+s.size)}
function stored(raw){const out=new Uint8Array(raw.length+8);put(out,0,raw.length);put(out,4,raw.reduce((a,b)=>(a+b)>>>0,0));out.set(raw,8);return out}
class Writer{
 constructor(){this.o=[0,0,0,0,0,0,0,0];this.tagpos=-1;this.bits=0;this.pos=0;this.locations=[]}
 bit(v){if(!this.bits){this.tagpos=this.o.length;this.o.push(0);this.bits=8}if(v)this.o[this.tagpos]|=1<<(this.bits-1);this.bits--}
 gamma(v){for(let i=31-Math.clz32(v)-1;i>=0;i--){this.bit((v>>>i)&1);this.bit(i===0?1:0)}}
 literal(v,maskPos){this.bit(1);if(this.pos>=maskPos&&this.pos<maskPos+4)this.locations.push(this.o.length);this.o.push(v);this.pos++}
 match(off,n,last){this.bit(0);if(off===last)this.gamma(2);else{const raw=off+767;this.gamma(raw>>>8);this.o.push(raw&255)}const base=n-1-(off>3328?1:0);if(base<=3){this.bit(base>>1);this.bit(base&1)}else{this.bit(0);this.bit(0);this.gamma(base-2)}this.pos+=n}
 end(){this.bit(0);this.gamma(0x1000002);this.o.push(255);const out=Uint8Array.from(this.o);put(out,0,out.length-8);put(out,4,out.subarray(8).reduce((a,b)=>(a+b)>>>0,0));return out}
}
function safePack(packed,maskPos=-100){
 const {data,ops}=B.aplibDepack(packed),w=new Writer();let last=1;
 for(const [kind,start,off,n] of ops){let pos=start;if(kind===1){w.literal(data[pos],maskPos);continue}let left=n;
  while(left){const count=Math.min(left,0x1ffc00+w.o.length-pos-64);if(count>=4){w.match(off,count,last);last=off;pos+=count;left-=count}else{const take=Math.min(left,512);for(let i=0;i<take;i++)w.literal(data[pos+i],maskPos);pos+=take;left-=take}}
 }
 const out=w.end();if(!eq(B.aplibDepack(out,{bootLayout:true}).data,data))throw Error('Bootstrap packing changed MAIN');return {packed:out,locations:w.locations};
}
function unpack(raw){const transport=B.unwrap(raw),container=B.parseContainer(transport.stream);return {transport,container,main:B.aplibDepack(section(container,3),{bootLayout:true}).data}}
function validateMask(mask){if(!Number.isInteger(mask)||mask<0||mask>ALL)throw Error('Invalid machine selection')}
function prepare(fullRaw,liteRaw,cyclesRaw,recipe){
 if(hash(fullRaw)!==recipe.source_sha256)throw Error('Full v215 checksum mismatch');
 if(hash(liteRaw)!=='0a6e67c552c3a799cb4090357ebe8018503efdebaae9ad3aaa3e68b5f3bd4e0e')throw Error('Lite v216 checksum mismatch');
 if(hash(cyclesRaw)!=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c')throw Error('Official Cycles OS 1.13 required');
 const full=unpack(fullRaw),lite=unpack(liteRaw),stock=unpack(cyclesRaw),end=be(full.main,0x40195ad0-BASE)-BASE;
 const prefix=full.main.slice(0,START),rtDecoded=B.aplibDepack(stored(full.main.subarray(START,end))),rt=rtDecoded.data.slice(),tail=full.main.slice(end);
 for(const patch of recipe.patches){const at=patch.at,a=at<RUNTIME?prefix:at<TAIL?rt:tail,base=at<RUNTIME?BASE:at<TAIL?RUNTIME:TAIL,p=at-base,old=B.fromHex(patch.old),next=B.fromHex(patch.new);if(!eq(a.subarray(p,p+old.length),old))throw Error('Optional patch guard mismatch: '+at.toString(16));a.set(next,p)}
 const dirtyRt=Uint8Array.from(rt,(x,i)=>+(x!==rtDecoded.data[i])),packedRt=B.aplibRepack(rt,rtDecoded.ops,dirtyRt);
 put(prefix,0x40195ad0-BASE,BASE+START+packedRt.length-8);
 const main=join(prefix,packedRt.subarray(8),tail),dirty=Uint8Array.from(main,(x,i)=>i>=START?1:+(x!==stock.main[i]));
 const stockOps=B.aplibDepack(section(stock.container,3)).ops;
 const packed=safePack(B.aplibRepack(main,stockOps,dirty,START)).packed;
 const plains=full.container.sections.map(s=>{try{return B.aplibDepack(section(full.container,s.id)).data}catch{return new Uint8Array()}});
 const c=full.container,key=B.findKey(plains,c.blob.subarray(0,c.blob.length-32),c.blob.subarray(c.blob.length-32));if(!key)throw Error('Firmware signature key not found');
 function encode(s){const blob=B.rebuildContainer(c,{3:s},key);if(blob.length>0x1c0000)throw Error('Firmware exceeds flash capacity');return {raw:B.wrap(B.buildStream(blob,101),full.transport.product,full.transport.start_seq),flashBytes:blob.length}}
 const universal=encode(packed);if(hash(universal.raw)!==recipe.universal_sha256||hash(main)!==recipe.main_sha256)throw Error('Python/browser optional build mismatch');
 const d=new Uint8Array(main.length);d.fill(1,recipe.mask_main_offset,recipe.mask_main_offset+4);
 const t=safePack(B.aplibRepack(main,B.aplibDepack(packed).ops,d),recipe.mask_main_offset);
 if(t.locations.length!==4)throw Error('Machine mask is not four independent literals');
 const result={recipe,template:t.packed,locations:t.locations,flashBytes:encode(t.packed).flashBytes,
  build(mask){validateMask(mask);if(mask===0)return {raw:liteRaw.slice(),mainOsSha:hash(lite.main),syxSha256:hash(liteRaw),flashBytes:lite.container.blob.length,mask,edition:'lite'};
   if(mask===ALL)return {raw:fullRaw.slice(),mainOsSha:hash(full.main),syxSha256:hash(fullRaw),flashBytes:full.container.blob.length,mask,edition:'full'};
   const rawMain=main.slice(),s=t.packed.slice();put(rawMain,recipe.mask_main_offset,mask);for(let i=0;i<4;i++)s[t.locations[i]]=(mask>>>(24-8*i))&255;
   put(s,4,s.subarray(8).reduce((a,b)=>(a+b)>>>0,0));const decoded=B.aplibDepack(s,{bootLayout:true}).data;if(!eq(decoded,rawMain))throw Error('Selection changed unrelated MAIN bytes');
   const out=encode(s);return {...out,mainOsSha:hash(rawMain),syxSha256:hash(out.raw),mask,edition:'full'};
  }};
 return result;
}
const API={prepare,unpack,safePack,validateMask,ALL};if(typeof module!=='undefined'&&module.exports)module.exports=API;else window.MCOptionalBuilder=API;
})();
