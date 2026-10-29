/* Budget au debut de l'IRQ jusqu'au gouverneur, plus sa queue precedente.
 * DX mesure en fin d'IRQ : le vieux render seul sous-estimait les pics.
 * IRQ uniquement, aucune E/S, allocation ou horloge musicale modifiee. */
typedef unsigned int u32;typedef unsigned char u8;
volatile u32 gb_irq_active,gb_irq_t0,gb_budget_t0,gb_last_tail,gb_last_total;
extern volatile u32 gb_enabled,gb_peak,gb_over,gb_mask,gb_sum,gb_blocks;
extern void mf_old_dx_before(u32);
void gb_dx_before(u32 now){
 if(!gb_irq_active){mf_old_dx_before(now);return;}
 if(!gb_enabled||*(volatile u32*)0x40a7883c!=1)return;
 u32 mask=0;for(u32 t=0;t<6;t++)if(((volatile u8*)0x46732058)[t])mask|=1u<<t;gb_mask=mask;
}
void gb_finish(u32 now){
 u32 start=gb_irq_t0;if(!gb_irq_active)return;u32 elapsed=now-start;gb_last_total=elapsed;
 if(gb_budget_t0){u32 tail=now-gb_budget_t0;gb_last_tail=tail>90112?90112:tail;}
 if(gb_enabled&&*(volatile u32*)0x40a7883c==1){
  if(elapsed>gb_peak)gb_peak=elapsed;if(elapsed>90112&&gb_over<9999)gb_over++;
  u32 load=elapsed>901120?2560:elapsed*256/90112;
  if(gb_blocks<1000000){gb_sum+=load;gb_blocks++;}
 }
 gb_irq_active=0;gb_irq_t0=gb_budget_t0=0;
}
