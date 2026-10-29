/* SPDX-License-Identifier: MIT
 * Regroupement borne des jobs natifs de miroirs encore en attente.
 * Le code natif conserve allocation, clonage, encodage et destruction.
 * Aucun compteur de diagnostic ni travail dans le rappel audio. */
#define NG 8u
#define NO 32u
#define SKIP 0xffffffffu
typedef struct {u32 token,model,dest,slot,epoch,refs,pending;} Group;
typedef struct {u32 pointer,token;} Owner;
static volatile Group groups[NG] DATA={{0}};
static volatile Owner owners[NO] DATA={{0}};
static u32 serial DATA=0;
static u32 lock(void){u32 s;__asm__ volatile("move.w %%sr,%0":"=d"(s)::"memory");u32 m=s|0x700;__asm__ volatile("move.w %0,%%sr"::"d"(m):"cc","memory");return s;}
static void unlock(u32 s){__asm__ volatile("move.w %0,%%sr"::"d"(s):"cc","memory");}
static volatile Group *group(u32 token){for(u32 i=0;i<NG;i++)if(groups[i].token==token)return &groups[i];return 0;}
/* Quatre sondes bornent le travail masque. Les tombes conservent les chaines.
 * Une table pleine revient au comportement natif sans supprimer de job. */
static u32 owner(u32 p){for(u32 i=0;i<4;i++){u32 at=((p>>2)+i)&(NO-1),value=owners[at].pointer;if(value==p)return owners[at].token;if(!value)break;}return 0;}
static u32 add_owner(u32 p,u32 token){volatile Group*g=group(token);if(!g)return 0;u32 free=NO;
 for(u32 i=0;i<4;i++){u32 at=((p>>2)+i)&(NO-1),value=owners[at].pointer;if(value==p)return 1;if(value<=1&&free==NO)free=at;if(!value)break;}
 if(free==NO){g->pending=0;return 0;}owners[free].token=token;owners[free].pointer=p;g->refs++;return 1;
}
static void drop(u32 p){u32 irq=lock();for(u32 i=0;i<4;i++){u32 at=((p>>2)+i)&(NO-1),value=owners[at].pointer;if(value==p){volatile Group*g=group(owners[at].token);owners[at].pointer=1;owners[at].token=0;if(g&&g->refs&&!--g->refs){g->pending=0;g->token=0;}break;}if(!value)break;}unlock(irq);}
static u32 begin(u32 model,u32 dest,u32 slot){u32 irq=lock(),epoch=per_edit_epoch;volatile Group*free=0;for(u32 i=0;i<NG;i++){
 volatile Group*g=&groups[i];if(g->token&&g->pending&&g->model==model&&g->dest==dest&&g->slot==slot&&g->epoch==epoch){unlock(irq);return SKIP;}if(!g->token&&!free)free=g;
 }if(!free){unlock(irq);return 0;}do{serial++;}while(!serial||serial==SKIP);u32 token=serial;free->model=model;free->dest=dest;free->slot=slot;free->epoch=epoch;free->refs=0;free->pending=1;free->token=token;unlock(irq);return token;}
static void finish(u32 token){u32 irq=lock();volatile Group*g=group(token);if(g&&!g->refs){g->pending=0;g->token=0;}unlock(irq);}
void per_mirror_notify(void *model,u32 slot,u32 mirror,u32 active){
 u32 m=(u32)model,token=0,dest=active?mirror:mirror+slot*0x1e00u;
 /* Verifier la source comme le helper natif avant de reserver un groupe. */
 u32 vt=*(u32*)model;if(vt){u32 getter=*(u32*)(vt+0x30);if(getter&&dest&&CALL(getter,u32(*)(void*,u32))(model,slot))token=begin(m,dest,slot);}
 if(token==SKIP)return;
 if(active)CALL(0x4000a276,void(*)(void*,u32,u32,u32))(model,slot,mirror,0);
 else CALL(0x4000a12e,void(*)(void*,u32,u32,u32))(model,slot,mirror,0);
 if(token)finish(token);
}
extern u32 pm_manager_a_original(u32*,const u32*,u32),pm_manager_b_original(u32*,const u32*,u32);
static u32 manage(u32*out,const u32*in,u32 mode,u32 active){u32 token=0;
 if(mode==2){u32 p=*in,irq=lock();token=owner(p);
  if(!token&&p){u32*m=(u32*)p;for(u32 i=0;i<NG;i++)if(groups[i].token&&groups[i].pending&&groups[i].epoch==per_edit_epoch&&groups[i].model==m[0]&&groups[i].dest==m[1]&&groups[i].slot==m[2]){token=groups[i].token;break;}}
  if(token&&!add_owner(p,token))token=0;unlock(irq);
 }else if(mode==3)drop(*out);
 u32 result=active?pm_manager_b_original(out,in,mode):pm_manager_a_original(out,in,mode);
 if(mode==2&&token){u32 irq=lock();add_owner(*out,token);unlock(irq);}return result;
}
u32 pm_manager_a(u32*out,const u32*in,u32 mode){return manage(out,in,mode,0);}
u32 pm_manager_b(u32*out,const u32*in,u32 mode){return manage(out,in,mode,1);}
static void running(void*object){u32 p=*(u32*)object,irq=lock();u32 token=owner(p);volatile Group*g=token?group(token):0;if(g){g->pending=0;}unlock(irq);}
extern u32 pm_callback_a_original(void*),pm_callback_b_original(void*);
u32 pm_callback_a(void*object){running(object);return pm_callback_a_original(object);}
u32 pm_callback_b(void*object){running(object);return pm_callback_b_original(object);}

#undef NG
#undef NO
#undef SKIP
