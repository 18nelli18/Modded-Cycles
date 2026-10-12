// Note 57 : réponses et erreurs du transfert du flasher MIDI expérimental.
const assert=require('assert');
const F=require('../docs/flasher-midi-test/flasher.js');
const raw=new Uint8Array(3*F.OS_BLOCK+37);
function session(reply){let count=0;return {request:async body=>{
 const n=count++;if(n===0)return new Uint8Array(10);
 return reply(n,body);
}};}
function ack(op=0){const r=new Uint8Array(10);r[9]=op;return r;}
(async()=>{
 // Même protocole sur le câble que le cœur principal éprouvé.
 const stock=require('../docs/flasher/flasher.js');
 const frames=async core=>{
  const sent=[];await core.upgradeFast({request:async body=>{sent.push(Buffer.from(body).toString('hex'));return ack();}},raw,{restMs:0});return sent;
 };
 assert.deepStrictEqual(await frames(F),await frames(stock));
 const blocks=[];
 const result=await F.upgradeFast(session(n=>ack(n===4?1:0)),raw,{restMs:0,onBlock:(n,total)=>blocks.push([n,total])});
 assert.strictEqual(result.sent,raw.length);assert.strictEqual(result.blocks,4);
 assert.deepStrictEqual(blocks,[[1,4],[2,4],[3,4],[4,4]]);
 await assert.rejects(F.upgradeFast(session(()=>ack(1)),raw,{restMs:0}),/Premature completion/);
 await assert.rejects(F.upgradeFast(session(()=>new Uint8Array(6)),raw,{restMs:0}),/Short acknowledgement/);
 await assert.rejects(F.upgradeFast(session(n=>{if(n===2)throw new F.XferError('timeout');return ack();}),raw,{restMs:0}),error=>error.code==='timeout'&&error.detail.includes('block 2, 2048/'));
 await assert.rejects(F.upgradeFast(session(()=>ack(2)),raw,{restMs:0}),error=>error.code==='write');
 let requests=0;const cancelled=await F.upgradeFast({request:async()=>{requests++;return ack();}},raw,{restMs:0,isCancelled:()=>true});
 assert(cancelled.cancelled&&cancelled.sent===0&&requests===1);
 // Le chemin classique transmet toujours tous les messages SysEx.
 const syx=Uint8Array.from([0xf0,1,0xf7,0xf0,2,0xf7]);let sent=0;
 const classic=await F.sendSysex({send:()=>sent++},syx,{pace:0});
 assert.strictEqual(sent,2);assert(!classic.cancelled);
 console.log('ok : totalité acquittée, fin prématurée/refus/réponse courte/timeout localisés, annulation et transfert classique');
})().catch(e=>{console.error(e);process.exitCode=1;});
