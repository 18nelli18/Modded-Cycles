/* Importateur original DX7 ; fichiers utilisateur uniquement, format Yamaha32voix. */

(function(global){'use strict';

function unpack(p){const v=[];for(let k=0;k<6;k++){const q=p.slice(k*17,k*17+17);v.push(...q.slice(0,11),q[11]&3,(q[11]>>2)&3,q[12]&7,q[13]&3,(q[13]>>2)&7,q[14],q[15]&1,(q[15]>>1)&31,q[16],(q[12]>>3)&15);}v.push(...p.slice(102,110),p[110],p[111]&7,(p[111]>>3)&1,...p.slice(112,116),p[116]&1,(p[116]>>1)&7,(p[116]>>4)&7,p[117],...p.slice(118,128),63);return v;}

function valid(v){const op=[99,99,99,99,99,99,99,99,99,99,99,3,3,7,3,7,99,1,31,99,14],g=[99,99,99,99,99,99,99,99,31,7,1,99,99,99,99,1,5,7,48];for(let k=0;k<6;k++)for(let i=0;i<21;i++)if(v[21*k+i]>op[i])return false;return g.every((x,i)=>v[126+i]<=x);}

/* Certaines cartouches contiennent des valeurs hors plage (ROM3A : niveau

 * EG127 dans TIMPANI). Borner une copie avant envoi au validateur strict

 * du firmware ; conserver tous les champs valides et le fichier original. */

function normalize(p,slot,adjustments){

 function limit(at,max,field){if(p[at]>max){adjustments.push({slot,field,from:p[at],to:max});p[at]=max;}}

 for(let k=0;k<6;k++){

  const at=17*k;

  for(let i=0;i<11;i++)limit(at+i,99,'operator '+(6-k)+' parameter '+i);

  limit(at+14,99,'operator '+(6-k)+' output');

  limit(at+16,99,'operator '+(6-k)+' fine frequency');

  const detune=(p[at+12]>>3)&15;

  if(detune>14){adjustments.push({slot,field:'operator '+(6-k)+' detune',from:detune,to:14});p[at+12]=(p[at+12]&7)|(14<<3);}

 }

 for(let i=102;i<110;i++)limit(i,99,'pitch envelope '+(i-102));

 limit(110,31,'algorithm');

 for(let i=112;i<116;i++)limit(i,99,'LFO parameter '+(i-112));

 const wave=(p[116]>>1)&7;

 if(wave>5){adjustments.push({slot,field:'LFO waveform',from:wave,to:5});p[116]=(p[116]&~14)|(5<<1);}

 limit(117,48,'transpose');

}

function parse(raw){

 if(!(raw instanceof Uint8Array))raw=new Uint8Array(raw);

 if(raw.length!==4104||raw[0]!==240||raw[1]!==67||raw[2]>15||raw[3]!==9||raw[4]!==32||raw[5]!==0||raw[4103]!==247)throw Error('Choose a Yamaha DX7 32-voice bank (.syx, 4104 bytes).');

 let sum=0;for(let i=6;i<4103;i++){if(raw[i]>127)throw Error('Invalid 7-bit bank data.');sum+=raw[i];}

 if(sum&127)throw Error('DX7 checksum failed.');

 const copy=new Uint8Array(raw),names=[],adjustments=[];

 for(let i=0;i<32;i++){

  const voice=copy.subarray(6+128*i,134+128*i);normalize(voice,i+1,adjustments);

  const v=unpack(voice);if(!valid(v))throw Error('Invalid voice parameters in slot '+(i+1));

  names.push(String.fromCharCode(...v.slice(145,155)).replace(/[^\x20-\x7e]/g,' ').trim());

 }

 if(adjustments.length){sum=0;for(let i=6;i<4102;i++)sum+=copy[i];copy[4102]=(-sum)&127;}

 return {raw:copy,names,adjustments};

}

function packet(bank,slot,name){if(!Number.isInteger(slot)||slot<0||slot>15)throw Error('Choose library slot 1–16.');const parsed=parse(bank),out=new Uint8Array(4121);out.set([240,125,83,77,76,1,slot]);const label=String(name).replace(/[^\x20-\x7e]/g,' ').trim().slice(0,13).padEnd(16,' ');if(!label.trim())throw Error('Give the bank a name.');out.set(Array.from(label,c=>c.charCodeAt(0)),7);out.set(parsed.raw.slice(6,4102),23);let sum=0;for(let i=2;i<4119;i++)sum+=out[i];out[4119]=(-sum)&127;out[4120]=247;return out;}

function chunkPackets(bank,slot,name,transaction=0){

 if(!Number.isInteger(transaction)||transaction<0||transaction>127)throw Error('Invalid transaction.');

 const full=packet(bank,slot,name),payload=full.slice(23,4119);

 const frame=(command,data)=>{const a=[240,125,83,77,76,2,transaction,command,...data];let sum=0;for(let i=2;i<a.length;i++)sum+=a[i];a.push((-sum)&127,247);return new Uint8Array(a);};

 const result=[frame(0,[slot,...full.slice(7,23)])];

 for(let i=0;i<32;i++)result.push(frame(1,[i,...payload.slice(i*128,(i+1)*128)]));

 result.push(frame(2,[(-payload.reduce((a,b)=>a+b,0))&127]));return result;

}

const api={parse,packet,unpack,chunkPackets};if(typeof module!=='undefined')module.exports=api;global.LegacyImport=api;

})(typeof window==='undefined'?globalThis:window);
