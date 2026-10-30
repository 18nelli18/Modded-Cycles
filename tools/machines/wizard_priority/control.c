/* CTRL-ALL modifie le son de base, sans rafraichir les slots verrouilles
 * de la note Wizard courante. UI seulement ; aucun travail DSP ajoute. */
typedef unsigned int u32;typedef unsigned char u8;typedef int s32;
#define N(a) ((u32(*)())(a))
#define LIVE(t,s) (*(volatile unsigned short*)(0x800015aeu +66*(t)+2*(s)))
#define SMOOTH(t,s) (*(volatile u32*)(0x800011e8u +4*(7+33*(t)+(s))))
extern volatile u32 wp_mask_pointer;
static u32 armed,protect[6][2],steps[6],project;
static unsigned short prior[6][33];static u32 smooth[6][33];
static u32 lock(void){u32 sr;__asm__ volatile("move.w %%sr,%0\n\tmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");return sr;}
static void unlock(u32 sr){__asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");}
void wp_before(const u32*e){
 armed=0;if(!e||e[0]!=0x400fbebc||e[3]<2||e[3]>15||!N(0x4007faf4)(2)||N(0x4007faf4)(1))return;
 if(!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c)return;
 project=*(volatile u32*)0x40a7887c;u32 root=N(0x400cf866)(),pattern=root?N(0x4000f208)(root):0,clock=N(0x400cfd0e)();if(!pattern||!clock)return;
 u32 excluded=wp_mask_pointer?*(const volatile u8*)wp_mask_pointer:0;
 for(u32 t=0;t<6;t++){
  protect[t][0]=protect[t][1]=0;
  if(excluded&(1u<<t))continue;
  u32 kit=*(volatile u32*)0x40a78888,own=kit?kit+28+100*t:0,current=((volatile u32*)0x800017ec)[t];
  if(current<0x40000000||current>=0x48000000)current=own;
  if(!current||*(const u8*)(current+38)!=6)continue;
  u32 object=N(0x4000cfcc)(pattern,t);if(!object)continue;
  u32 step=N(0x4006a984)(clock,t);steps[t]=step;if(step>=64)continue;
  u32 owner=*(const u32*)(object+44);if(!owner)continue;
  if(current!=own){protect[t][0]=~0u;protect[t][1]=1;}
  else for(u32 slot=0;slot<33;slot++)if((s32)N(0x4000da2a)(owner,t,step,slot)>=0)protect[t][slot>>5]|=1u<<(slot&31);
 }
 u32 sr=lock();for(u32 t=0;t<6;t++)for(u32 s=0;s<33;s++)if(protect[t][s>>5]&(1u<<(s&31))){prior[t][s]=LIVE(t,s);smooth[t][s]=SMOOTH(t,s);}armed=1;unlock(sr);
}
void wp_after(void){
 if(!armed)return;armed=0;if(project!=*(volatile u32*)0x40a7887c)return;
 u32 clock=N(0x400cfd0e)();if(!clock)return;
 u32 same[6];for(u32 t=0;t<6;t++)same[t]=N(0x4006a984)(clock,t)==steps[t];
 u32 sr=lock();for(u32 t=0;t<6;t++)if(same[t])for(u32 s=0;s<33;s++)if(protect[t][s>>5]&(1u<<(s&31))){LIVE(t,s)=prior[t][s];SMOOTH(t,s)=smooth[t][s];}unlock(sr);
}
