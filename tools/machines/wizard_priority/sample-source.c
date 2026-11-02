/* Un token SMP choisit un sample, pas un instantane des33 parametres.
 * Le pointeur du son du pool reste intact pour sp_lock et les previews.
 * Aucun etat, allocation ou traitement par sample audio. */
typedef unsigned int u32;typedef unsigned char u8;
u32 ws_source(u32 sound,u32 track){
 if(track>=6)return sound;
 const u8*p=(const u8*)sound;
 if(p[38]!=6||p[4]!='S'||p[5]!='M'||p[6]!='P')return sound;
 for(u32 i=7;i<15;i++){u32 c=p[i];if(!((c>='0'&&c<='9')||(c>='A'&&c<='F')))return sound;}
 u32 kit=*(volatile u32*)0x40a78888;if(!kit)return sound;
 u32 own=kit+28+100*track;
 return *(const u8*)(own+38)==6?own:sound;
}
