# Deployment & Scaling (GPU & Hybrid)

## Reference architecture
Frontend on Vercel (or self-host) → API (FastAPI) → Queue (Redis/Celery) → **GPU Worker Pool** → S3/MinIO storage. Postgres for metadata and transcripts (opt-in only).

**Data path:** Browser uploads via pre-signed URL → API enqueues job (+ SHA-256) → workers process → results written to storage → UI notified.

## GPU options
- **Self-host GPU**: Control & predictable cost; needs maintenance. Spec: NVIDIA 4090/6000 Ada, 24–48GB VRAM, NVMe, 128GB+ RAM.
- **Managed GPU cloud**: Elastic; watch OPEX/egress. Providers: AWS g5/g6/g6e, GCP A2/L4, Azure NC, Lambda Labs/CoreWeave/RunPod/Paperspace.
- **Hybrid (recommended)**: Vercel UI + your API + cloud/on-prem GPU workers connected via **mTLS/WireGuard/Cloudflare Tunnels**.

## Security
mTLS service-to-service; workers in **no-egress** subnets; SSE-KMS (or MinIO SSE+KMS); hash (SHA-256) originals/exports and include in audit.

## Performance knobs
faster-whisper **large-v3** on GPU (batching), WhisperX alignment, pyannote diarization with cached embeddings, audio downmix to 16k mono + loudness normalize.

## Cost control
Autoscale on queue depth/ETA; split CPU preprocess from GPU ASR; lifecycle policies for short TTL.
