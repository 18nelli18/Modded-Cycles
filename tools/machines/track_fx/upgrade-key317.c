/* DATA distant prive : seulement le vrai dialogue de confirmation OS.
 * La requete RPC planifie une tache UI native ; aucun hook ni etat audio.
 * RTTI du callback de progression OS verifie avant toute touche injectee.
 */
typedef unsigned int u32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern void uk_old_request(const u8*),uk_old_send(u8*);
static volatile u32 queued,status,sequence,reply_pending;
static const char uk_type_name[]="SupermodelPrivateUpgradeKey";
static const u32 uk_typeinfo[2]={0x40123e94,(u32)uk_type_name};
u32 uk_manager(u32*out,const u32*in,u32 op){
 if(op==0)*out=(u32)uk_typeinfo;
 else if(op==1)*out=(u32)in;
 else if(op==2){out[0]=in[0];out[1]=in[1];}
 return 0;
}
static u32 pointer(u32 p){return p>=0x40400000u&&p<0x46a00000u&&!(p&3);}
u32 uk_target(u32 app){
 if(!pointer(app))return 0;
 u32 sentinel=app+64+20,node=*(u32*)sentinel,upgrade=0,confirm=0,count=0;
 while(node!=sentinel&&count++<16){
  if(!pointer(node))return 0;
  u32 view=*(u32*)(node+8);
  if(pointer(view)){
   u32 vt=*(u32*)view;
   if(vt==0x40111104)upgrade=view;
   if(vt==0x40111544||vt==0x40111054){
    u32 storage=view+92,manager=*(u32*)(view+100),type=0;
    if(vt==0x40111054){
     u32 wrapper=*(u32*)(view+140);
     if(*(u32*)(view+148)!=0x400e7348||*(u32*)(view+152)!=0x400e71c6||!pointer(wrapper)||*(u32*)wrapper!=view){node=*(u32*)node;continue;}
     storage=wrapper+4;manager=*(u32*)(wrapper+12);
    }
    if(manager>=0x40000400u&&manager<0x401aa140u){
     N(manager)(&type,(const void*)storage,0);
     if(type==0x40110f9c)confirm=view;
    }
   }
  }
  node=*(u32*)node;
 }
 return node==sentinel&&upgrade?confirm:0;
}
void uk_run(const void*unused){
 (void)unused;queued=0;
 u32 app=N(0x400d0974)(),target=uk_target(app);
 if(!target){status=3;return;}
 volatile u32 event[6];event[0]=0x400fbe5c;event[1]=0;event[2]=*(volatile u32*)0xfc07000c;event[3]=32;event[4]=16;event[5]=0;
 /* Meme consommateur natif que DATA : aucune selection de menu automatique. */
 N(*(u32*)target==0x40111054?0x40073bac:0x4006f25e)(target,event);status=2;
}
void uk_request(const u8*msg){
 uk_old_request(msg);
 if(msg[8]!=2)return;
 const u8*p=*(const u8*const*)(msg+12),*end=*(const u8*const*)(msg+16);
 if(end<p||end-p!=13)return;
 const char*magic="SMUK317!";for(u32 i=0;i<8;i++)if(p[5+i]!=(u8)magic[i])return;
 sequence=((u32)p[0]<<8)|p[1];reply_pending=1;
 if(queued){status=4;return;}
 volatile u32 fn[4];fn[0]=fn[1]=0;fn[2]=(u32)uk_manager;fn[3]=(u32)uk_run;queued=1;status=1;
 N(0x400072c0)(N(0x400d0974)(),fn);
}
void uk_send(u8*msg){
 uk_old_send(msg);
 if(!reply_pending||msg[8]!=0x82)return;
 u8*p=*(u8**)(msg+12),*end=*(u8**)(msg+16);
 if(end<p||end-p!=15||(((u32)p[2]<<8)|p[3])!=sequence)return;
 reply_pending=0;p[5]='U';p[6]='K';p[7]=(u8)status;p[8]=(u8)queued;
 for(u32 i=9;i<15;i++)p[i]=0;
}
