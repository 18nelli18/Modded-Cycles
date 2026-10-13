// Même coût en bits et regard d'un octet que tools/aplib_cost.py.
// Le format et le décompresseur restent inchangés.
function aplibCostPack(data,depth=128){
 const w=new _Writer(),chains=new Map(),n=data.length,key=i=>(data[i]<<16)|(data[i+1]<<8)|data[i+2];
 const gamma=v=>2*(31-Math.clz32(v));let i=0,last=1;
 function match(at,last){
  if(at+3>n)return [0,0,0];
  const k=key(at),positions=(chains.get(k)||[]).slice().reverse(),reuse=at-last;
  if(reuse>=0&&key(reuse)===k&&!positions.includes(reuse))positions.unshift(reuse);
  let best=[0,0,0];
  for(const pos of positions){
   const off=at-pos;if(off<1||off>TAIL_WINDOW)continue;
   let length=3,limit=Math.min(n-at,TAIL_MAX);
   while(length<limit&&data[pos+length]===data[at+length])length++;
   const base=length-1-(off>FAR_THRESHOLD?1:0);
   const bits=1+(off===last?gamma(REUSE_GAMMA):gamma((off+OFFSET_BIAS)>>>8)+8)+2+(base>3?gamma(base-2):0),score=9*length-bits;
   if(score>best[0]||(score===best[0]&&off===last))best=[score,off,length];
  }
  return best;
 }
 while(i<n){
  let [score,off,length]=match(i,last);
  if(length&&i+1<n&&match(i+1,last)[0]>score+9)score=0;
  const count=score>0?length:1;
  if(score>0){w.match(off,length,last);last=off;}else w.literal(data[i]);
  for(let pos=i;pos<Math.min(i+count,n-2);pos++){
   const k=key(pos),history=chains.get(k)||[];history.push(pos);if(history.length>depth)history.shift();chains.set(k,history);
  }
  i+=count;
 }
 w.end();return Uint8Array.from(w.o.slice(SECT_HDR));
}
