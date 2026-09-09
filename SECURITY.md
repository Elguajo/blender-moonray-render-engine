# Security Policy

## Supported versions

This project is pre-release. Security fixes are applied to the current development branch only until the first stable release policy is defined.

## Reporting a vulnerability

**Do not open a public Issue for a security vulnerability.**

Preferred reporting path:

1. Use GitHub's **Security → Report a vulnerability** flow if private vulnerability reporting is enabled for the repository.
2. If that option is unavailable, contact the repository maintainers privately through an available maintainer contact channel without posting exploit details publicly.

Include:

- affected commit/version;
- impact;
- reproduction steps or proof of concept;
- whether the issue affects build scripts, dependency acquisition, local execution, file handling, or another trust boundary.

## Scope notes

The project executes third-party build tools and render software and may interact with Windows/WSL filesystems. Reports involving malicious dependency substitution, unsafe download verification, path injection, archive extraction, privilege escalation, or unintended host filesystem modification are especially relevant.
