// Note121 : chaque recette compacte conserve les sites UI et descripteurs utilises par le helper.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto');
const{open}=require('./test_retrosyn_flasher');
(async()=>{const{w,errors}=open();try{
 await w.MCLfoDestinationsReady;const b=w.MCBuilder,base=0x40000400,os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),c=b.parseContainer(b.unwrap(os).stream),s=c.sections.find(s=>s.id===3),stock=b.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data;
 let total=0;
 for(const[mode,entries]of Object.entries(w.MCMachineCombinationData)){
  assert.equal(Object.keys(entries).length,768);
  for(let mask=256;mask<1024;mask++){
   const e=entries[mask];assert.equal(crypto.createHash('sha256').update(JSON.stringify(e.engine)).digest('hex'),e.engine_sha256);
   const tweaks=mode==='wizard'?[e.wizard,e.engine]:[e.engine],p=b.applyWrites(stock,tweaks).data;
   for(const at of [0x4005a4e8,0x4000b208,0x4000b22a]){const hex=b.hex(p.subarray(at-base,at-base+6));assert(new RegExp('^72[0-7][0-9a-f]202f000'+(at===0x4005a4e8?'4':'8')+'$').test(hex),mode+' '+mask+' '+at.toString(16));}
   assert.equal(b.hex(p.subarray(0x4001eaa2-base,0x4001eaa8-base)),'4fefffc4700b');assert.equal(b.hex(p.subarray(0x4002650e-base,0x40026514-base)),'4eb94000b208');
   assert.equal(p[118644],0x67,mode+' '+mask+' invert-track guard');
   const count=p[0x4005a4e9-base];assert(count<=127);assert.equal(e.engine.machine_selection,mask);assert(e.engine.machine_names.length<=17);
   if(mask&512){const v=new DataView(p.buffer,p.byteOffset,p.byteLength),table=v.getUint32(0x4005a4f4-base,false),start=table+56*(count-5);for(let i=0;i<4;i++){const at=start+56*i,part=e.engine.append.parts.find(p=>p.hex&&parseInt(p.dest,16)<=at&&at+56<=parseInt(p.dest,16)+p.hex.length/2);assert(part,mode+' '+mask+' Retrosyn descriptors');const buf=Buffer.from(part.hex,'hex'),off=at-parseInt(part.dest,16);assert.equal(buf.readUInt32BE(off),6);assert.equal(buf.readUInt32BE(off+4),11+i);}}
   total++;
  }
  console.log('PASS all 768',mode,'catalogue recipes: integrity, guarded writes, LFO hooks, bounds and Retrosyn descriptors');
 }
 w.document.getElementById('super-clear').click();const empty=w.MCMidiBankCompose([],os,null);assert.equal(empty.tweaks.length,0);console.log('PASS empty selection keeps the official build free of added payloads');
 assert.equal(total,1536);assert.equal(errors.length,0);console.log('PASS exhaustive compact machine catalogue',total);
}finally{w.close()}})().catch(e=>{console.error(e.stack);process.exitCode=1});
