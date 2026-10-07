# Security

## Reporting

Report security issues privately to the repository owner (Ken Huang / DistributedApps.ai). Do not open a public issue for exploitable lab defects until a fix is available.

## Scope of this lab

`grsi-lab` is an educational companion. Sandbox, ledger, and promotion controls are **contract stubs** for Packt chapters — not a hardened multi-tenant runtime. Treat them as teaching models:

- Path and jail checks demonstrate ownership / isolation rules.
- Promotion tokens and sealed ledgers demonstrate governance gates.
- No real GPU training, cloud credentials, or production agent traffic is required for tests.

## Maintainer scripts

Google Docs publish scripts under `scripts/` require local `gws` auth via environment variables (see `.env.example`). Never commit `.env` or personal CLI profile paths.
