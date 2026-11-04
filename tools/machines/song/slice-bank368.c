/* Clavier normal : FUNC ajoute16 slices seulement pour Wizard en mode Slice.
 * Appel UI lors d'une attaque acceptee ; aucun hook audio ni nouvel etat. */
typedef unsigned int u32;
extern volatile u32 sn_modes[6];
#define N(a) ((u32(*)())(a))
u32 sn_offset368(u32 track,const u32*event){
 if(track>=6||!event||event[3]<16||event[3]>31||(event[4]&9)!=1)return 0;
 if(!(event[4]&2)&&!N(0x4007faf4)(1))return 0;
 if(N(0x4007faf4)(2)||N(0x4007faf4)(3))return 0;
 if(N(0x4001e318)(0,track)!=6||sn_modes[track]!=2)return 0;
 return 16;
}
