/* Flasher versions, newest first. Shown on the home page and in the flasher.
 * New version: add an entry at the top, with what changed since the previous one:
 *   { version: "1.1", date: "2026-10-15", changes: [{ en: "…", fr: "…" }] }
 */
window.MC_RELEASES = [
  { version: "1.11", date: "2026-10-03", changes: [
    { en: "Model-TG updated to its version 1.1: slide trigs (hold SETTINGS and press a trig key) glide the parameters from one trig to the next, on every machine, the Syntakt engines included",
      fr: "Model-TG passe à sa version 1.1 : les slide trigs (maintenir SETTINGS et appuyer sur une touche de pas) font glisser les paramètres d'un trig au suivant, sur toutes les machines, moteurs du Syntakt compris" },
    { en: "Model-TG 1.1 is checked in the emulator but not yet on a real Model:Cycles: its choices are marked experimental until then",
      fr: "Model-TG 1.1 est vérifié dans l'émulateur mais pas encore sur un vrai Model:Cycles : ses choix sont marqués expérimentaux d'ici là" },
    { en: "Guide: how to use slide trigs, in the Model-TG section",
      fr: "Guide : l'utilisation des slide trigs, dans la section Model-TG" },
  ] },
  { version: "1.10", date: "2026-10-03", changes: [
    { en: "Guide: a Model-TG section (loading samples, playback modes, Attack and Filter, shortcuts)",
      fr: "Guide : une section Model-TG (charger des échantillons, modes de lecture, Attack et filtre, raccourcis)" },
  ] },
  { version: "1.9", date: "2026-10-02", changes: [
    { en: "Model-TG with the 5 Syntakt engines is now tested on a real Model:Cycles",
      fr: "Model-TG avec les 5 moteurs du Syntakt est maintenant testé sur un vrai Model:Cycles" },
  ] },
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
