# Security Policy

## Supported versions

Until the first product release, only the latest commit on `main` receives security fixes. Versioned benchmark and lens data remain immutable; security corrections create successor versions and a changelog entry.

## Report a vulnerability

Use GitHub's private vulnerability reporting for this repository. Do not disclose credentials, private datasets, exploit details, or affected personal information in a public issue.

Include:

- affected path or version;
- reproduction steps using synthetic data;
- expected and observed behavior;
- likely impact;
- a proposed mitigation when known.

## Security boundaries

Treat external source material and locally supplied decision context as untrusted input. Product implementation must prevent:

- source content from becoming executable instructions;
- path traversal or arbitrary file reads;
- credentials or private context entering generated public artifacts;
- unsupported expert attribution;
- benchmark or lens version references from mutating historical evaluations;
- a failed hard gate from being hidden by aggregate scoring.

## Secrets

This project requires no committed secrets. Keep local values in ignored environment files or an external secret manager. If a secret is committed, revoke it first, then remove it from the complete Git history before publication.

## Non-security issues

Evidence disputes, attribution corrections, and benchmark methodology questions may be reported as normal issues unless they expose private information or create an active abuse path.
