# Decisions & Guidance (Resolved)

## Dev storage backend
Use **MinIO (S3-compatible)** for dev and prod parity. Keep **LocalFS** only for quick demos.

## Processing mode (now vs later)
**Now:** Web-local processing only (privacy-first).  
**Later (Prod):** Add **GPU worker backend** for long/large jobs.

## Global corrections
**OFF by default.** Opt-in per workspace. When enabled, anonymize data and show a transparent “what changed & why.” User rules always override global rules.
