/* Note120 : LEDs de pages B, mapping et writer boolean natifs.
 * API : callback precedent, poll precedent, obj, track, step, pattern, play, clock.
 * Aucun rendu audio ni port MIDI ; longueur commune via setter natif UI.
 */
typedef unsigned int u32;
volatile u32 pg_api[12];
static u32 pg_last;
#define V(i) (*(volatile u32 *)pg_api[i])

/* NORMAL natif : longueur commune A en mot BE ; mode1 garde les voies B. */
static u32 common(void){
 volatile unsigned char *a=*(volatile unsigned char **)0x40a7887c;
 if(!a||a[30667]!=0)return 0;
 u32 len=*(volatile unsigned short *)(a+30662);return len>=1&&len<=64?len:0;
}
static u32 sync_length(u32 pattern){
 u32 len=common(),changed=0;if(!len||!pattern||pattern==V(9))return 0;
 volatile unsigned char *p=(volatile unsigned char *)pattern;
 for(u32 lane=0;lane<6;lane++,p+=264)if(p[4]!=len){p[4]=len;changed=1;}
 return changed;
}
u32 pg_clock(u32 runtime,u32 pattern,u32 clock,u32 now,u32 mode){
 sync_length(pattern);return ((u32(*)(u32,u32,u32,u32,u32))pg_api[8])(runtime,pattern,clock,now,mode);
}
u32 pg_config(u32 pattern,u32 lane,u32 field,u32 value){
 u32 len=common();
 if(field==4&&len){
  if(pattern==V(5)&&pattern!=V(9)&&V(2)&&lane<6&&value>=1&&value<=64){
   u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));if(sr&0x700)return 0;
   u32 ui=*(volatile u32 *)0x40fe4228;if(!ui)return 0;
   u32 object=((u32(*)(u32))0x4000f208)(ui);if(!object)return 0;
   volatile unsigned char *header=*(volatile unsigned char **)(object+60);
   if(!header||header[25]!=0)return 0;
   /* Le setter Len stock notifie le projet et revalide aussi la page A. */
   ((void(*)(u32,u32))0x4002fbf6)(0,value);
   value=*(volatile unsigned short *)(header+20);
   if(value<1||value>64)return 0;
   volatile unsigned char *p=(volatile unsigned char *)pattern;
   for(u32 i=0;i<6;i++,p+=264)p[4]=value;
  }else value=len;
 }
 return ((u32(*)(u32,u32,u32,u32))pg_api[10])(pattern,lane,field,value);
}

static u32 recording(void){
 u32 ui=((u32(*)(void))0x400cf9a8)();
 return ui?(((u32(*)(u32))0x4006b978)(ui)&255):0;
}
u32 pg_open(void){
 u32 page=0,inherit=common()&&!V(2);
 if(inherit){
  u32 ui=((u32(*)(void))0x400cf866)();
  if(ui){u32 settings=((u32(*)(u32))0x4000eb90)(ui);if(settings)page=((u32(*)(u32))0x400124b8)(settings);}
 }
 u32 result=((u32(*)(void))pg_api[11])();
 if(result&&inherit&&V(2)&&V(5)&&V(3)<6){
  sync_length(V(5));u32 len=((volatile unsigned char *)V(5))[264*V(3)+4];
  if(page<4&&page*16<len){V(4)=page*16;((void(*)(u32))0x400760ba)(V(2));}
 }
 return result;
}
static int playing(void){
 if(*(volatile u32 *)0x40a7883c!=1 || !V(5) || V(5)!=V(6) || !V(7) || V(3)>5)return -1;
 volatile u32 *clock=(volatile u32 *)V(7);if(clock[0]!=1)return -1;
 u32 lane=V(3),len=((volatile unsigned char *)V(5))[264*lane+4],next=clock[2+2*lane];
 if(!len||len>64||next>=len)return -1;
 return next?next-1:len-1;
}
u32 pg_led(void *handler,u32 flags,u32 *mask){
 u32 result=((u32(*)(void*,u32,u32*))pg_api[0])(handler,flags,mask);
 if(!V(2)||(u32)handler!=V(2)+0x500||!V(5)||V(3)>5)return result;
 u32 selected=(V(4)>>4)&3,rec=recording(),len=((volatile unsigned char *)V(5))[264*V(3)+4];int step=playing();
 void *led=(void*)((u32(*)(void))0x400cfaf4)();if(!led)return result;
 for(u32 page=0;page<4;page++){
  u32 id=((u32(*)(u32))0x400060ac)(page);if(id>53)continue;
  mask[1-(id>>5)]|=1u<<(id&31);
  u32 active=step>=0&&page==((u32)step>>4);
  u32 on=rec?(active?(((u32)step&3)>1):(page==selected)):
   (page*16<len&&(!active||(((u32)step&3)<=1)));
  ((void(*)(void*,u32,u32,void*))0x40005fe6)(led,id,on,(void*)0x404a8cb8);
 }
 return result;
}
void pg_poll(void){
 u32 changed=sync_length(V(5));if(V(6)!=V(5))changed|=sync_length(V(6));
 if(common()&&((V(4)&48)>=common())){V(4)&=15;changed=1;}
 ((void(*)(void))pg_api[1])();
 if(!V(2)){pg_last=0xffffffff;return;}
 int step=playing();u32 key=((V(4)>>4)&3)|(V(3)<<8)|(recording()?0x10000:0);
 if(step>=0)key|=0x80|((u32)step>>4<<2)|((((u32)step&3)>1)<<4);
 if(changed||key!=pg_last){pg_last=key;((void(*)(u32))0x400760ba)(V(2));}
}
