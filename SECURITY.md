# Security

## Reporting

Report security issues privately to the repository owner (Ken Huang / DistributedApps.ai). Do not open a public issue for exploitable lab defects until a fix is available.

## Scope of this lab

`grsi-lab` is an educational companion. Sandbox, ledger, promotion, and ecosystem controls are **fully implemented teaching gates** for Packt chapters. They are not a hardened multi-tenant production runtime. Residual risk is expected and documented:

- Path and jail checks demonstrate ownership / isolation rules on a local filesystem.
- Promotion tokens (HMAC) and sealed ledgers demonstrate governance gates with real crypto and hash chains.
- Boundary proxy defaults to allowlist-only checks without outbound network (`enable_network=False`).
- No real GPU training, cloud credentials, or production agent traffic is required for tests.

Do not deploy these packages as a shared SaaS control plane without additional hardening (multi-tenant isolation, key management, distributed kill ack, audit retention).

## Maintainer scripts

Google Docs publish scripts under `scripts/` require local `gws` auth via environment variables (see `.env.example`). Never commit `.env` or personal CLI profile paths.
