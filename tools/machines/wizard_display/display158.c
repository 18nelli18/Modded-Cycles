/* Wizard158 : vue d accueil seulement. Aucun setter, fichier ou chemin audio.
 * Bitmap128x64 natif, colonnes min/max bornees et cachees par slot/hash/taille.
 * Les popups et fenetres natives gardent leur rendu et toutes leurs touches. */
typedef unsigned int u32;typedef int s32;typedef unsigned short u16;typedef signed short s16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern u32 ws_previous_draw(u32,u32),sx_track(void);
extern const u16*ws_params(u32);
extern volatile u32 ws_slot_base[64],ws_slot_count[64],ws_slot_size[64],ws_slot_hash[64],ws_slot_side[64],ws_track_slot[6],ws_mode[6];
extern const char ws_names[];extern const u8 ws_pcm_top[];
static s32 low[122],high[122];
static u32 cache_base,cache_count,cache_hash,cache_side,cache_slot,cache_size,valid,peak;
static void pixel(u32*fb,u32 x,u32 y){if(x<128&&y<64){u32 yy=63-y;fb[x*2+(yy>>5)]|=1u<<(31-(yy&31));}}
static void line(u32*fb,u32 x,u32 y0,u32 y1){for(u32 y=y0;y<=y1&&y<64;y++)pixel(fb,x,y);}
static void text(u32 canvas,u32*font,u32 x,u32 top,const char*value){N(0x40071a04)(canvas,font,x,55-top,0,"%s",value);}

#ifdef WS_VOLUME159
/* Niveau de piste natif, pas un faux vu-metre. Le getter renvoie un octet. */
static void volume(u32*fb,u32 lane,u32 right){
 u32 root=N(0x400cf866)();if(!root)return;u32 kit=N(0x4000eb9c)(root);if(!kit)return;
 u32 value=N(0x40009c5a)(kit,lane)&255;if(value>127)value=127;
 u32 x0=24,x1=right>6?right-6:24;if(x1>88)x1=88;if(x1<=x0)return;u32 count=(x1-x0+2)/6,fill=value*count/127;
 for(u32 i=0;i<count;i++){
  u32 x=x0+i*6;
  for(u32 dx=0;dx<4;dx++)for(u32 y=57;y<=61;y++)
   if(i<fill||dx==0||dx==3||y==57||y==61)pixel(fb,x+dx,y);
 }
}
#endif

static u32 scan(u32 slot,u32 base,u32 count,u32 size,u32 hash,u32 side){
 if(valid&&cache_base==base&&cache_count==count&&cache_hash==hash&&cache_side==side&&cache_slot==slot&&cache_size==size)return 1;
 valid=0;peak=256;
 const s16*mid=(const s16*)(base+64);const s16*other=side?(const s16*)(base+64+side):0;
 for(u32 x=0;x<122;x++){
  u32 first=x*count/122,end=(x+1)*count/122;if(end<=first)end=first+1;if(end>count)end=count;
  u32 step=(end-first+31)/32;if(!step)step=1;s32 lo=32767,hi=-32768;
  for(u32 i=first;i<end;i+=step){s32 a=mid[i],b=a;if(other){s32 s=other[i];b=a-s;a+=s;}if(a<lo)lo=a;if(a>hi)hi=a;if(b<lo)lo=b;if(b>hi)hi=b;}
  low[x]=lo;high[x]=hi;u32 a=lo<0?(u32)-lo:(u32)lo,b=hi<0?(u32)-hi:(u32)hi;if(a>peak)peak=a;if(b>peak)peak=b;
 }
 if(ws_slot_base[slot]!=base||ws_slot_count[slot]!=count||ws_slot_hash[slot]!=hash||ws_slot_side[slot]!=side||ws_slot_size[slot]!=size)return 0;
 cache_base=base;cache_count=count;cache_hash=hash;cache_side=side;cache_slot=slot;cache_size=size;valid=1;return 1;
}
u32 ws_draw(u32 view,u32 canvas){
 u32 previous=ws_previous_draw(view,canvas);if(previous)return previous;
 if(view&&(*(const u32*)view!=0x400ffe20||*(const u32*)(view+284)))return 0;
 u32 lane=sx_track();if(lane>=6)return 0;const u16*p=ws_params(lane);if(!p||(p[9]>>8)!=6)return 0;
 /* Memes deux etats prioritaires que DrumSelect : note/potard et vue speciale.
  * Deleguer AVANT toute lecture PCM ou ecriture de pixels. */
 u32 ui=N(0x400cf9a8)();if(ui&&((N(0x4006b704)(ui)&255)||(N(0x4006b736)(ui)&255)||(N(0x4006bb18)(ui)&255)))return 0;
 if(!canvas||*(const u32*)(canvas+12)!=2)return 0;u32*fb=*(u32**)(canvas+16);if(!fb)return 0;
 u32 slot=ws_track_slot[lane],base=0,count=0,size=0,hash=0,side=0,loaded=0;
 if(slot<64){base=ws_slot_base[slot];count=ws_slot_count[slot];size=ws_slot_size[slot];hash=ws_slot_hash[slot];side=ws_slot_side[slot];
  u32 top=(u32)ws_pcm_top;
  loaded=hash&&base>=0x4a810000&&base<top&&size>=64&&size<=0x1800000&&size<=top-base&&count&&count<=0xc00000&&count<=(size-64)/2;
  if(loaded&&side&&(side>size-64||count>(size-64-side)/2||side<count*2))loaded=0;
  if(loaded)loaded=scan(slot,base,count,size,hash,side);
 }
 for(u32 i=0;i<256;i++)fb[i]=0;
 char title[18],label[24];u32 n=0;
 if(loaded){const char*name=ws_names+slot*32;while(n<16&&name[n]){title[n]=name[n];n++;}
  if(n==16&&name[16])title[15]='~';title[n]=0;
  /* Un nom court conserve les points internes ; retirer seulement .wav final. */
  if(n>=4&&title[n-4]=='.'&&(title[n-3]=='w'||title[n-3]=='W')&&(title[n-2]=='a'||title[n-2]=='A')&&(title[n-1]=='v'||title[n-1]=='V'))title[n-4]=0;
  if(!title[0])N(0x40000e6e)(title,"Sample %u",slot+1);
 }else{const char*s="Sample Wizard";while(*s)title[n++]=*s++;title[n]=0;valid=0;}
 u32 duration_x=91;u32 font[2];N(0x40072260)(font,0x40140ab0);
 text(canvas,font,3,2,title);
 if(loaded)N(0x40000e6e)(label,"S%02u",slot+1);else N(0x40000e6e)(label,"S--");text(canvas,font,107,2,label);
 /* Bandeau inverse ; les coords du framebuffer sont retournees dans pixel(). */
 for(u32 x=0;x<128;x++)for(u32 y=0;y<12;y++){u32 yy=63-y;fb[x*2+(yy>>5)]^=1u<<(31-(yy&31));}
 for(u32 x=2;x<126;x++)pixel(fb,x,53);
 N(0x40000e6e)(label,"T%u",lane+1);text(canvas,font,3,55,label);
 if(loaded){u32 centis=count/480;N(0x40000e6e)(label,"%u.%02us",centis/100,centis%100);u32 len=0;while(label[len])len++;duration_x=len<20?126-6*len:3;text(canvas,font,duration_x,55,label);
  for(u32 x=0;x<122;x++){
   s32 a=32-high[x]*17/(s32)peak,b=32-low[x]*17/(s32)peak;if(a<14)a=14;if(b>50)b=50;
   if(a>b){s32 t=a;a=b;b=t;}line(fb,x+3,(u32)a,(u32)b);
  }
  for(u32 x=3;x<125;x+=3)pixel(fb,x,32);
  /* Repere Start/Position, pas un faux curseur anime : Stretch utilise Speed. */
  u32 mode=ws_mode[lane];if(mode<=3||mode==5){s32 start=(s16)p[11];if(start<0)start=0;if(start>32512)start=32512;u32 x=3+(u32)start*121/32768;
   for(u32 y=14;y<51;y+=2)pixel(fb,x,y);for(s32 d=-2;d<=2;d++)pixel(fb,(u32)((s32)x+d),13);
  }
 }else{text(canvas,font,37,29,"No sample");text(canvas,font,91,55,"--.--s");}
 #ifdef WS_VOLUME159
 volume(fb,lane,duration_x);
#else
 (void)duration_x;
#endif
 N(0x40072080)(font);return 1;
}
