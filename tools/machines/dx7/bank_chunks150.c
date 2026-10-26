/* SML2 : banques LEGACY en petits messages checksummes, traitement UI seul.
 * Conserve SML1 et sa validation/ecriture finale ; aucun disque dans le RX. */
typedef struct {u8 data[4121];u32 active,transaction,next,sum;} ChunkBank;
static ChunkBank chunk_bank[2] __attribute__((section(".bankchunks")));
#ifdef DX7_BANK_QUEUE
void dx7_chunk_reset(u32 port){if(port<2)chunk_bank[port].active=0;}
#endif
u32 dx7_chunk_packet(u32 port,const u8*p,u32 n,u8*bank){
 if(port>=2)return 0;ChunkBank*c=&chunk_bank[port];
 if(n<10||p[0]!=240||p[1]!=125||p[2]!=83||p[3]!=77||p[4]!=76||p[5]!=2||p[n-1]!=247)goto bad;
 u32 sum=0;for(u32 i=2;i<n-1;i++){if(p[i]>127)goto bad;sum+=p[i];}if(sum&127)goto bad;
 if(p[7]==0){
  if(n!=27||p[8]>=16)goto bad;for(u32 i=9;i<25;i++)if(p[i]<32||p[i]>126)goto bad;
  c->active=1;c->transaction=p[6];c->next=c->sum=0;
  const u8 head[6]={240,125,83,77,76,1};for(u32 i=0;i<6;i++)c->data[i]=head[i];c->data[6]=p[8];for(u32 i=0;i<16;i++)c->data[7+i]=p[9+i];
  REPORT("BANK RECEIVING");return 1;
 }
 if(!c->active||c->transaction!=p[6])goto bad;
 if(p[7]==1){
  if(n!=139||p[8]>=32)goto bad;u32 index=p[8];
  if(index<c->next){for(u32 i=0;i<128;i++)if(c->data[23+index*128+i]!=p[9+i])goto bad;return 1;}
  if(index!=c->next)goto incomplete;
  for(u32 i=0;i<128;i++){c->data[23+index*128+i]=p[9+i];c->sum+=p[9+i];}c->next++;return 1;
 }
 if(p[7]==2){
  if(n!=11)goto bad;if(c->next!=32)goto incomplete;if((c->sum+p[8])&127)goto bad;
  sum=0;for(u32 i=2;i<4119;i++)sum+=c->data[i];c->data[4119]=(u8)(0u-sum)&127;c->data[4120]=247;c->active=0;
  if(!dx7_library_packet(c->data,4121,bank)){REPORT("BANK SAVE ERROR");return 0;}
  REPORT("LEGACY BANK SAVED");return 2;
 }
bad:c->active=0;REPORT("BANK RX ERROR");return 0;
incomplete:c->active=0;REPORT("INCOMPLETE BANK");return 0;
}
