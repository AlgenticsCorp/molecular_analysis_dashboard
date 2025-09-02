# Security Policy

## Supported Versions
We follow semantic versioning. Only the latest minor/patch versions will receive security updates.

## Reporting a Vulnerability
Please email `security@yourdomain.tld` with details. We will acknowledge receipt within 72 hours and strive to provide a remediation timeline.

For sensitive reports, please encrypt using our public key (if available) or request a secure channel in your email.

## Disclosure Policy
- We aim to fix confirmed issues promptly
- We will coordinate a disclosure date with you
- We appreciate responsible disclosure and will credit reporters (if desired)

## Best Practices
This template includes Bandit, mypy, and pre-commit checks. Run:

```bash
pre-commit run --all-files
bandit -r src
```
