/* Main flasher policy: independent Sample Wizard only; Model-TG stays retired. */
(function (root) {
  'use strict';
  const isModelTG = id => typeof id === 'string' && (id === 'model-tg' || id.startsWith('model-tg-') || /(?:^|-)tg(?:-|$)/.test(id));
  function assertNoModelTG(recipes) {
    for (const recipe of recipes || []) {
      if (isModelTG(recipe.id) || (recipe.requires || []).some(isModelTG)) {
        throw new Error('Model-TG is retired from the main flasher. Use independent Sample Wizard. / Model-TG est retire du flasheur principal. Utilisez Sample Wizard independant.');
      }
    }
  }
  function install(win) {
    const data = win.MC_TWEAKS;
    // Reject future feature registration as well as a stale selection.
    const checkFeature = f => !isModelTG(f.id) && !isModelTG(f.requires);
    const protect = values => new Proxy(values, {set(target, key, value) {
      if (key !== 'length' && value && !checkFeature(value)) throw new Error('Model-TG feature is forbidden in main');
      return Reflect.set(target, key, value);
    }});
    let features = protect(data.features.filter(checkFeature));
    Object.defineProperty(data, 'features', {
      configurable: false,
      get: () => features,
      set: value => { if (value.some(f => !checkFeature(f))) throw new Error('Model-TG feature is forbidden in main'); features = protect(value); }
    });
    const builder = win.MCBuilder, original = builder.build;
    Object.defineProperty(builder, 'build', { configurable: false, writable: false,
      value: function(raw, device, recipes, options) { assertNoModelTG(recipes); return original.call(this, raw, device, recipes, options); }
    });
    const resolve = win.MCMainClearResolve;
    win.MCMainClearResolve = function(out) { const recipes = resolve ? resolve(out) : out; assertNoModelTG(recipes); return recipes; };
    win.MCFlasherApp?.applyLang(win.document.documentElement.lang || 'en');
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {isModelTG, assertNoModelTG, install};
  if (root?.MCBuilder && root?.MC_TWEAKS) install(root);
})(typeof window !== 'undefined' ? window : null);
