/* Commandes physiques limitees a la piste ACID active.
 * PITCH2 et DECAY3 ; aucune interception des gestes FUNC/TRACK/MACHINES. */
typedef unsigned int u32;typedef int s32;
#define N(a) ((u32(*)())(a))
extern u32 aa_glide_get(u32),aa_legato_get(u32);
extern void aa_track_set(u32,u32,u32),fx_notice(const char*);
extern u32 aa_old_encoder(u32,const u32*);
extern void sg_sync(void);
extern volatile u32 wf_api[];
extern volatile u32 menu,sg_page;
extern u32 sg_encoder(const u32*);
extern u32 sg_key(const u32*),aa_old_key(u32,const u32*);
extern u32 sg_prepare_transport(const u32*);
u32 aa_face_key(u32 view,const u32*e){
 if(menu&&sg_page&&e){u32 code=e[3];if(code==10||code==11)return sg_prepare_transport(e)?aa_old_key(view,e):1;if(code==1){sg_key(e);return aa_old_key(view,e);}return sg_key(e);}
 return aa_old_key(view,e);
}
static u32 stamp[12],delta[12],valid;
static u32 aa_encoder_inner(u32 view,const u32*e){
 if(menu&&sg_page&&e&&e[0]==0x400fbebc)return sg_encoder(e);
 if(!e||e[0]!=0x400fbebc||(e[3]!=2&&e[3]!=3)||!N(0x4007faf4)(13)||N(0x4007faf4)(1)||N(0x4007faf4)(2)||N(0x4007faf4)(5))return aa_old_encoder(view,e);
 u32 root=N(0x400cf866)();if(!root)return aa_old_encoder(view,e);
 u32 t=N(0x40012412)(root+48);if(t>=6||N(0x4001e318)(0,t)!=13)return aa_old_encoder(view,e);
 sg_sync();
 u32 k=e[3]-2,index=2*t+k,bit=1u<<index;
 if(e[2]&&(valid&bit)&&stamp[index]==e[2]&&delta[index]==e[4])return 1;
 stamp[index]=e[2];delta[index]=e[4];valid|=bit;
 s32 d=(s32)N(0x4006f73a)(e,1,1),g=aa_glide_get(t),l=aa_legato_get(t);
 if(k)l=d?d>0:l;else{g+=d;if(g<0)g=0;if(g>127)g=127;}
 aa_track_set(t,g,l);
 /* Marquer l'accord sans consommer la touche : sa release doit atteindre
  * le handler commun et remettre set_held a zero. */
 if(wf_api[5])*(volatile u32*)wf_api[5]=1;
 char text[40];if(k)N(0x40000e6e)(text,"ACID Legato %s",l?"ON":"OFF");else if(!g)N(0x40000e6e)(text,"ACID Glide OFF");else N(0x40000e6e)(text,"ACID Glide %d ms",50+(g-1)*310/126);
 fx_notice(text);return 1;
}
extern void wp_before(const u32*),wp_after(void);
u32 aa_face_encoder(u32 view,const u32*e){wp_before(e);u32 result=aa_encoder_inner(view,e);wp_after();return result;}
