/* Eco Delay/Ping : boucle stereo12k/16bits, raccord48k, feedback borne.
 * Time suit la formule stock publiee dans POTS/model27 (MIT, durchgemacht).
 * La ligne POTS est partagee exclusivement : les autres types gardent leur
 * moteur et leur remise a zero. Pas de nouvel espace ring ni d effacement IRQ.
 */
typedef unsigned int u32;typedef int s32;typedef short s16;
extern s16 ed_line[2][65536];
extern volatile u32 ed_panic,ed_native_active,ed_crstate[];
extern volatile u32 ed_pots_active,ed_pots_gain,ed_pots_prior;
extern void ed_native(s32*,const s32*,const s16*),ed_sidechain(s32*,u32);
extern void ed_pots_reset(void);
static const s32 silence[64];static const s16 no_feedback[2];
static struct {u32 epoch,ready,w,n,d8,quiet,level,mode,target,tempo,time;s32 lp[2],previous[2];} st;
const char ed_delay_name[]="EC DELAY",ed_ping_name[]="EC PING";
static s32 sat16(s32 x){return x>32767?32767:x< -32768?-32768:x;}
static void empty(void){st.w=st.n=0;st.lp[0]=st.lp[1]=st.previous[0]=st.previous[1]=0;}
void sf_eco_leave(void){st.ready=st.level=st.quiet=0;empty();}
void sf_eco_delay(s32*out,const s32*in,const s16*params,u32 mode){
 ed_crstate[4]=0;ed_native_active=0;
 if(st.epoch!=ed_panic||st.mode!=mode){st.epoch=ed_panic;st.ready=st.level=st.quiet=0;st.mode=mode;empty();}
 u32 energy=0;for(u32 i=0;i<64;i++)energy|=(u32)in[i];
 if(!energy&&!st.n){for(u32 i=0;i<64;i++)out[i]=0;return;}
 u32 tempo=*(volatile u32*)0x40149310,time=params[0]<0?0:(u32)params[0];if(time>32512)time=32512;
 if(!tempo){for(u32 i=0;i<64;i++)out[i]=0;return;}
 if(!st.ready||st.tempo!=tempo||st.time!=time){
  u32 d=(((time+256)*48000)>>10)*900/tempo;d=d>261120?261120:d<32?32:d;
  st.target=((d+2)/4)<<8;st.tempo=tempo;st.time=time;
 }
 if(!st.ready){
  st.ready=1;st.d8=st.target;ed_crstate[4]=0;ed_native_active=0;
  ed_pots_active=0;ed_pots_gain=ed_pots_prior=256;ed_pots_reset();
  ed_native(out,silence,no_feedback);
 }
 ed_crstate[4]=0;
 s32 change=((s32)st.target-(s32)st.d8)/64;
 if(!change&&st.target!=st.d8)change=st.target>st.d8?1:-1;
 st.d8=(u32)((s32)st.d8+change);u32 delay=st.d8>>8,fraction=st.d8&255;
 u32 feedback=params[1]<0?0:(u32)params[1];if(feedback>32512)feedback=32512;
 feedback=feedback*30000/32512;
 if(energy)st.quiet=0;else if(st.quiet<400000)st.quiet+=32;
 u32 prior=st.level;
 if(st.quiet>delay*4+48000)st.level=st.level>=8?st.level-8:0;
 else if(st.level<256)st.level+=8;
 if(!st.level&&!prior&&!energy){empty();for(u32 i=0;i<64;i++)out[i]=0;return;}
 for(u32 i=0;i<32;i+=4){
  s32 input[2]={0,0},wet[2];
  for(u32 j=0;j<4;j++){input[0]+=in[2*(i+j)]>>18;input[1]+=in[2*(i+j)+1]>>18;}
  for(u32 c=0;c<2;c++){
   st.lp[c]+=(input[c]-st.lp[c])/2;
   s32 a=st.n<delay?0:ed_line[c][(st.w-delay)&65535];
   s32 b=st.n<delay+1?0:ed_line[c][(st.w-delay-1)&65535];
   wet[c]=a+(b-a)*(s32)fraction/256;
  }
  if(mode==5){
   s32 mono=(st.lp[0]+st.lp[1])/2;
   ed_line[0][st.w]=(s16)sat16(mono+wet[1]*(s32)feedback/32768);
   ed_line[1][st.w]=(s16)sat16(wet[0]*(s32)feedback/32768);
  }else for(u32 c=0;c<2;c++)ed_line[c][st.w]=(s16)sat16(st.lp[c]+wet[c]*(s32)feedback/32768);
  for(u32 c=0;c<2;c++){
   s32 sample=st.previous[c]*65536,step=(wet[c]-st.previous[c])*16384;
   for(u32 j=0;j<4;j++){sample+=step;out[2*(i+j)+c]=sample;}
   st.previous[c]=wet[c];
  }
  st.w=(st.w+1)&65535;if(st.n<65535)st.n++;
 }
 if(prior!=256||st.level!=256){
  s32 phase=(s32)prior*32,step=(s32)st.level-(s32)prior;
  for(u32 i=0;i<32;i++){phase+=step;s32 g=phase>>5;out[2*i]=(out[2*i]>>8)*g;out[2*i+1]=(out[2*i+1]>>8)*g;}
 }
 ed_sidechain(out,1);
}
