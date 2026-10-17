/* Conversion locale WAV -> IMA ADPCM et remplissage du pool réservé Model909.
 * Algorithme IMA et préparation inspirés de DMDaudio/model909 (MIT).
 * Aucun accès réseau ni stockage des données audio.
 */
(function (root) {
'use strict';
const STEP = [7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,1707,1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,15289,16818,18500,20350,22385,24623,27086,29794,32767];
const INDEX = [-1,-1,-1,-1,2,4,6,8,-1,-1,-1,-1,2,4,6,8];
const NAMES = ['ch','oh','crash','ride'];
function wav(bytes) {
  const v = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const tag = at => String.fromCharCode(...bytes.subarray(at,at+4));
  if (bytes.length < 44 || tag(0)!=='RIFF' || tag(8)!=='WAVE') throw new Error('Choose a RIFF/WAVE audio file.');
  let fmt, data;
  for (let at=12; at+8<=bytes.length;) {
    const n=v.getUint32(at+4,true), start=at+8;
    if (n>bytes.length-start) throw new Error('Incomplete WAV chunk.');
    if (tag(at)==='fmt ') {
      if(n<16) throw new Error('Invalid WAV format.');
      let kind=v.getUint16(start,true);
      if(kind===65534) {
        if(n<40) throw new Error('Invalid extended WAV format.');
        kind=v.getUint16(start+24,true);
      }
      fmt={kind,channels:v.getUint16(start+2,true),rate:v.getUint32(start+4,true),align:v.getUint16(start+12,true),bits:v.getUint16(start+14,true)};
    }
    if(tag(at)==='data' && !data) data={at:start,n};
    at=start+n+(n&1);
  }
  if(!fmt || !data) throw new Error('WAV format or audio data is missing.');
  const {kind,channels,rate,align,bits}=fmt, size=bits/8;
  if(channels<1 || channels>8 || rate<8000 || rate>192000 || align!==size*channels || !((kind===1 && [8,16,24,32].includes(bits)) || (kind===3 && [32,64].includes(bits)))) throw new Error('Use PCM or floating-point WAV, 8–192 kHz, up to eight channels.');
  const count=Math.floor(data.n/align);
  if(!count || count>rate*30) throw new Error('Choose an audio hit shorter than 30 seconds.');
  const out=new Float64Array(count);
  for(let i=0;i<count;i++) {
    let sum=0;
    for(let c=0;c<channels;c++) {
      const at=data.at+i*align+c*size; let x;
      if(kind===3) x=bits===32?v.getFloat32(at,true):v.getFloat64(at,true);
      else if(bits===8) x=(v.getUint8(at)-128)/128;
      else if(bits===16) x=v.getInt16(at,true)/32768;
      else if(bits===24) {let n=v.getUint8(at)|(v.getUint8(at+1)<<8)|(v.getUint8(at+2)<<16); if(n&0x800000)n-=0x1000000; x=n/8388608;}
      else x=v.getInt32(at,true)/2147483648;
      if(!Number.isFinite(x)) throw new Error('WAV contains invalid sample values.');
      sum+=Math.max(-1,Math.min(1,x));
    }
    out[i]=sum/channels;
  }
  return {pcm:out,rate};
}
function resample(input,rate) {
  if(rate===32000) return input;
  const ratio=rate/32000, cutoff=Math.min(1,1/ratio)*0.95, radius=24;
  const out=new Float64Array(Math.max(1,Math.round(input.length/ratio)));
  for(let i=0;i<out.length;i++) {
    const pos=i*ratio, center=Math.floor(pos);let sum=0,weight=0;
    for(let j=center-radius+1;j<=center+radius;j++) {
      if(j<0 || j>=input.length)continue;
      const d=pos-j, z=Math.PI*d*cutoff;
      const w=(Math.abs(z)<1e-12?cutoff:Math.sin(z)/(Math.PI*d))*(0.5+0.5*Math.cos(Math.PI*d/radius));
      sum+=input[j]*w;weight+=w;
    }
    out[i]=weight?sum/weight:0;
  }
  return out;
}
function prepare(input) {
  let peak=0; for(const x of input)peak=Math.max(peak,Math.abs(x));
  if(peak<1e-12)throw new Error('The sample is silent.');
  const pcm=Int16Array.from(input,x=>Math.max(-32768,Math.min(32767,Math.round(x*30000/peak))));
  const tail=30000*Math.pow(10,-66/20);let end=pcm.length,start=0;
  while(end && Math.abs(pcm[end-1])<=tail)end--;
  while(start<end && Math.abs(pcm[start])<=300)start++;
  start=Math.max(0,start-8);
  const out=pcm.slice(start,end), fade=Math.min(out.length,320);
  for(let i=0;i<fade;i++)out[out.length-fade+i]=Math.round(out[out.length-fade+i]*(fade-i)/fade);
  return out;
}
function ima(pcm) {
  let pred=0,index=0;const out=new Uint8Array(Math.ceil(pcm.length/2));
  for(let i=0;i<pcm.length;i++) {
    const step=STEP[index];let d=pcm[i]-pred,code=d<0?8:0,diff=step>>3;d=Math.abs(d);
    if(d>=step){code|=4;d-=step;diff+=step;}
    if(d>=(step>>1)){code|=2;d-=step>>1;diff+=step>>1;}
    if(d>=(step>>2)){code|=1;diff+=step>>2;}
    pred=Math.max(-32768,Math.min(32767,pred+(code&8?-diff:diff)));
    index=Math.max(0,Math.min(88,index+INDEX[code]));
    out[i>>1]|=code<<((i&1)*4);
  }
  return out;
}
function encode(bytes) {
  const audio=wav(bytes),pcm=prepare(resample(audio.pcm,audio.rate));
  return {data:ima(pcm),frames:pcm.length,seconds:pcm.length/32000};
}
function populate(template,samples) {
  const tweak=JSON.parse(JSON.stringify(template)),slot=tweak.sample_slots;
  if(!slot || slot.rate!==32000)throw new Error('Invalid sample template.');
  const pool=new Uint8Array(slot.capacity),table=new Uint8Array(32),v=new DataView(table.buffer);let used=0;
  for(let i=0;i<NAMES.length;i++) {
    const s=samples[NAMES[i]]; if(!s || !s.data || !s.frames)throw new Error('Choose all four samples.');
    used=(used+3)&~3;
    if(s.data.length>pool.length-used)throw new Error('The four samples exceed the reserved sample space. Use shorter hits.');
    pool.set(s.data,used);v.setUint32(i*8,parseInt(slot.pool,16)+used,false);v.setUint32(i*8+4,s.frames,false);used+=s.data.length;
  }
  const hex=b=>Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');
  const poolPart=tweak.append.parts.find(p=>parseInt(p.dest,16)===parseInt(slot.pool,16));
  if(!poolPart || poolPart.hex.length!==pool.length*2)throw new Error('Invalid reserved sample pool.');
  poolPart.hex=hex(pool);
  const address=parseInt(slot.table,16),part=tweak.append.parts.find(p=>p.hex && address>=parseInt(p.dest,16) && address+32<=parseInt(p.dest,16)+p.hex.length/2);
  if(!part)throw new Error('Sample table is outside the firmware template.');
  const off=(address-parseInt(part.dest,16))*2;part.hex=part.hex.slice(0,off)+hex(table)+part.hex.slice(off+64);
  return {tweak,used};
}
root.MC909Samples={wav,resample,prepare,ima,encode,populate};
if(typeof module!=='undefined')module.exports=root.MC909Samples;
})(typeof window!=='undefined'?window:globalThis);
