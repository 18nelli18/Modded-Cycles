/* Longueur commune aux pages physiques16pas. Aucun heap/E/S dans l'horloge.
 * Tag PL/n/~n dans les quatre derniers octets reserves de l'en-tete64octets.
 * Le codec natif exporte les64octets ; notre decodeur valide ce seul tag. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
#define HEADER 30642u
#ifdef PAGE_WARP195
static u32 pl_valid(const u8*h){return h[60]==80&&(h[61]==76||h[61]==87)&&h[62]>=1&&h[62]<=16&&h[63]==(u8)~h[62];}
u32 pl_length(const u8*h){return pl_valid(h)?h[62]:16;}
u32 pl_warp(const u8*h){return pl_valid(h)&&h[61]==87;}
#else
u32 pl_length(const u8*h){u32 n=h[62];return h[60]==80&&h[61]==76&&n>=1&&n<=16&&h[63]==(u8)~n?n:16;}
#endif
u32 pl_next(const u8*p,u32 next){u32 n=pl_length(p+HEADER);return (next&15)>=n?(next+15)&~15u:next;}
u32 pl_effective(const u8*p,u32 len){u32 n=pl_length(p+HEADER),tail=len&15;return (len>>4)*n+(tail<n?tail:n);}
extern u32 pl_old_decode(u8*,const u8*),pl_old_init(u8*,u32);
u32 pl_decode(u8*d,const u8*s){u32 result=pl_old_decode(d,s);if((result&255)&&d){u32 n=s?pl_length(s):16;
#ifdef PAGE_WARP195
u32 warp=s?pl_warp(s):0;
#endif
d[60]=80;d[61]=76;
#ifdef PAGE_WARP195
if(warp)d[61]=87;
#endif
d[62]=n;d[63]=~n;}return result;}
u32 pl_init(u8*d,u32 flags){u32 result=pl_old_init(d,flags);if(d&&!flags){d[60]=d[61]=d[62]=d[63]=0;}return result;}
static u32 ui_header(void){u32 root=N(0x400cf866)();if(!root)return 0;u32 p=N(0x4000f208)(root);return p?N(0x4000d0dc)(p):0;}
static u8*raw_header(u32 object){u32 vt=object?*(u32*)object:0;return vt?(u8*)N(*(u32*)(vt+40))(object):0;}
void pl_change(u32 **closure,u32 unused,s32 delta){
 (void)closure;(void)unused;u32 object=ui_header();u8*h=raw_header(object);if(!h||!delta)return;
 s32 n=pl_length(h);n+=delta>16?16:delta< -16?-16:delta;if(n<1)n=1;if(n>16)n=16;
 if((u32)n==pl_length(h))return;
 u32 sr;__asm__ volatile("move.w %%sr,%0\n move.w #0x2700,%%sr":"=d"(sr)::"memory","cc");
#ifdef PAGE_WARP195
 u32 warp=pl_warp(h);
#endif
 h[60]=80;h[61]=76;h[62]=n;h[63]=~n;
#ifdef PAGE_WARP195
 if(warp)h[61]=87;
#endif
 __asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");
 /* Meme notification d'en-tete que le setter Len natif. */
 N(*(u32*)(*(u32*)object+16))(object,0);
}
void pl_draw(u32 **closure,u32 unused,u32 canvas,u8*item,u32 flags){
 (void)closure;(void)unused;u8*h=raw_header(ui_header());u32 buf[2],n=h?pl_length(h):16;
 N(0x40072260)(buf,0x40140ab0);N(0x40071a04)(canvas,buf,item+24,flags,4,"%d",n);N(0x40072080)(buf);
}
typedef struct{u32 storage,unused,manager,invoke;} Fn;
extern void pl_label(void);
#ifdef PAGE_WARP195
extern void pl_warp_label(void);
void pl_warp_change(u32 **c,u32 unused,s32 delta){
 (void)c;(void)unused;u32 object=ui_header();u8*h=raw_header(object);if(!h||!delta)return;
 u32 enabled=delta>0,n=pl_length(h);if(enabled==pl_warp(h))return;u32 sr;
 __asm__ volatile("move.w %%sr,%0\n move.w #0x2700,%%sr":"=d"(sr)::"memory","cc");
 h[60]=80;h[61]=enabled?87:76;h[62]=n;h[63]=~n;
 __asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");N(*(u32*)(*(u32*)object+16))(object,0);
}
void pl_warp_draw(u32 **c,u32 unused,u32 canvas,u8*item,u32 flags){
 (void)c;(void)unused;u8*h=raw_header(ui_header());u32 buf[2];N(0x40072260)(buf,0x40140ab0);N(0x40071a04)(canvas,buf,item+24,flags,4,"%s",h&&pl_warp(h)?"ON":"OFF");N(0x40072080)(buf);
}
static void pl_add_item(u32 view,u32 warp){
 Fn f[4];u32 data[4],item;const u32 inv[4]={warp?(u32)pl_warp_label:(u32)pl_label,0x4002ccd0,warp?(u32)pl_warp_draw:(u32)pl_draw,warp?(u32)pl_warp_change:(u32)pl_change};
#else
void pl_menu_add(u32 view){
 Fn f[4];u32 data[4],item;const u32 inv[4]={(u32)pl_label,0x4002ccd0,(u32)pl_draw,(u32)pl_change};
#endif
 /* Les quatre captures4octets sont detruites par les gestionnaires natifs. */
 for(u32 i=0;i<4;i++){data[i]=N(0x400802e0)(4);if(!data[i]){for(u32 j=0;j<i;j++)N(0x400802ec)(data[j]);return;}}
 item=N(0x400802e0)(84);if(!item){for(u32 i=0;i<4;i++)N(0x400802ec)(data[i]);return;}
 for(u32 i=0;i<4;i++){*(u32*)data[i]=view;f[i].storage=data[i];f[i].unused=0;f[i].manager=0x4002cf00;f[i].invoke=inv[i];}
 N(0x400734b0)(item,&f[0],&f[1],&f[2],&f[3],-1,8);N(0x40072ce6)(view,item);
 for(u32 i=0;i<4;i++)N(0x400cf044)(&f[i]);
}
#ifdef PAGE_WARP195
void pl_menu_add(u32 view){pl_add_item(view,0);pl_add_item(view,1);}
#endif
extern u32 pl_old_led(u32,u32,u32);
u32 pl_led(u32 view,u32 arg,u32 canvas){
 /* Le premier claimant LED gagne. Revendiquer les16pads avant le callback
  * natif, qui conserve les LEDs PAGE et tout le reste de son affichage. */
 if(view&&*(u32*)view==0x40103f34){
  u32 begin=*(u32*)(view+4),end=*(u32*)(view+8),index=*(u32*)(view+20)+*(u32*)(view+24);
  if(end>=begin&&index<(end-begin)/8){u32 item=*(u32*)(begin+index*8);
   if(item&&(*(u32*)(item+56)==(u32)pl_draw
#ifdef PAGE_WARP195
      ||*(u32*)(item+56)==(u32)pl_warp_draw
#endif
   )){u8*h=raw_header(ui_header());u32 n=h?pl_length(h):16,led=N(0x400cfaf4)();
    for(u32 i=0;i<16;i++){
#ifdef PAGE_DARK194
     /* L'API booleenne native revendique OFF=1, ON=2 ;3 clignote. */
     N(0x40005fe6)(led,i+1,i<n,0x404a8cb8);
#else
     N(0x40005f86)(led,i+1,i<n?2:3,0x404a8cb8);
#endif
    }
   }
  }
 }
 return pl_old_led(view,arg,canvas);
}
#ifdef PAGE_GRID197
extern u32 pg_old_led(u32,u32,u32),pg_old_key(u32,u32);
static u32 pg_grid(void){u32 state=N(0x400cf9a8)();return state&&(N(0x4006b978)(state)&255)&&!(N(0x4006bb18)(state)&255);}
static u32 pg_length(void){u8 *h=raw_header(ui_header());return h?pl_length(h):16;}
u32 pg_led(u32 view,u32 arg,u32 canvas){
 if(pg_grid()){u32 n=pg_length();if(n<16){u32 led=N(0x400cfaf4)();for(u32 i=n;i<16;i++)N(0x40005fe6)(led,i+1,0,0x404a8cb8);}}
 return pg_old_led(view,arg,canvas);
}
u32 pg_key(u32 view,u32 event){
 u32 code=N(0x4007240c)(event);
 if(code>=16&&code<32&&pg_grid()&&code-16>=pg_length())return 1;
 return pg_old_key(view,event);
}
#endif
