# Additional Options to Consider

- **Storage**: Wasabi/B2 (S3-compatible), immutable buckets for audit artifacts.
- **Network**: WireGuard site-to-site, Cloudflare Tunnels (no inbound ports).
- **KMS**: HashiCorp Vault or cloud KMS; per-tenant envelope encryption, quarterly key rotation.
- **Threat Mitigations**: File allowlist; mezzanine transcode; containers with seccomp/AppArmor; ulimits; no outbound internet.
- **Compliance (future)**: SOC 2 prep; DPA templates.
- **Authenticity**: C2PA-style provenance, clip watermarking, QR links tied to hashes.
- **Identity/Auth**: Self-host JWT now; OIDC (Auth0/Clerk/Keycloak) for SaaS; per-matter RBAC.
- **Client-only mode**: Encrypted bundle export/import; no server storage.
