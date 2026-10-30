/* Commandes physiques limitees a la piste ACID active.
 * PITCH2 et DECAY3 ; aucune interception des gestes FUNC/TRACK/MACHINES. */
typedef unsigned int u32;typedef int s32;
#define N(a) ((u32(*)())(a))
extern u32 aa_glide_get(u32),aa_legato_get(u32);
extern void aa_track_set(u32,u32,u32),fx_notice(const char*);
extern u32 aa_old_encoder(u32,const u32*);
extern void sg_sync(void);
static u32 stamp[12],delta[12],valid;
u32 aa_face_encoder(u32 view,const u32*e){
 if(!e||e[0]!=0x400fbebc||(e[3]!=2&&e[3]!=3)||!N(0x4007faf4)(13)||N(0x4007faf4)(1)||N(0x4007faf4)(2)||N(0x4007faf4)(5))return aa_old_encoder(view,e);
 u32 root=N(0x400cf866)();if(!root)return aa_old_encoder(view,e);
 u32 t=N(0x40012412)(root+48);if(t>=6||N(0x4001e318)(0,t)!=13)return aa_old_encoder(view,e);
 sg_sync();
 u32 k=e[3]-2,index=2*t+k,bit=1u<<index;
 if(e[2]&&(valid&bit)&&stamp[index]==e[2]&&delta[index]==e[4])return 1;
 stamp[index]=e[2];delta[index]=e[4];valid|=bit;
 s32 d=(s32)N(0x4006f73a)(e,1,1),g=aa_glide_get(t),l=aa_legato_get(t);
 if(k)l=d?d>0:l;else{g+=d;if(g<0)g=0;if(g>127)g=127;}
 aa_track_set(t,g,l);N(0x400723e0)(13);
 char text[40];if(k)N(0x40000e6e)(text,"ACID Legato %s",l?"ON":"OFF");else if(!g)N(0x40000e6e)(text,"ACID Glide OFF");else N(0x40000e6e)(text,"ACID Glide %d ms",50+(g-1)*310/126);
 fx_notice(text);return 1;
}
