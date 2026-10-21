/* Deux LFO MIDI dans les mots natifs du son :1..8 et23..30. Le canal/port
 * occupe31 ;32 distingue le format CC seul du format MIDI complet.
 * Aucune banque B, pointeur ou phase n'est stocke dans le projet.
 */
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed int i32;
extern u32 mm_cc_edit(u16 *,u32,i32,u32);
static const u16 maximum[8]={32767,23,32767,128,6,32767,4,32767};
static const u16 defaults[8]={16384,9,16384,128,0,0,0,16384};
static u32 enumerated(u32 field){return field==1||field==3||field==4||field==6;}
/* Format K : liberer les slots natifs Swing6 et Chance8. Les champs MIDI
 * Phase/Depth du LFO1 occupent deux anciens emplacements CC reserves. */
static u32 slot(u32 lfo,u32 field,u32 modern){
 if(!lfo&&modern){if(field==5)return 21;if(field==7)return 22;}
 return (lfo?23:1)+field;
}
void mm_setup(u16 *params){
 if(!params||params[32]==0x4d4b)return;
 if(params[32]==0x4d4a){
  params[21]=params[6];params[22]=params[8];
  params[6]=0;params[8]=0;params[19]=64;params[32]=0x4d4b;return;
 }
 if(params[32]!=0x4d49)mm_cc_edit(params,0,0,1);
 for(u32 lfo=0;lfo<2;lfo++)for(u32 field=0;field<8;field++)
  params[slot(lfo,field,1)]=enumerated(field)?defaults[field]<<8:defaults[field];
 params[6]=0;params[8]=0;params[19]=64;
 params[31]=16; /* Canal et port natifs par defaut, pas de transmission. */
 params[32]=0x4d4b;
}
u32 mm_lfo_read(const u16 *params,u32 lfo,u32 field){
 if(!params||lfo>1||field>7)return 0xffffffffu;
 if(params[32]!=0x4d4a&&params[32]!=0x4d4b)return defaults[field];
 u32 value=params[slot(lfo,field,params[32]==0x4d4b)];
 if(enumerated(field))value>>=8;
 return value<=maximum[field]?value:defaults[field];
}
u32 mm_lfo_edit(u16 *params,u32 lfo,u32 field,i32 delta){
 if(!params||lfo>1||field>7)return 0xffffffffu;
 mm_setup(params);
 if(delta>32767)delta=32767;
 if(delta < -32767)delta=-32767;
 i32 value=(i32)mm_lfo_read(params,lfo,field)+delta;
 if(value<0)value=0;
 if(value>maximum[field])value=maximum[field];
 params[slot(lfo,field,1)]=enumerated(field)?value<<8:value;
 return (u32)value;
}
u32 mm_route_read(const u16 *params,u32 port){
 if(!params||(params[32]!=0x4d4a&&params[32]!=0x4d4b))return port?0:16;
 u32 value=port?params[31]>>5:params[31]&31;
 return value<=(port?4u:16u)?value:(port?0:16);
}
u32 mm_route_edit(u16 *params,u32 port,i32 delta){
 if(!params||port>1)return 0xffffffffu;
 mm_setup(params);i32 value=(i32)mm_route_read(params,port);
 if(delta>127)delta=127;
 if(delta < -127)delta=-127;
 value+=delta;if(value<0)value=0;if(value>(port?4:16))value=port?4:16;
 if(port)params[31]=(params[31]&31)|((u32)value<<5);
 else params[31]=(params[31]&0xe0)|(u32)value;
 return (u32)value;
}
u32 mm_channel(const u16 *params,u32 lane){
 if(lane>=6)return 16;
 u32 channel=mm_route_read(params,0);
 if(channel==16){
  u32 root=((u32 (*)(void))0x400cf866)();
  channel=((u32 (*)(u32,u32))0x40012e82)(root+48,lane);
 }
 return channel<16?channel:16;
}
u32 mm_port(const u16 *params){
 u32 port=mm_route_read(params,1);
 if(!port){port=((u32 (*)(void))0x40082686)();if(port==1)port=0;}
 else if(port==1)port=0;
 return port>=2&&port<=4?port:0;
}
