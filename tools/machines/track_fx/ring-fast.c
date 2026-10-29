/* Memes phase, interpolation et arrondis. Aux bornes de profondeur,
 * le gain est exactement nul ou egal au sinus, sans division par127. */
#ifndef FX_INPUT_FIX
#error Le raccourci exige le chemin Q31 historique FX_INPUT_FIX.
#endif
void fx_ring(s32*out,const s32*in){
 u32 f=fx_ring_freq&127,d=fx_ring_depth&127,step=ring_step[f];
 if(!d){ring_phase+=step*32u;for(u32 i=0;i<64;i++)out[i]=0;return;}
 if(d==127){
  for(u32 i=0;i<32;i++){s32 g=sine(ring_phase);ring_phase+=step;for(u32 c=0;c<2;c++)out[2*i+c]=((in[2*i+c]>>16)*g)*2;}
  return;
 }
 for(u32 i=0;i<32;i++){s32 g=sine(ring_phase)*(s32)d/127;ring_phase+=step;for(u32 c=0;c<2;c++)out[2*i+c]=((in[2*i+c]>>16)*g)*2;}
}
