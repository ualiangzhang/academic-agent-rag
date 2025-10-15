# Configuration Change Control and Audit

## Principles
- All configuration changes are reviewed and traceable.
- Secrets are never included in change descriptions.

## Process
1. Open a PR describing the configuration change, scope, and risk.
2. Link to related tickets and update `docs/CONFIGURATION.md` if behavior changes.
3. Include rollout plan and rollback plan.
4. Obtain approvals per code owners.
5. Merge with CI green and deploy using staged rollout.

## Audit
- Record: author, date, environment, variables changed, PR link, rollout/rollback outcome.
- Store audit entries in the repo (e.g., release notes) and in the deployment system.

## Emergency Changes
- Allowed only for incident mitigation; follow up with a retro PR updating docs and audit.
