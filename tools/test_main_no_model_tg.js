'use strict';
const assert = require('node:assert/strict');
const {assertNoModelTG, install} = require('../docs/flasher/main-policy.js');
for (const id of ['model-tg','model-tg-st','syntakt-tg-sd','macro-tg','retrosyn-tg']) {
  assert.throws(() => assertNoModelTG([{id}]), /Model-TG/);
  assert.throws(() => assertNoModelTG([{id:'other',requires:[id]}]), /Model-TG/);
}
assertNoModelTG([{id:'sample-wizard'},{id:'tiny-machines-255'},{id:'retrosyn-all-machines'}]);
let calls = 0;
const win = {MC_TWEAKS:{features:[{id:'tiny'},{id:'model-tg'}]},MCBuilder:{build(){calls++;return 42;}},MCMainClearResolve:x=>x};
install(win);
assert.deepEqual(win.MC_TWEAKS.features.map(f=>f.id),['tiny']);
assert.throws(()=>win.MCBuilder.build(null,null,[{id:'model-tg-st'}]),/Model-TG/);
assert.equal(calls,0);
assert.equal(win.MCBuilder.build(null,null,[{id:'sample-wizard'}]),42);
assert.throws(()=>win.MC_TWEAKS.features=[{id:'model-tg'}],/forbidden/);
assert.throws(()=>win.MC_TWEAKS.features.push({id:'model-tg'}),/forbidden/);
assert.throws(()=>win.MCMainClearResolve([{id:'model-tg'}]),/Model-TG/);
assert.throws(()=>{win.MCBuilder.build=()=>{};},TypeError);
console.log('ok main flasher rejects Model-TG and dependencies; independent Wizard and TINY allowed');
