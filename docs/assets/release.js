/* Flasher versions, newest first. Shown on the home page and in the flasher.
 * New version: add an entry at the top, with what changed since the previous one:
 *   { version: "1.1", date: "2026-10-15", changes: [{ en: "…", fr: "…" }] }
 */
window.MC_RELEASES = [
  { version: "1.8", date: "2026-10-02", changes: [
    { en: "MACHINES screen: with more than 7 machines, the position dots go on two rows instead of running over the machine picture",
      fr: "Écran MACHINES : au-delà de 7 machines, les points de position passent sur deux lignes au lieu de déborder sur l'image de la machine" },
  ] },
  { version: "1.8", date: "2026-10-02", changes: [
    { en: "Syntakt engines: the flasher takes Syntakt OS 1.42, the version now on elektron.se (1.41 still works: same engines, same firmware)",
      fr: "Moteurs du Syntakt : le flasher accepte l'OS Syntakt 1.42, la version désormais sur elektron.se (la 1.41 marche toujours : mêmes moteurs, même firmware)" },
  ] },
  { version: "1.7", date: "2026-10-02", changes: [
    { en: "Model-TG with the Syntakt engines: a little lighter on the CPU (our busiest code in the fast internal memory, silent tails of the original machines stopped sooner under heavy load)",
      fr: "Model-TG avec les moteurs du Syntakt : un peu plus léger pour le processeur (notre code le plus appelé en mémoire interne rapide, fins de notes inaudibles des machines d'origine arrêtées plus tôt sous forte charge)" },
  ] },
  { version: "1.6", date: "2026-10-01", changes: [
    { en: "Model-TG together with the Syntakt engines: the Sampler stays the 7th machine, the engines follow it (checked in the emulator)",
      fr: "Model-TG avec les moteurs du Syntakt : le Sampler reste la 7e machine, les moteurs le suivent (vérifié en émulation)" },
  ] },
  { version: "1.5", date: "2026-10-01", changes: [
    { en: "Model-TG by TinyGregAudio: a Sampler machine, resampling, retrig and master FX (on its own for now)",
      fr: "Model-TG de TinyGregAudio : machine Sampler, rééchantillonnage, retrig et effets master (seul pour l'instant)" },
  ] },
  { version: "1.4", date: "2026-10-01", changes: [
    { en: "Fewer cut notes when Syntakt voices play together: only sustained load or a really long block cuts a voice",
      fr: "Moins de notes coupées quand les voix du Syntakt jouent ensemble : seule une charge soutenue ou un bloc vraiment trop long coupe une voix" },
  ] },
  { version: "1.3", date: "2026-10-01", changes: [
    { en: "Syntakt voices keep their state in the fast internal memory too",
      fr: "Les voix du Syntakt gardent aussi leur état en mémoire interne rapide" },
  ] },
  { version: "1.2", date: "2026-10-01", changes: [
    { en: "Syntakt engines even lighter: their code now runs from the fast internal memory",
      fr: "Moteurs du Syntakt encore plus légers : leur code s'exécute en mémoire interne rapide" },
  ] },
  { version: "1.1", date: "2026-10-01", changes: [
    { en: "Syntakt engines lighter on the CPU: their work buffers now use the fast internal memory",
      fr: "Moteurs du Syntakt plus légers pour le processeur : leurs tampons de calcul passent en mémoire interne rapide" },
  ] },
  { version: "1.0", date: "2026-10-01", changes: [] },
];
