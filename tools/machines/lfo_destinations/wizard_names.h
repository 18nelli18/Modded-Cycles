/* Noms issus des tables natives du mode reel, sans modifier les parametres. */
static u32 wizard_name(u32 context,u32 key,u32 short_name){
 if(key<11||key>14)return 0;
 u32 kit=((u32(*)(void))0x400cf866)();
 if(!kit)return 0;
 u32 handle=*(volatile u32 *)(context+4),track=6;
 for(u32 t=0;t<6;t++)
  if(((u32(*)(u32,u32))0x40009c1a)(kit+116,t)==handle){track=t;break;}
 if(track==6)track=((u32(*)(u32))0x40012412)(kit+48);
 if(track>5)return 0;
 u32 mode=((volatile u32 *)0x401b2554)[track];
 u32 table=0x401ab88a;
 if(mode==3)table=0x401ab916;
 else if(mode==4)table=0x401ab9a2;
 else if(mode==5)table=0x401aba2e;
 else if(mode==6)table=0x401ababa;
 else {
  u32 fx=((volatile u32 *)0x401bc928)[track];
  if(fx==1)table=0x401abb46;
  else if(fx==2||fx==3)table=0x401abbd2;
 }
 return *(volatile u32 *)(table+28*(key-11)+(short_name?12:4));
}
