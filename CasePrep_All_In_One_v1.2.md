# Case‑Prep Transcription App — Comprehensive Blueprint (v1.2)

> **Scope**: English-only, case‑prep tool (non‑certified). Self‑hosted in dev. **Accuracy over speed**. Default **no data stored** unless the user opts in. Strong privacy + encryption. Future: optional certification via reporter partners (>6 months).

---

## 0) Quick Start — 24‑Step Implementation Plan (MVP → Prod)

1. **Repo bootstrap**: monorepo (apps/web, services/api, services/worker, infra). Add `/docs` with this file.  
2. **Env**: Python 3.11+, `uv`, Node 20+, Docker (with BuildKit).  
3. **Frontend scaffold** (Next.js + TS + Tailwind): two‑pane player+transcript; light/dark; basic auth stub.  
4. **API scaffold** (FastAPI): health, upload, start transcription, get transcript, export endpoints.  
5. **Queue**: Celery + Redis; define tasks: normalize → ASR → align → diarize → postprocess → export.  
6. **Storage**: MinIO (S3‑compatible) for dev; pre‑signed URLs; SSE enabled.  
7. **DB**: Postgres + SQLAlchemy/Alembic; create core tables (matter, media, transcript, segments, edits, dictionaries, audit).  
8. **Security baseline**: HTTPS, HSTS, JWT auth (dev), role model (owner/editor/viewer), CSRF for forms.  
9. **Audio pipeline**: ffmpeg downmix to mono 16 kHz; loudness normalize.  
10. **ASR engine**: faster‑whisper `large-v3` (CPU for dev, GPU later).  
11. **Alignment**: WhisperX for word timestamps.  
12. **Diarization**: pyannote; map to placeholders (Female 1, Male 1…).  
13. **Post‑processing**: apply user dictionary + regex rules; optional global rules (OFF by default).  
14. **Transcript editor**: inline edits, speaker rename, find/replace, seek‑on‑click.  
15. **Exports**: SRT/VTT, DOCX, PDF (Quote Pack), CSV; include SHA‑256 + audit summary.  
16. **Clipper**: ffmpeg stream‑copy for ±N seconds around selection; re‑encode fallback.  
17. **Chain of custody**: compute SHA‑256 on ingest and on every export; append to audit log with hash‑chain.  
18. **Privacy controls**: retention (0/7/30/90 days), per‑matter toggles (store media, store transcript, allow anon learning).  
19. **Learning from edits**: persist per‑user rules; apply on future jobs; global learning opt‑in only, with transparency.  
20. **Testing**: unit (rules), golden‑file integration (end‑to‑end on sample media), perf samples (10–60 min).  
21. **Observability**: structured logs, basic metrics (ASR mins/sec, queue depth, WER proxy), request IDs.  
22. **Docker Compose (dev)**: FastAPI, Redis, Postgres, MinIO, worker; local TLS for API; no egress for workers.  
23. **GPU plan**: decide A/B/C (self‑host vs managed vs hybrid); prepare worker Dockerfile with NVIDIA runtime.  
24. **Docs**: publish API docs (OpenAPI), security overview, admin runbooks, purge/retention procedures.

---

## 1) Architecture Overview

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

**Why two modes?** Default privacy (no upload) + a scalable path for longer videos and higher accuracy.

---

## 2) Security & Privacy Model

- **Default no-storage**: server processes in a temp enclave and deletes on completion; returns artifacts to the browser only.  
- **In-transit**: HTTPS; service‑to‑service **mTLS**.  
- **At rest (opt‑in)**: SSE‑KMS (S3/MinIO) or LUKS; **application‑layer encryption** for transcripts (XChaCha20‑Poly1305) with per‑tenant envelope keys (KMS/Vault).  
- **Key mgmt**: HashiCorp Vault or cloud KMS; rotate wrapping keys quarterly.  
- **Chain of custody**: SHA‑256 on original and outputs; append‑only, hash‑chained **audit_event** table; export an audit summary.  
- **Retention**: 0/7/30/90 days per matter; granular toggles: store media? store transcript? allow anon learning?  
- **Sandboxing**: workers in containers with seccomp/AppArmor; no‑egress subnets; strict ffmpeg args; transcode to safe mezzanine for odd formats.

---

## 3) Data Storage Options

- **Browser-only**: IndexedDB via localforage; optional client‑side encryption (passphrase→scrypt/PBKDF2→XChaCha20‑Poly1305). Export/import encrypted bundles (.zip).  
- **MinIO (dev & prod parity)**: S3 API, SSE, versioning, lifecycle. Pre‑signed URLs for direct browser upload/download.  
- **Alternatives**: Wasabi/B2 (S3‑compatible), immutable buckets for audit artifacts (object lock/legal hold).  
  
**Decision**: Use **MinIO** by default in dev; keep LocalFS only for quick demos.

---

## 4) Database Schema (Postgres)

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

## 5) Transcript JSON (API)

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

## 6) REST API Design (FastAPI) — Sketch

**Auth**: self‑host dev via JWT (later OIDC).  
  
**Endpoints (subset)**
```
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

**OpenAPI stub (YAML)**
```yaml
openapi: 3.0.3
info: { title: CasePrep API, version: 0.1.0 }
paths:
  /v1/transcripts:
    post:
      summary: Start transcription job
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                mediaId: { type: string, format: uuid }
      responses: { '202': { description: Job enqueued } }
```

---

## 7) FastAPI Skeleton (selected files)

**services/api/main.py**
```python
from fastapi import FastAPI
from routers import transcripts, matters, media

app = FastAPI(title="CasePrep API")
app.include_router(matters.router, prefix="/v1/matters")
app.include_router(media.router, prefix="/v1/media")
app.include_router(transcripts.router, prefix="/v1/transcripts")

@app.get("/health")
def health():
    return {"ok": True}
```

**services/api/routers/transcripts.py**
```python
from fastapi import APIRouter, HTTPException
from schemas import TranscriptCreate
from tasks import enqueue_transcription

router = APIRouter()

@router.post("")
async def start_transcript(payload: TranscriptCreate):
    job_id = enqueue_transcription(payload.media_id)
    return {"jobId": job_id, "status": "queued"}
```

**services/api/schemas.py**
```python
from pydantic import BaseModel
from uuid import UUID

class TranscriptCreate(BaseModel):
    media_id: UUID
```

---

## 8) Celery Tasks (Python)

**services/worker/celery_app.py**
```python
from celery import Celery

celery = Celery(
    "caseprep",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)
```

**services/worker/tasks.py**
```python
from .celery_app import celery

@celery.task
def normalize_audio(media_key: str) -> str:
    # ffmpeg to wav mono 16k, return path/key
    ...

@celery.task
def asr_transcribe(wav_key: str) -> dict:
    # faster-whisper large-v3
    ...

@celery.task
def align_with_whisperx(result: dict) -> dict:
    ...

@celery.task
def diarize(aligned: dict) -> dict:
    # pyannote to assign speakers
    ...

@celery.task
def postprocess_apply_dictionaries(transcript_id: str) -> str:
    ...

@celery.task
def export_clip(transcript_id: str, start_ms: int, end_ms: int) -> str:
    ...
```

---

## 9) FFmpeg Clipper — Commands

```bash
# Stream-copy (fast, no re-encode) when GOP allows
ffmpeg -ss 00:23:35 -i input.mp4 -to 00:23:59 -c copy -movflags +faststart clip.mp4

# Fallback re-encode
ffmpeg -ss 00:23:35 -i input.mp4 -to 00:23:59 \
  -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 128k clip.mp4
```

---

## 10) Learning From Edits — Design

**Per‑user adaptive rules**
- Store corrections as rules: word/phrase/regex → replacement.  
- Apply order: speaker aliases → user exact/word → user regex → global anon rules.  
- Conflicts: user rules override global.

**Global learning (opt‑in, OFF by default)**
- Aggregate anonymous, high‑frequency edits into a scored rule table.  
- Show a transparency panel: which rules applied, where; one‑click revert.  
- Future: small re‑ranker for legal domain phrases.

**Speaker naming**
- Placeholder labels (“Female 1”) with inline rename to proper names; propagate through transcript and exports.

---

## 11) Frontend UX Spec (Next.js + Tailwind)

- Two‑pane: **video right, transcript left**; sticky controls (search, replace, export).  
- Color bands by speaker; mono font for timestamps; keyboard seek (←/→ by segment).  
- Segment menu: Copy quote, Make clip (±N), Highlight, Add tag.  
- Export dialog: SRT/VTT, DOCX, PDF (Quote Pack), CSV, JSON.  
- Settings: retention, storage on/off, allow anon learning (off default), name dictionary.

---

## 12) Project Setup With `uv`

```bash
uv init caseprep
cd caseprep
uv add fastapi uvicorn[standard] pydantic[dotenv] python-multipart
uv add sqlalchemy psycopg2-binary alembic
uv add redis celery orjson httpx
uv add ffmpeg-python
uv add faster-whisper whisperx pyannote.audio torch torchaudio
uv add cryptography pynacl pyjwt
uv add python-docx reportlab pypdf2
```

> Torch wheels may need platform-specific steps; document Mac/Linux install notes.

---

## 13) Docker Compose (Dev)

**docker-compose.yml**
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
      - S3_ACCESS_KEY=minio
      - S3_SECRET_KEY=minio123
    ports: ["8080:8080"]
    depends_on: [db, redis, minio]
  worker:
    build: ./services/worker
    environment:
      - REDIS_URL=redis://redis:6379/0
      - S3_ENDPOINT=http://minio:9000
      - S3_BUCKET=caseprep
      - S3_ACCESS_KEY=minio
      - S3_SECRET_KEY=minio123
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

**services/api/Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN pip install uv && uv sync --frozen || true
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**services/worker/Dockerfile (CPU)**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN pip install uv && uv sync --frozen || true
COPY . .
CMD ["celery", "-A", "celery_app.celery", "worker", "--loglevel=INFO"]
```

---

## 14) GPU Worker Setup & Options

### 14.1 Self‑hosted GPU (Ubuntu)

1. **NVIDIA drivers & CUDA**  
   - Install latest production drivers (e.g., `ubuntu-drivers install`).  
   - Install CUDA/cuDNN matching PyTorch versions.  
2. **Docker + NVIDIA toolkit**  
   ```bash
   curl -fsSL https://get.docker.com | sh
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
   curl -fsSL https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
     sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
   sudo apt update && sudo apt install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure && sudo systemctl restart docker
   ```
3. **GPU worker image**  
   **services/worker/Dockerfile.gpu**
   ```dockerfile
   FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04
   WORKDIR /app
   RUN apt-get update && apt-get install -y python3-pip ffmpeg && rm -rf /var/lib/apt/lists/*
   COPY pyproject.toml uv.lock* ./
   RUN pip install uv && uv sync --frozen || true
   COPY . .
   ENV NVIDIA_VISIBLE_DEVICES=all NVIDIA_DRIVER_CAPABILITIES=compute,utility,video
   CMD ["celery", "-A", "celery_app.celery", "worker", "--loglevel=INFO", "-Q", "gpu"]
   ```
4. **Compose override**  
   ```yaml
   worker-gpu:
     build:
       context: ./services/worker
       dockerfile: Dockerfile.gpu
     deploy:
       resources:
         reservations:
           devices:
             - capabilities: [gpu]
     environment:
       - REDIS_URL=redis://redis:6379/0
       - CUDA_VISIBLE_DEVICES=0
     depends_on: [redis, minio]
   ```

### 14.2 Managed GPU Cloud (autoscaling)

- **Pattern**: Build a worker container; run N replicas behind an autoscaler triggered by **queue depth** and **avg job time**.  
- **Providers**: AWS g5/g6/g6e, GCP A2/L4, Azure NC; specialist: Lambda Labs, CoreWeave, RunPod, Paperspace.  
- **Security**: place workers in no‑egress subnets; allow to Redis + MinIO only; use **mTLS** to API.  
- **Storage**: S3/MinIO with SSE‑KMS; lifecycle policies for ephemeral mode (24h TTL).  

### 14.3 Hybrid with Vercel

- Host UI on **Vercel**; API + GPU workers on your infra/cloud.  
- Secure link: **mTLS**, **WireGuard site‑to‑site**, or **Cloudflare Tunnels**.  
- Vercel functions **only enqueue** work; heavy lifting is in workers.

---

## 15) Config & Env

```
APP_ENV=dev
SECRET_KEY=...                          # JWT / cookies
DATABASE_URL=postgresql+psycopg2://...
REDIS_URL=redis://...
STORAGE_BACKEND=null|local|s3
LOCAL_STORAGE_PATH=/data
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

## 16) Logging, Metrics, and Auditing

- **Logs**: structured (orjson); include request/job IDs.  
- **Metrics**: ASR mins/sec, queue depth, success/error counts, export latency, WER proxy.  
- **Audit**: append‑only hash chain; snapshot to cold storage (opt‑in).

---

## 17) Testing Plan

- **Unit**: dictionary rules, speaker alias propagation, export formatters.  
- **Integration**: end‑to‑end pipeline on 1–3 short media files; golden JSON compare.  
- **Security**: upload validators, permission checks, storage toggles.  
- **Performance**: compare `medium` vs `large‑v3` across 10–60 min inputs; record GPU vs CPU times.

---

## 18) Exports

- **SRT/VTT** captions; **DOCX** styled by speaker; **PDF Quote Pack** with cover (matter metadata + SHA‑256), highlighted quotes, optional QR links; **CSV** segments; **JSON** full transcript.  
- All exports embed hash + audit pointer.

---

## 19) Roadmap

- **MVP (8–10 weeks part‑time)**: upload, transcribe, diarize, edit, export, clips, user dictionaries, audit log.  
- **Phase 1.5**: client‑only encrypted bundles; WASM/WebGPU feasibility spikes.  
- **Phase 2 (>6 months)**: court‑reporter partner network; certified transcript workflow; multi‑language; live capture.

---

## 20) Decisions Recap (Locked)

- **Storage (dev)**: MinIO; LocalFS only for demos.  
- **Processing (now)**: web‑local CPU; **Prod**: GPU worker backend.  
- **Global corrections**: OFF by default; opt‑in per workspace; transparency UI; user rules override.

---

## 21) Appendices

### A) Example Makefile
```makefile
.PHONY: api worker up down fmt lint
up:
\tdocker compose up -d --build

down:
\tdocker compose down -v

api:
\tuvicorn services.api.main:app --reload --port 8080

worker:
\tcelery -A services.worker.celery_app.celery worker -l INFO

fmt:
\truff check --fix . && black .
```

### B) Hashing Utility (Python)
```python
import hashlib, sys
with open(sys.argv[1], 'rb') as f:
    print(hashlib.sha256(f.read()).hexdigest())
```

### C) WireGuard (snip)
```ini
[Interface]
PrivateKey = <api-priv>
Address = 10.10.0.1/24

[Peer]
PublicKey = <worker-pub>
AllowedIPs = 10.10.0.0/24
Endpoint = worker.example.com:51820
PersistentKeepalive = 25
```

### D) Cloudflare Tunnel (snip)
```bash
cloudflared tunnel create caseprep
cloudflared tunnel route dns caseprep api.caseprep.local
cloudflared tunnel run caseprep
```

### E) OpenAPI (extended stub)
```yaml
components:
  schemas:
    Transcript:
      type: object
      properties:
        transcriptId: { type: string, format: uuid }
        segments:
          type: array
          items:
            type: object
            properties:
              id: { type: string, format: uuid }
              speaker: { type: string }
              startMs: { type: integer }
              endMs: { type: integer }
              text: { type: string }
```

---

*End of Comprehensive Blueprint v1.2*
