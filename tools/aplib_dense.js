// Même recherche bornée que tools/aplib_dense.py ; aucun changement du décodeur.
function aplibDensePack(data, depth=32) {
  const w=new _Writer(), chains=new Map(), n=data.length;
  const key=i=>(data[i]<<16)|(data[i+1]<<8)|data[i+2];
  let i=0,last=1;
  while(i<n){
    let best=0,offset=0;
    if(i+3<=n){
      const k=key(i), candidates=(chains.get(k)||[]).slice().reverse(), reuse=i-last;
      if(reuse>=0 && key(reuse)===k && !candidates.includes(reuse)) candidates.unshift(reuse);
      for(const pos of candidates){
        const off=i-pos;if(off<1||off>TAIL_WINDOW)continue;
        let length=3,limit=Math.min(n-i,TAIL_MAX);
        while(length<limit&&data[pos+length]===data[i+length])length++;
        if(length>best||(length===best&&off===last)){best=length;offset=off;}
      }
    }
    const count=best>=3?best:1;
    if(best>=3){w.match(offset,best,last);last=offset;}else w.literal(data[i]);
    for(let pos=i;pos<Math.min(i+count,n-2);pos++){
      const k=key(pos),history=chains.get(k)||[];history.push(pos);
      if(history.length>depth)history.shift();chains.set(k,history);
    }
    i+=count;
  }
  w.end();const dense=Uint8Array.from(w.o.slice(SECT_HDR)),baseline=aplibPack(data);
  return dense.length<baseline.length?dense:baseline;
}
