# Security Overview (MVP)

- **Default**: No server-side storage. Client-side optional encrypted cache (IndexedDB).
- **Transport**: HTTPS + HSTS; mTLS for service-to-service.
- **At Rest**: AES-256 (LUKS or SSE-KMS). App-layer encryption for transcripts (XChaCha20-Poly1305), per-tenant envelope keys.
- **Chain of Custody**: SHA-256 on ingest + outputs, append-only hash-chained audit log, exportable Audit Summary.
- **Retention**: 0 (ephemeral) / 7 / 30 / 90 days, per-matter. Granular opt-ins for media/transcripts/global learning.
- **Sandboxing**: Workers containerized; no-egress; strict ffmpeg args; content-type checks; transcode to safe mezzanine.
