/* POTS modele27, DSP intact ; integration dans le slot delay partage.
 * Le fondu32blocs conserve les autres modes. Une passe native silencieuse
 * laisse des buffers DMA nuls quand POTS prend le slot, comme modele27.
 * Le ring prive46980000..469c0000 ne chevauche ni GATED ni WAVE. */
typedef unsigned int u32;typedef int s32;typedef short s16;
extern volatile u32 cr_mode;
extern u32 fx_delay_state[];
extern void mf_old_pots_delay(s32*,const s32*,const s16*,const s32*,const s32*);
extern void pots_native(s32*,const s32*,const s16*),pots_process(s32*,const s32*,const s16*),pots_reset(void);
u32 pots_slot_active,pots_slot_gain=256,pots_slot_prior=256;
static u32 previous_mode;
static s32 silence[64],discard[64];
static const s16 no_feedback[2]={0,0};
void pots_slot_delay(s32*out,const s32*in,const s16*params,const s32*dl,const s32*dr){
 u32 wanted=cr_mode==12;
 if(wanted!=pots_slot_active){
  pots_slot_gain=pots_slot_gain>=8?pots_slot_gain-8:0;
  if(!pots_slot_gain){
   if(wanted){fx_delay_state[4]=0;pots_native(discard,silence,no_feedback);}
   pots_reset();pots_slot_active=wanted;
  }
 }else if(pots_slot_gain<256)pots_slot_gain+=8;
 if(pots_slot_active){
  if(*(volatile s32*)0x40149310>0)pots_process(out,in,params);
  else for(u32 i=0;i<64;i++)out[i]=0;
 }else{
  u32 mode=cr_mode;if(wanted)cr_mode=previous_mode;else previous_mode=mode;
  mf_old_pots_delay(out,in,params,dl,dr);cr_mode=mode;
 }
 if(pots_slot_gain!=256||pots_slot_prior!=256)for(u32 i=0;i<32;i++){
  s32 g=(s32)pots_slot_prior+(((s32)pots_slot_gain-(s32)pots_slot_prior)*(s32)(i+1)>>5);
  for(u32 c=0;c<2;c++)out[2*i+c]=(out[2*i+c]>>8)*g;
 }
 pots_slot_prior=pots_slot_gain;
}
