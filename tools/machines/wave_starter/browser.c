/* BACK de WAVE : le sous-dossier remonte, sa release ne ferme pas la vue.
 * La racine et les navigateurs des autres machines gardent leur chemin natif. */
typedef unsigned int u32;
extern u32 wave_native_browser_key(u32,const u32*);
extern u32 wave_parent_navigation(u32,const u32*);
static u32 back_owner;
static u32 ours(void){
 u32 lane=*(volatile u32*)0x40a700c4,sounds=*(volatile u32*)0x40a78888;
 return lane<6&&sounds&&*(volatile unsigned char*)(sounds+28+100*lane+38)==14;
}
u32 wave_browser_key(u32 pm,const u32*event){
 if(event&&event[3]==12){
  u32 flags=event[4];
  if(back_owner==pm){if(!(flags&1))back_owner=0;return 1;}
  if((flags&1)&&!(flags&0x2a)&&*(volatile u32*)0x4677ab66&&ours()){
   u32 folder=*(u32*)(pm+640);
   u32 current=((u32(*)(u32))0x4007cf72)(folder);
   if(current!=*(volatile u32*)0x4677ab6e){
    back_owner=pm;wave_parent_navigation(pm,event);return 1;
   }
  }
 }
 return wave_native_browser_key(pm,event);
}
