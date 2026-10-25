"""Projection bornee des dials, conservation canonique pendant MACHINES."""
from wizard_isolation_assets import S
C=r"""
typedef unsigned int u32;typedef unsigned short u16;typedef short i16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern u32 kr_native(u32);extern void kr_bounds(u32,int*);extern u32 kr_menu_native(u32,u32,u32,u32);
static const u32 slot[6]={10,18,11,12,13,14};
typedef struct {u32 obj,valid;u16 values[3][6],applied[6];} Bank;
static Bank banks[6];static u32 active;
static u32 group(u32 machine){return machine==17?2:machine==6?1:0;}
static u8 *sound(u32 obj){u32 vt=*(u32*)obj;return vt?(u8*)N(*(u32*)(vt+40))(obj):0;}
static Bank *bank(u32 obj){if(!active)return 0;for(u32 i=0;i<6;i++)if(banks[i].obj==obj)return &banks[i];return 0;}
static void save(Bank*b,u32 g,const u8*p){for(u32 i=0;i<6;i++)b->values[g][i]=*(const u16*)(p+20+slot[i]*2);b->valid|=1u<<g;}

static void applied(Bank*b,const u8*p){for(u32 i=0;i<6;i++)b->applied[i]=*(const u16*)(p+20+slot[i]*2);}
void kr_fix_snapshot(u32 obj,u32*v,u32 lane){(void)v;if(lane>=6)return;Bank*b=&banks[lane];b->obj=obj;b->valid=0;u8*p=sound(obj);if(p){save(b,group(p[38]),p);applied(b,p);}}
/* La banque conserve les valeurs voulues. Les bornes du moteur courant ne
 * modifient que sa projection, jamais la banque lors d'un simple defilement.
 * Une vraie edition est detectee par comparaison avec la derniere projection. */
u32 kr_menu(u32 view,u32 delta,u32 all,u32 arg){
 u32 previous=active,old[6],packed[6];active=view;
 for(u32 k=0;k<6;k++){old[k]=~0u;Bank*b=&banks[k];
  if(!b->obj){continue;}u8*p=sound(b->obj);if(!p){continue;}old[k]=p[38];packed[k]=*(u32*)(p+72);u32 g=group(old[k]);
  if(!(b->valid&(1u<<g)))save(b,g,p);
  for(u32 i=0;i<6;i++){u16 raw=*(u16*)(p+20+slot[i]*2);if(raw!=b->applied[i])b->values[g][i]=raw;}
 }
 u32 result=kr_menu_native(view,delta,all,arg);
 for(u32 k=0;k<6;k++){Bank*b=&banks[k];if(old[k]==~0u)continue;u8*p=sound(b->obj);if(!p)continue;u32 machine=p[38],g=group(machine),from=group(old[k]);
  if(old[k]!=machine){
   if(!(b->valid&(1u<<g)))save(b,g,p);
   /* Pitch et Decay restent communs entre Wizard et synthese, MIDI isole. */
   if(g<2&&from<2)for(u32 i=0;i<2;i++)b->values[g][i]=b->values[from][i];
   if(machine==6&&from<2&&((packed[k]>>28)==7||(packed[k]>>28)==15))*(u32*)(p+72)=packed[k];
   for(u32 i=0;i<6;i++){
    u32 desc=N(0x4005a692)(slot[i],machine);if(!desc)continue;int limits[3];kr_bounds(desc,limits);
    int value=(i16)b->values[g][i];if(value<limits[0])value=limits[0];if(value>limits[1])value=limits[1];*(u16*)(p+20+slot[i]*2)=(u16)value;
   }
   N(*(u32*)(*(u32*)b->obj+16))(b->obj,0);
  }
  applied(b,p);
 }
 active=previous;return result;
}

u32 kr_reset(u32 obj,u32 old){if(active)return kr_native(obj);u8*p=sound(obj);if(!p)return kr_native(obj);u32 machine=p[38];if(old>18||machine>18)return kr_native(obj);
 Bank*b=bank(obj);u32 from=group(old),to=group(machine),midi=old==17||machine==17;
 /* Hors selection, garder les resets et changements MIDI natifs. */
 if(midi)return kr_native(obj);
 u32 packed=*(u32*)(p+72),tag=packed>>28;u16 before[6];for(u32 i=0;i<6;i++)before[i]=*(u16*)(p+20+slot[i]*2);
 if(b)save(b,from,p);
 u32 result=kr_native(obj);p=sound(obj);if(!p||p[38]!=machine)return result;
 if(!midi&&machine==6&&(tag==7||tag==15))*(u32*)(p+72)=packed;
 for(u32 i=0;i<6;i++){
  u16 value=before[i];
  if(midi){if(!b||!(b->valid&(1u<<to)))continue;value=b->values[to][i];}
  else if(i>=2){if(machine==6){if(b&&(b->valid&2))*(u16*)(p+20+slot[i]*2)=b->values[1][i];continue;}
   if(old==6){if(!b||!(b->valid&1))continue;value=b->values[0][i];}}
  u32 desc=N(0x4005a692)(slot[i],machine);if(!desc)continue;int limits[3];kr_bounds(desc,limits);int bounded=(i16)value;if(bounded<limits[0])bounded=limits[0];if(bounded>limits[1])bounded=limits[1];*(u16*)(p+20+slot[i]*2)=(u16)bounded;
 }
 if(b)save(b,to,p);
 return result;}
"""
