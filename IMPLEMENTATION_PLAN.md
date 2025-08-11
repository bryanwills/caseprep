# CasePrep Implementation Plan - Comprehensive Technical Specifications

> **Detailed technical blueprint for building a privacy-first legal transcription SaaS platform**

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [API Design](#api-design)
4. [Processing Pipeline](#processing-pipeline)
5. [Security & Privacy](#security--privacy)
6. [Frontend Implementation](#frontend-implementation)
7. [Infrastructure Setup](#infrastructure-setup)
8. [Testing Strategy](#testing-strategy)
9. [Deployment & Scaling](#deployment--scaling)
10. [24-Step Implementation Guide](#24-step-implementation-guide)

---

## Architecture Overview

### Core System Design
```
Browser (Next.js)
  ├─ Local mode (default for demos)
  │   ├─ File API for local media
  │   ├─ IndexedDB (opt-in, encrypted)
  │   └─ Client-only export of results
  └─ Server mode (self-hosted)
      ├─ FastAPI gateway (CPU)
      ├─ Redis queue (Celery)
      ├─ Worker pool (ffmpeg → ASR → align → diarize → postprocess → export)
      ├─ MinIO (S3 API) for objects (opt-in)
      └─ Postgres for metadata/transcripts (opt-in)
```

### Technology Stack
- **Frontend**: Next.js 14+, TypeScript, Tailwind CSS, React Query
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **Queue**: Redis + Celery for async processing
- **Storage**: MinIO (S3-compatible), Postgres 16+
- **AI/ML**: faster-whisper, WhisperX, pyannote.audio
- **Media**: FFmpeg for processing and clipping
- **Security**: XChaCha20-Poly1305, HashiCorp Vault, JWT

---

## Database Schema

### Core Tables
```sql
-- Tenants & Users
CREATE TABLE tenant (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  kms_wrap_key_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE app_user (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenant(id) ON DELETE CASCADE,
  email CITEXT UNIQUE NOT NULL,
  display_name TEXT,
  role TEXT DEFAULT 'member',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Projects / Matters
CREATE TABLE matter (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenant(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  retention_days INT DEFAULT 0,
  store_media BOOLEAN DEFAULT FALSE,
  store_transcripts BOOLEAN DEFAULT FALSE,
  allow_anon_learning BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Media and Hashes
CREATE TABLE media_asset (
  id UUID PRIMARY KEY,
  matter_id UUID REFERENCES matter(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  mime_type TEXT,
  byte_length BIGINT,
  sha256 TEXT NOT NULL,
  storage_uri TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Transcript root
CREATE TABLE transcript (
  id UUID PRIMARY KEY,
  matter_id UUID REFERENCES matter(id) ON DELETE CASCADE,
  media_id UUID REFERENCES media_asset(id) ON DELETE SET NULL,
  language TEXT DEFAULT 'en',
  diarization_model TEXT,
  asr_model TEXT,
  total_duration_seconds NUMERIC,
  version INT DEFAULT 1,
  encrypted BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Segments (word-aligned optional)
CREATE TABLE transcript_segment (
  id UUID PRIMARY KEY,
  transcript_id UUID REFERENCES transcript(id) ON DELETE CASCADE,
  speaker_label TEXT,
  start_ms INT NOT NULL,
  end_ms INT NOT NULL,
  text TEXT NOT NULL,
  confidence NUMERIC,
  words JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Edits (diff log)
CREATE TABLE transcript_edit (
  id UUID PRIMARY KEY,
  transcript_id UUID REFERENCES transcript(id) ON DELETE CASCADE,
  user_id UUID REFERENCES app_user(id) ON DELETE SET NULL,
  segment_id UUID REFERENCES transcript_segment(id) ON DELETE SET NULL,
  before_text TEXT,
  after_text TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- User dictionaries & rules
CREATE TABLE user_dictionary (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES app_user(id) ON DELETE CASCADE,
  pattern TEXT NOT NULL,
  replacement TEXT NOT NULL,
  scope TEXT DEFAULT 'word',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE speaker_alias (
  id UUID PRIMARY KEY,
  transcript_id UUID REFERENCES transcript(id) ON DELETE CASCADE,
  placeholder TEXT NOT NULL,
  alias TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Immutable event log for chain of custody
CREATE TABLE audit_event (
  id UUID PRIMARY KEY,
  transcript_id UUID REFERENCES transcript(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  event_payload JSONB NOT NULL,
  event_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  prev_hash TEXT,
  curr_hash TEXT NOT NULL
);
```

---

## API Design

### REST Endpoints (FastAPI)
```python
# Core API endpoints
POST   /v1/matters                         # create matter/workspace
POST   /v1/media/upload-url                # pre-signed URL (S3/MinIO)
POST   /v1/transcripts                     # start job (body: mediaId | multipart)
GET    /v1/transcripts/{id}                # transcript JSON
GET    /v1/transcripts/{id}/export.srt     # SRT
GET    /v1/transcripts/{id}/export.pdf     # PDF / Quote Pack
POST   /v1/transcripts/{id}/clips          # clip from time range/segment
POST   /v1/transcripts/{id}/dictionary     # upsert user rules
POST   /v1/transcripts/{id}/speaker-map    # rename placeholders
GET    /v1/transcripts/{id}/audit          # audit JSON
DELETE /v1/transcripts/{id}                # delete transcript/media (if stored)
```

### Transcript JSON Schema
```json
{
  "transcriptId": "uuid",
  "media": {"id": "uuid", "filename": "court_video.wmv", "sha256": "..."},
  "language": "en",
  "diarizationModel": "pyannote-...",
  "asrModel": "faster-whisper-large-v3",
  "durationMs": 1265323,
  "segments": [
    {
      "id": "uuid",
      "speaker": "Female 1",
      "startMs": 30000,
      "endMs": 55000,
      "text": "All right, there are two cases on today...",
      "confidence": 0.92,
      "words": [
        {"w": "All", "startMs": 30020, "endMs": 30070, "conf": 0.95},
        {"w": "right,", "startMs": 30070, "endMs": 30120, "conf": 0.93}
      ]
    }
  ],
  "speakerMap": {"Female 1": "", "Male 1": ""},
  "createdAt": "2025-08-11T20:00:00Z"
}
```

---

## Processing Pipeline

### Celery Task Chain
```python
# Core processing tasks
@celery.task
def normalize_audio(media_key: str) -> str:
    # ffmpeg to wav mono 16k, return path/key

@celery.task
def asr_transcribe(wav_key: str) -> dict:
    # faster-whisper large-v3

@celery.task
def align_with_whisperx(result: dict) -> dict:
    # WhisperX for word-level timestamps

@celery.task
def diarize(aligned: dict) -> dict:
    # pyannote to assign speakers

@celery.task
def postprocess_apply_dictionaries(transcript_id: str) -> str:
    # Apply user corrections and learning rules

@celery.task
def export_clip(transcript_id: str, start_ms: int, end_ms: int) -> str:
    # FFmpeg clip generation
```

### FFmpeg Commands
```bash
# Audio normalization
ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 -filter:a loudnorm output.wav

# Stream-copy clipping (fast)
ffmpeg -ss 00:23:35 -i input.mp4 -to 00:23:59 -c copy -movflags +faststart clip.mp4

# Re-encode fallback
ffmpeg -ss 00:23:35 -i input.mp4 -to 00:23:59 \
  -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 128k clip.mp4
```

---

## Security & Privacy

### Encryption Architecture
- **Default**: No server-side storage. Client-side optional encrypted cache (IndexedDB)
- **Transport**: HTTPS + HSTS; mTLS for service-to-service
- **At Rest**: AES-256 (LUKS or SSE-KMS). App-layer encryption for transcripts (XChaCha20-Poly1305), per-tenant envelope keys
- **Chain of Custody**: SHA-256 on ingest + outputs, append-only hash-chained audit log, exportable Audit Summary
- **Retention**: 0 (ephemeral) / 7 / 30 / 90 days, per-matter. Granular opt-ins for media/transcripts/global learning
- **Sandboxing**: Workers containerized; no-egress; strict ffmpeg args; content-type checks; transcode to safe mezzanine

### Key Management
```python
# Example encryption implementation
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import os

def encrypt_transcript(transcript_data: str, tenant_key: bytes) -> bytes:
    cipher = ChaCha20Poly1305(tenant_key)
    nonce = os.urandom(12)
    ciphertext = cipher.encrypt(nonce, transcript_data.encode(), None)
    return nonce + ciphertext

def decrypt_transcript(encrypted_data: bytes, tenant_key: bytes) -> str:
    cipher = ChaCha20Poly1305(tenant_key)
    nonce, ciphertext = encrypted_data[:12], encrypted_data[12:]
    plaintext = cipher.decrypt(nonce, ciphertext, None)
    return plaintext.decode()
```

---

## Frontend Implementation

### Next.js App Structure
```
apps/web/
├── components/
│   ├── ui/                 # Reusable UI components
│   ├── transcript/         # Transcript editor components
│   ├── media/             # Video/audio player
│   └── export/            # Export dialogs
├── pages/
│   ├── api/               # API routes (if needed)
│   ├── matters/           # Case management
│   ├── transcripts/       # Transcript pages
│   └── settings/          # User preferences
├── lib/
│   ├── api.ts            # API client
│   ├── encryption.ts     # Client-side crypto
│   └── storage.ts        # IndexedDB wrapper
└── hooks/                # React hooks
```

### Key UI Features
- **Two-pane Layout**: Video right, transcript left; sticky controls
- **Color Coding**: Speaker bands; mono font for timestamps
- **Keyboard Navigation**: ←/→ by segment; seek on click
- **Segment Menu**: Copy quote, Make clip (±N), Highlight, Add tag
- **Export Options**: SRT/VTT, DOCX, PDF (Quote Pack), CSV, JSON
- **Settings Panel**: Retention, storage toggles, dictionaries

---

## Infrastructure Setup

### Docker Compose (Development)
```yaml
version: "3.9"
services:
  api:
    build: ./services/api
    environment:
      - DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/app
      - REDIS_URL=redis://redis:6379/0
      - S3_ENDPOINT=http://minio:9000
      - S3_BUCKET=caseprep
    ports: ["8080:8080"]
    depends_on: [db, redis, minio]
    
  worker:
    build: ./services/worker
    environment:
      - REDIS_URL=redis://redis:6379/0
      - S3_ENDPOINT=http://minio:9000
      - S3_BUCKET=caseprep
    depends_on: [redis, minio]
    
  db:
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=postgres
    ports: ["5432:5432"]
    
  redis:
    image: redis:7
    ports: ["6379:6379"]
    
  minio:
    image: minio/minio:latest
    environment:
      - MINIO_ROOT_USER=minio
      - MINIO_ROOT_PASSWORD=minio123
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
```

### Environment Configuration
```bash
APP_ENV=dev
SECRET_KEY=...                          # JWT / cookies
DATABASE_URL=postgresql+psycopg2://...
REDIS_URL=redis://...
STORAGE_BACKEND=null|local|s3
S3_ENDPOINT=http://minio:9000
S3_BUCKET=caseprep
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123
KMS_PROVIDER=vault|local
KMS_KEY_ID=...
MAX_UPLOAD_GB=5
RETENTION_DAYS_DEFAULT=0
```

---

## Testing Strategy

### Unit Tests
- Dictionary rules and replacement logic
- Speaker alias propagation through transcript
- Export formatters (SRT, DOCX, PDF generation)
- Encryption/decryption functions
- Hash chain validation

### Integration Tests
- End-to-end pipeline on sample media files (1-3 minutes)
- Golden JSON comparison for consistent results
- Upload → process → export workflow
- Permission and access control validation

### Security Tests
- File upload validators and type checking
- Permission boundary enforcement
- Storage toggle behavior verification
- Audit log integrity and immutability

### Performance Tests
- CPU vs GPU processing time comparison
- Memory usage during long transcriptions
- Queue performance under load
- Export generation speed benchmarks

---

## Deployment & Scaling

### GPU Acceleration Options

#### Self-hosted GPU Setup
```dockerfile
# GPU Worker Dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04
WORKDIR /app
RUN apt-get update && apt-get install -y python3-pip ffmpeg
COPY requirements.txt .
RUN pip install -r requirements.txt
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,video
CMD ["celery", "-A", "celery_app.celery", "worker", "-Q", "gpu"]
```

#### Cloud GPU Options
- **AWS**: g5/g6/g6e instances with NVIDIA A10G/L4
- **GCP**: A2/T4/L4 instances with Compute Engine
- **Azure**: NC series with NVIDIA V100/T4
- **Specialized**: Lambda Labs, CoreWeave, RunPod, Paperspace

#### Hybrid Architecture
- Frontend on Vercel/Netlify
- API on self-hosted/cloud infrastructure
- GPU workers on dedicated GPU cloud
- Secure connectivity via mTLS/WireGuard

### Production Scaling Considerations
- Autoscaling based on Redis queue depth
- Separate CPU preprocessing from GPU ASR
- Object storage lifecycle policies (24h-7d TTL)
- Monitoring with structured logging and metrics
- Cost optimization through spot instances

---

## 24-Step Implementation Guide

### Phase 1: Foundation (Steps 1-6)
1. **Repo Bootstrap**: Set up monorepo structure (apps/web, services/api, services/worker, infra)
2. **Environment Setup**: Python 3.11+, uv, Node 20+, Docker with BuildKit
3. **Frontend Scaffold**: Next.js + TypeScript + Tailwind, two-pane layout, auth stub
4. **API Scaffold**: FastAPI with health, upload, transcription, export endpoints
5. **Queue System**: Celery + Redis; define task chain structure
6. **Storage Setup**: MinIO S3-compatible storage with pre-signed URLs, SSE enabled

### Phase 2: Core Processing (Steps 7-12)
7. **Database Schema**: Postgres + SQLAlchemy/Alembic; implement all core tables
8. **Security Baseline**: HTTPS, HSTS, JWT auth, role-based access, CSRF protection
9. **Audio Pipeline**: FFmpeg normalization to mono 16kHz with loudness control
10. **ASR Engine**: faster-whisper large-v3 integration (CPU initially)
11. **Alignment**: WhisperX integration for precise word timestamps
12. **Diarization**: pyannote.audio speaker identification with placeholder mapping

### Phase 3: Advanced Features (Steps 13-18)
13. **Post-processing**: User dictionary application and regex rule engine
14. **Transcript Editor**: Inline editing, speaker renaming, find/replace, media sync
15. **Export System**: SRT/VTT, DOCX, PDF Quote Pack, CSV with SHA-256 + audit
16. **Media Clipping**: FFmpeg stream-copy with re-encode fallback
17. **Chain of Custody**: SHA-256 hashing on ingest/export with hash-chained audit log
18. **Privacy Controls**: Retention policies, per-matter storage toggles

### Phase 4: Production Ready (Steps 19-24)
19. **Learning System**: Edit-based rule generation; global learning (opt-in only)
20. **Test Suite**: Unit tests, golden-file integration tests, performance benchmarks
21. **Observability**: Structured logging, metrics (processing time, accuracy proxy), request tracing
22. **Docker Environment**: Complete compose setup with TLS, network isolation
23. **GPU Infrastructure**: Worker scaling plan, CUDA Dockerfile, autoscaling triggers
24. **Documentation**: API docs (OpenAPI), security overview, admin procedures, compliance guides

---

## Monitoring & Observability

### Key Metrics
- **Processing**: ASR minutes/second, queue depth, job success/failure rates
- **Quality**: WER proxy via edit frequency, confidence score distributions
- **Business**: Active users, processing hours consumed, export counts
- **Infrastructure**: CPU/GPU utilization, memory usage, storage consumption

### Logging Structure
```json
{
  "timestamp": "2025-08-11T20:00:00Z",
  "level": "INFO",
  "request_id": "req_abc123",
  "job_id": "job_def456",
  "component": "asr_worker",
  "event": "transcription_complete",
  "duration_ms": 45000,
  "audio_duration_s": 300,
  "model": "faster-whisper-large-v3",
  "gpu_used": true
}
```

---

## Learning From Edits Design

### Per-user Adaptive Rules
- Store corrections as structured rules: exact match, word boundary, regex patterns
- Apply in order: speaker aliases → user exact/word → user regex → global rules
- Conflict resolution: user rules always override global suggestions
- Version control: track rule evolution and effectiveness

### Global Learning System (Opt-in)
- Aggregate anonymous, high-frequency corrections across users
- Score rules by frequency and success rate
- Transparency UI: show which rules applied and allow one-click revert
- Future enhancement: domain-specific re-ranking model for legal terminology

### Implementation Example
```python
def apply_correction_rules(text: str, user_rules: List[Rule], global_rules: List[Rule]) -> str:
    # Apply speaker aliases first
    for speaker_rule in get_speaker_aliases():
        text = speaker_rule.apply(text)
    
    # Apply user rules (exact match, then word boundary, then regex)
    for rule in sorted(user_rules, key=lambda r: r.priority):
        text = rule.apply(text)
    
    # Apply global rules only if user hasn't overridden
    for rule in global_rules:
        if not rule.conflicts_with_user_rules(user_rules):
            text = rule.apply(text)
    
    return text
```

---

*This implementation plan serves as the comprehensive technical specification for building CasePrep. Each section can be expanded during development as new requirements and optimizations are discovered.*