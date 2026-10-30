/* Verifier le routage des rapports sans publier de messages ni de tickets. */
const test = require('node:test');
const assert = require('node:assert/strict');
const route = require('./bug-reports.cjs');

function fixture(issue, missingLabel = false) {
  const calls = [];
  const issues = Object.fromEntries(['addAssignees', 'getLabel', 'createLabel', 'addLabels'].map(method => [method, async args => {
    calls.push([method, args]);
    if (method === 'getLabel' && missingLabel) throw Object.assign(new Error('missing'), {status: 404});
  }]));
  return {calls, github: {rest: {issues}}, context: {repo: {owner: 'AveyCole', repo: 'Supermodel'}, payload: {issue}}};
}
test('new report gets an owner notification and bug label', async () => {
  const f = fixture({number: 12, title: '[Bug] silent track', assignees: []});
  await route(f);
  assert.deepEqual(f.calls.map(x => x[0]), ['addAssignees', 'getLabel', 'addLabels']);
  assert.deepEqual(f.calls[0][1], {owner: 'AveyCole', repo: 'Supermodel', issue_number: 12, assignees: ['AveyCole']});
});
test('form assignment is preserved without duplicate assignment', async () => {
  const f = fixture({number: 13, title: '[Bug] sample window', assignees: [{login: 'aveycole'}]});
  await route(f);
  assert(!f.calls.some(x => x[0] === 'addAssignees'));
});
test('missing default label is created, including concurrent creation', async () => {
  const f = fixture({number: 14, title: '[Bug] test'}, true);
  f.github.rest.issues.createLabel = async () => {throw Object.assign(new Error('already created'), {status: 422});};
  await route(f);
  assert.equal(f.calls.at(-1)[0], 'addLabels');
});
test('API errors fail visibly instead of silently losing notification', async () => {
  const f = fixture({number: 15, title: '[Bug] test'});
  f.github.rest.issues.addAssignees = async () => {throw Object.assign(new Error('forbidden'), {status: 403});};
  await assert.rejects(route(f), /forbidden/);
});
test('pull requests are ignored and plain issues still notify the owner', async () => {
  const pr = fixture({number: 16, title: '[Bug] patch', pull_request: {}});
  await route(pr);assert.equal(pr.calls.length, 0);
  const issue = fixture({number: 17, title: 'Unexpected sound'});
  await route(issue);assert.deepEqual(issue.calls.map(x => x[0]), ['addAssignees']);
});
