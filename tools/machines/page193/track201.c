/* Six reglages compacts dans les trous libres de l'en-tete natif.
 * Ne touche ni les signatures/accords CHORD (32..35,40..63), ni les champs stock. */
typedef unsigned int u32;typedef unsigned char u8;
extern u32 pl_length(const u8*),pl_warp(const u8*);
static const u8 slots[6]={29,30,31,36,37,39};
u32 pt_length(const u8*h,u32 t){if(!h)return 16;u32 v=t<6?h[slots[t]]:0;return h[25]==1&&(v&224)==160?(v&15)+1:pl_length(h);}
u32 pt_warp(const u8*h,u32 t){if(!h)return 0;u32 v=t<6?h[slots[t]]:0;return h[25]==1&&(v&224)==160?(v>>4)&1:pl_warp(h);}
void pt_load(u8*d,const u8*s){for(u32 i=0;i<6;i++){u32 v=s?s[slots[i]]:0;d[slots[i]]=(v&224)==160?v:0;}}
void pt_set(u8*h,u32 t,u32 n,u32 warp){
 if(t>=6)return;u32 initial=(pl_length(h)-1)|(pl_warp(h)<<4);
 for(u32 i=0;i<6;i++)if((h[slots[i]]&224)!=160)h[slots[i]]=160|initial;
 h[slots[t]]=160|(n-1)|(warp<<4);
}
u32 pt_next(const u8*p,u32 next,u32 t){u32 n=pt_length(p+30642,t);return (next&15)>=n?(next+15)&~15u:next;}
/* Codecs externes : les trous RAM de header restent disponibles, mais leurs
 * octets SysEx appartiennent au codec FX. Les reglages TRK exportes occupent
 * les cinq bits hauts du Scale de chaque piste ; bit7 Mode signe ce format.
 * Les champs natifs sont toujours normalises avant toute lecture sequenceur. */
extern u32 pt_old_encode(u8*,const u8*,u32),pt_old_decode(u8*,const u8*,u32);
u32 pt_encode(u8*out,const u8*raw,u32 limit){
 u32 ok=pt_old_encode(out,raw,limit);if(!(ok&255)||!out||!raw)return ok;
 const u8*h=raw+30642;u32 valid=0;for(u32 t=0;t<6;t++)valid|=(h[slots[t]]&224)==160;
 if(valid){
  out[0x3990+25]=128|(h[25]&1);
  for(u32 t=0;t<6;t++){u32 v=h[slots[t]],cfg=(v&224)==160?v&31:(pl_length(h)-1)|(pl_warp(h)<<4);u32 at=4+722*t+715;out[at]=(out[at]&7)|(cfg<<3);}
 }
 return ok;
}
u32 pt_decode(u8*raw,const u8*in,u32 id){
 u32 ok=pt_old_decode(raw,in,id);if(!(ok&255)||!raw||!in)return ok;
 u8*h=raw+30642;pt_load(h,0);
 if(in[0x3990+25]&128){
  h[25]=in[0x3990+25]&1;
  if(h[25]){u32 n=(u32)in[0x3990+20]*256+in[0x3990+21];if(n<1||n>1024)n=16;h[20]=n>>8;h[21]=n;}
  for(u32 t=0;t<6;t++){u32 v=in[4+722*t+715],scale=v&7;raw[722*t+715]=scale<=6?scale:2;h[slots[t]]=160|(v>>3);}
 }
 return ok;
}
