typedef unsigned int u32;
#define N(a) ((u32(*)())(a))
extern volatile u32 fx_menu_open,fx_menu_slot,fx_menu_cursor;
extern const u32 nv_rev_order[8],fx_del_order[7];extern const char*const fx_rev_names[],*const fx_del_names[];
void nv_bypass(int*out,const int*in){for(u32 i=0;i<64;i++)out[i]=in[i];}
u32 nv_overlay(u32 view,u32 canvas){
 (void)view;if(!fx_menu_open)return 0;
 u32 slot=fx_menu_slot,n=slot?7:8,cursor=fx_menu_cursor;if(cursor>=n)cursor=fx_menu_cursor=n-1;
 N(0x40070efc)(canvas,12,4,119,57,0xffffffffu);N(0x40070efc)(canvas,10,6,117,59,0);N(0x40070c4e)(canvas,10,6,117,59,0xffffffffu);
 N(0x40071a04)(canvas,0x40ea14cc,17,48,0x10,"%s",slot?"DELAY FX":"REVERB FX");N(0x40070efc)(canvas,12,44,115,44,0xffffffffu);
 u32 top=cursor?cursor-1:0;if(top+3>n)top=n-3;
 for(u32 i=top;i<top+3;i++){u32 y=33-12*(i-top),m=(slot?fx_del_order:nv_rev_order)[i];N(0x40071a04)(canvas,0x40ea14cc,18,y,0x10,"%s",(slot?fx_del_names:fx_rev_names)[m]);if(i==cursor)N(0x40070f6e)(canvas,14,y-1,112,y+10,0xffffffffu);}
 if(top)N(0x40071a04)(canvas,0x40ea14cc,108,33,0x10,"%s","^");if(top+3<n)N(0x40071a04)(canvas,0x40ea14cc,108,9,0x10,"%s","v");return 1;
}
/* Le dessin de pile appelle aussi le clone GCC a un seul argument. */
u32 nv_overlay_canvas(u32 canvas){return nv_overlay(0,canvas);}
