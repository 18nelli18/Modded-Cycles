/* Boite commune : assigner chaque nouveau rapport au proprietaire pour les notifications.
 * Le texte du rapport reste une donnee, jamais du code ou une commande shell. */
'use strict';
module.exports = async function route({github, context}) {
  const issue = context.payload.issue;
  if (!issue || issue.pull_request) return;
  const target = {...context.repo, issue_number: issue.number};
  const owner = 'AveyCole';
  if (!(issue.assignees || []).some(person => person.login.toLowerCase() === owner.toLowerCase())) {
    await github.rest.issues.addAssignees({...target, assignees: [owner]});
  }
  if (!issue.title.startsWith('[Bug]')) return;
  try {
    await github.rest.issues.getLabel({...context.repo, name: 'bug'});
  } catch (error) {
    if (error.status !== 404) throw error;
    try {
      await github.rest.issues.createLabel({...context.repo, name: 'bug', color: 'd73a4a', description: 'Supermodel bug report'});
    } catch (creationError) {
      if (creationError.status !== 422) throw creationError;
    }
  }
  await github.rest.issues.addLabels({...target, labels: ['bug']});
};
