/* Convertir le WAV original avec le convertisseur WAVE deja distribue. */
const fs=require('node:fs'),C=require(process.argv[2]);
const input=fs.readFileSync(process.argv[3]);
const samples=C.fromWav(input.buffer.slice(input.byteOffset,input.byteOffset+input.byteLength));
if(samples.length%C.N)throw Error('Incomplete wavetable frames');
const converted=C.bake(samples),raw=Buffer.alloc(converted.length*2);
for(let i=0;i<converted.length;i++)raw.writeInt16BE(converted[i],i*2);
fs.writeFileSync(process.argv[4],raw);
process.stdout.write(JSON.stringify({frames:samples.length/C.N,samples:converted.length,perFrame:C.S_TOTAL,bytes:raw.length}));
