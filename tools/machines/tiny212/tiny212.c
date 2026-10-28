/* GATE retient l'enveloppe commune ; conserver le vrai coefficient natif
 * pendant le maintien et le remettre avant update/release. Aucun heap/float. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;typedef unsigned short u16;
extern void tn_old_update(s32,void*,const void*);
struct state {u32 held;s32 snap;u32 decay,forced;};static struct state states[6];
void tn_update(s32 note,u8*v,const u8*p){
 u32 offset=(u32)v-0x42308828u;
 if(offset>5u*796u||offset%796u){tn_old_update(note,v,p);return;}
 u32 lane=offset/796u;struct state*s=states+lane;u8*core=(u8*)(0x46780000u+lane*2108u);
 if(*(u32*)(v+44)!=0x54494e59u){s->held=0;s->snap=0;s->forced=0;}
 else if(s->forced){*(u32*)(core+16)=s->decay;s->forced=0;}
 if(*(u32*)(v+56)){s->held=1;s->snap=*(const u16*)(p+30)?12*65536:0;}
 else if(*(u32*)(v+60))s->held=0;
 /* Famille1 : vitesse d'excitation et compteur de porte internes.
  * Famille9 : six amplitudes partielles, phases distinctes en60..83.
  * Leur decroissance se fait dans update, hors enveloppe commune. */
 u32 internal[6],kind=core[0],hold=*(const u16*)(p+32)&&s->held&&!*(u32*)(v+56)&&core[2104]&&!core[2106];
 if(hold&&kind==1){internal[0]=*(u32*)(core+44);internal[1]=*(u16*)(core+60);}
 if(hold&&kind==9)for(u32 i=0;i<6;i++)internal[i]=((u32*)(core+36))[i];
 if(!*(const u16*)(p+30))s->snap=0;
 tn_old_update(note+s->snap,v,p);s->snap=(s->snap*7)/8;
 if(hold&&kind==1){*(u32*)(core+44)=internal[0];*(u16*)(core+60)=(u16)internal[1];}
 if(hold&&kind==9)for(u32 i=0;i<6;i++)((u32*)(core+36))[i]=internal[i];
 s->decay=*(u32*)(core+16);
 if(*(const u16*)(p+32)&&s->held&&core[2104]&&!core[2106]){*(u32*)(core+16)=65536u;s->forced=1;}
}
