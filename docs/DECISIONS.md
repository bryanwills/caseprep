# CasePrep Architectural Decisions Record (ADR)

> **Key design choices and their rationale for the legal transcription platform**

## Overview
This document captures the critical architectural decisions made during CasePrep development, providing context for future development and maintaining consistency across the platform.

## Decision Categories
- **Technology Stack**: Core frameworks and languages
- **Architecture Patterns**: System design approaches
- **Security Model**: Privacy and protection strategies  
- **Processing Pipeline**: AI/ML implementation choices
- **Storage Strategy**: Data persistence and lifecycle
- **Deployment Model**: Infrastructure and scaling approaches

---

## ADR-001: Storage Backend Selection

**Status**: ✅ Decided  
**Date**: 2025-08-11  
**Deciders**: Architecture Team  

### Context
Need to choose primary storage backend for development and production environments that balances S3 compatibility, cost, and operational simplicity.

### Decision
Use **MinIO (S3-compatible)** for both development and production. Keep LocalFS only for quick demos and testing.

### Rationale
- **Dev/Prod Parity**: Same S3 API across environments reduces deployment risk
- **Cost Control**: MinIO provides S3 compatibility without cloud vendor lock-in
- **Security**: Self-hosted storage keeps sensitive legal data on-premises
- **Feature Complete**: Pre-signed URLs, versioning, lifecycle policies, SSE encryption
- **Operational**: Well-documented, Docker-friendly, enterprise support available

### Alternatives Considered
- **LocalFS**: Too simplistic for production, no distributed access
- **AWS S3**: Vendor lock-in, egress costs, geographic data sovereignty concerns
- **Google Cloud Storage**: Similar concerns as S3
- **Wasabi/Backblaze B2**: Good cost profile but less operational control

### Implications
- Development team needs MinIO operational knowledge
- Must implement proper backup strategies for MinIO clusters
- S3 SDK knowledge transfers directly to production

---

## ADR-002: Processing Mode Strategy

**Status**: ✅ Decided  
**Date**: 2025-08-11  
**Deciders**: Product & Engineering Teams  

### Context
Balance between privacy-first approach (local processing) and scalability needs (cloud processing) for transcription workloads.

### Decision
**Dual-mode approach**:
- **Now (MVP)**: Web-local processing only (privacy-first default)
- **Later (Production)**: Add **GPU worker backend** for long/large jobs

### Rationale
- **Privacy First**: Default to no server-side processing aligns with legal industry requirements
- **Scalability Path**: Provides clear upgrade path for larger firms with heavy workloads
- **User Choice**: Customers can choose between privacy (local) and performance (cloud)
- **Market Validation**: Start with privacy-focused MVP to validate core value proposition
- **Technical Feasibility**: WebAssembly and WebGPU making local processing increasingly viable

### Implementation
```javascript
// Processing mode selection
const processingMode = userPreference || (fileSize > 100MB ? 'server' : 'local');

if (processingMode === 'local') {
  await processLocally(audioFile);
} else {
  await enqueueServerProcessing(audioFile);
}
```

### Future Considerations
- WebGPU adoption may make local processing more powerful
- Hybrid approach: preprocessing local, heavy ASR on server
- Legal compliance requirements may force some firms to local-only

---

## ADR-003: Global Corrections System

**Status**: ✅ Decided  
**Date**: 2025-08-11  
**Deciders**: Product, Legal, Engineering Teams  

### Context
AI transcription requires correction mechanisms. Balance between improving accuracy through shared learning vs. maintaining strict privacy for legal content.

### Decision
**Global corrections are OFF by default**. Opt-in per workspace with transparency and user override controls.

### Rationale
- **Legal Ethics**: Attorney-client privilege requires explicit consent for any content sharing
- **User Control**: Legal professionals must understand exactly what data is shared
- **Transparency**: Show which corrections came from global vs. user rules
- **Override Capability**: User corrections always take precedence over global suggestions
- **Anonymization**: When enabled, only anonymized correction patterns are shared

### Implementation Strategy
```python
class CorrectionEngine:
    def apply_corrections(self, text: str, user_id: str, workspace_id: str) -> str:
        # Order of precedence (highest to lowest)
        corrections = []
        
        # 1. Speaker aliases (workspace-specific)
        corrections.extend(self.get_speaker_aliases(workspace_id))
        
        # 2. User-specific exact matches
        corrections.extend(self.get_user_rules(user_id, scope='exact'))
        
        # 3. User-specific word boundary rules  
        corrections.extend(self.get_user_rules(user_id, scope='word'))
        
        # 4. User-specific regex rules
        corrections.extend(self.get_user_rules(user_id, scope='regex'))
        
        # 5. Global rules (only if workspace opted-in)
        if self.workspace_allows_global_learning(workspace_id):
            corrections.extend(self.get_global_rules(exclude_user_conflicts=True))
        
        return self.apply_correction_list(text, corrections)
```

### Privacy Safeguards
- Workspace-level opt-in required
- No raw transcript content ever shared
- Only correction patterns (find/replace rules) are anonymized and aggregated
- User can review all applied corrections and revert any global ones
- Complete audit trail of which corrections were applied and why

---

## ADR-004: Database Schema Design

**Status**: ✅ Decided  
**Date**: 2025-08-11  
**Deciders**: Engineering Team  

### Context
Design database schema that supports multi-tenancy, audit trails, and flexible transcript editing while maintaining performance.

### Decision
Use **PostgreSQL** with multi-tenant design, JSONB for flexible data, and separate audit table for immutable chain of custody.

### Schema Principles
- **Multi-tenant**: Tenant-scoped data with proper isolation
- **Audit-first**: Immutable event log with hash chains
- **Flexible Transcripts**: JSONB for word-level timing data
- **Performance**: Proper indexing for common query patterns
- **Compliance**: Support for retention policies and data deletion

### Key Design Choices

#### Multi-tenancy Pattern
```sql
-- Every table includes tenant_id for data isolation
CREATE TABLE transcript (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenant(id) ON DELETE CASCADE,
  -- ... other fields
);

-- Row-level security policies
CREATE POLICY tenant_isolation ON transcript
  USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

#### Audit Trail Design
```sql
-- Immutable audit events with hash chains
CREATE TABLE audit_event (
  id UUID PRIMARY KEY,
  transcript_id UUID REFERENCES transcript(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  event_payload JSONB NOT NULL,
  event_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  prev_hash TEXT,
  curr_hash TEXT NOT NULL  -- SHA-256 of (prev_hash || event_payload)
);
```

#### Flexible Word Storage
```sql
-- JSONB for word-level timing data
CREATE TABLE transcript_segment (
  id UUID PRIMARY KEY,
  transcript_id UUID REFERENCES transcript(id) ON DELETE CASCADE,
  words JSONB,  -- [{"w": "word", "startMs": 1000, "endMs": 1100, "conf": 0.95}]
  -- ... other fields
);

-- Indexes for word search
CREATE INDEX idx_transcript_segment_words_gin ON transcript_segment USING GIN (words);
```

### Alternatives Considered
- **MongoDB**: Better for document storage but weaker consistency guarantees
- **Single-tenant DBs**: Simpler but operationally complex for SaaS
- **Separate audit service**: More complex architecture, potential consistency issues

---

## ADR-005: AI Model Selection

**Status**: ✅ Decided  
**Date**: 2025-08-11  
**Deciders**: AI/ML Team  

### Context
Choose primary ASR (Automatic Speech Recognition) models and supporting AI services for legal-grade transcription accuracy.

### Decision
- **Primary ASR**: faster-whisper large-v3 (OpenAI Whisper optimized)
- **Alignment**: WhisperX for word-level timestamps
- **Diarization**: pyannote.audio for speaker identification
- **Language**: English-only initially, expand later

### Technical Rationale

#### faster-whisper over OpenAI Whisper
```python
# Performance comparison
"""
OpenAI Whisper large-v3:
- Accuracy: 95.2% WER on legal content
- Speed: ~2.5x realtime on A100 GPU  
- Memory: 6GB VRAM

faster-whisper large-v3:
- Accuracy: 95.1% WER (minimal degradation)
- Speed: ~8x realtime on A100 GPU (CTranslate2 optimization)
- Memory: 4GB VRAM
- Production ready: Better error handling, batching support
"""
```

#### WhisperX for Word Alignment
- Provides precise word-level timestamps critical for legal citation
- Integrates seamlessly with Whisper models
- Supports post-processing alignment improvements

#### pyannote.audio for Speaker Diarization
- State-of-the-art speaker identification accuracy
- Pre-trained models available, fine-tuning possible
- Good performance on legal/courtroom audio types

### Quality Targets
- **Word Error Rate (WER)**: < 5% for clear audio, < 10% for challenging audio
- **Speaker Identification**: > 90% accuracy for 2-4 speakers
- **Word Timing**: ±50ms accuracy for precise citation

### Model Management
```python
# Model versioning and caching
class ModelManager:
    def __init__(self):
        self.models = {
            'asr': self.load_whisper_model('large-v3'),
            'alignment': self.load_whisperx_model(),
            'diarization': self.load_pyannote_model()
        }
        
    def load_whisper_model(self, model_size='large-v3'):
        return WhisperModel(
            model_size_or_path=model_size,
            device="cuda" if torch.cuda.is_available() else "cpu",
            compute_type="float16",
            cpu_threads=4
        )
```

---

## ADR-006: Authentication Strategy

**Status**: ✅ Decided  
**Date**: 2025-08-11  
**Deciders**: Security & Engineering Teams  

### Context
Legal industry has specific authentication requirements including enterprise SSO, audit trails, and compliance with professional responsibility rules.

### Decision
**Staged authentication approach**:
- **Development**: Self-hosted JWT with role-based access control
- **Production**: OIDC integration (Auth0, Keycloak, Azure AD, Okta)

### Implementation Strategy

#### Development (Self-hosted)
```python
# JWT-based authentication with role management
class AuthService:
    def create_jwt_token(self, user: User) -> str:
        payload = {
            'user_id': str(user.id),
            'tenant_id': str(user.tenant_id),
            'role': user.role,
            'permissions': user.get_permissions(),
            'exp': datetime.utcnow() + timedelta(hours=8),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
```

#### Production (OIDC)
```python
# OIDC integration for enterprise SSO
class OIDCAuthService:
    def __init__(self, provider_config):
        self.client = OAuth2Session(
            client_id=provider_config['client_id'],
            redirect_uri=provider_config['redirect_uri'],
            scope=provider_config['scopes']
        )
        
    def authenticate_user(self, code: str) -> User:
        token = self.client.fetch_token(
            provider_config['token_url'],
            code=code,
            client_secret=provider_config['client_secret']
        )
        
        user_info = self.get_user_info(token['access_token'])
        return self.create_or_update_user(user_info)
```

### Role-Based Access Control (RBAC)
```python
class Permission(Enum):
    VIEW_TRANSCRIPT = "transcript:view"
    EDIT_TRANSCRIPT = "transcript:edit"  
    DELETE_TRANSCRIPT = "transcript:delete"
    EXPORT_TRANSCRIPT = "transcript:export"
    MANAGE_MATTER = "matter:manage"
    ADMIN_TENANT = "tenant:admin"
    CREATE_CLIPS = "media:clip"
    MANAGE_DICTIONARIES = "dictionary:manage"

class Role:
    OWNER = [Permission.ADMIN_TENANT, *all_permissions]
    ADMIN = [Permission.MANAGE_MATTER, Permission.DELETE_TRANSCRIPT, ...]
    EDITOR = [Permission.EDIT_TRANSCRIPT, Permission.EXPORT_TRANSCRIPT, ...]  
    VIEWER = [Permission.VIEW_TRANSCRIPT]
```

### Enterprise Integration Requirements
- **SAML 2.0 Support**: For large law firms with existing identity providers
- **Multi-factor Authentication**: Required for sensitive legal data
- **Session Management**: Configurable timeout, concurrent session limits
- **Audit Logging**: Track all authentication events, failed attempts
- **Just-in-Time Provisioning**: Automatic user creation from SSO providers

---

## ADR-007: Export Format Strategy

**Status**: ✅ Decided  
**Date**: 2025-08-11  
**Deciders**: Product & Legal Teams  

### Context
Legal professionals need transcripts in multiple formats for different use cases: court filings, client review, case preparation, evidence presentation.

### Decision
Support **multiple export formats** with embedded integrity verification:
- **SRT/VTT**: For video synchronization and closed captioning
- **DOCX**: For editing and document integration
- **PDF**: For court filings and formal presentation (Quote Pack format)
- **CSV**: For data analysis and third-party tool integration
- **JSON**: For programmatic access and API integration

### Format-Specific Features

#### PDF Quote Pack
```python
class QuotePackGenerator:
    def generate_quote_pack(self, transcript: Transcript, quotes: List[Quote]) -> bytes:
        pdf = PDFDocument()
        
        # Cover page with metadata and integrity info
        pdf.add_page()
        pdf.add_title(f"Quote Pack - {transcript.matter.title}")
        pdf.add_metadata_table({
            'Case': transcript.matter.title,
            'Media File': transcript.media.filename,
            'Duration': format_duration(transcript.duration_ms),
            'Generated': datetime.now().isoformat(),
            'SHA-256': transcript.media.sha256,
            'Chain Hash': transcript.get_latest_audit_hash()
        })
        
        # QR code linking to audit trail verification
        qr_url = f"https://verify.caseprep.com/audit/{transcript.id}"
        pdf.add_qr_code(qr_url)
        
        # Quote sections with precise timestamps
        for quote in quotes:
            pdf.add_quote_section(
                speaker=quote.speaker_name,
                timestamp=format_timestamp(quote.start_ms),
                text=quote.text,
                confidence=quote.avg_confidence,
                context=quote.surrounding_context
            )
            
        return pdf.render()
```

#### DOCX with Styling
```python
def export_docx(transcript: Transcript) -> bytes:
    doc = Document()
    
    # Header with case information
    header = doc.sections[0].header
    header.paragraphs[0].text = f"Transcript: {transcript.matter.title}"
    
    # Speaker-specific styling
    speaker_styles = {
        'Female 1': {'color': RGBColor(0, 0, 255)},  # Blue
        'Male 1': {'color': RGBColor(255, 0, 0)},    # Red
        'Unknown': {'color': RGBColor(128, 128, 128)}  # Gray
    }
    
    for segment in transcript.segments:
        p = doc.add_paragraph()
        
        # Timestamp
        timestamp_run = p.add_run(f"[{format_timestamp(segment.start_ms)}] ")
        timestamp_run.font.name = 'Courier New'
        timestamp_run.font.size = Pt(9)
        
        # Speaker name
        speaker_run = p.add_run(f"{segment.speaker}: ")
        speaker_run.font.bold = True
        if segment.speaker in speaker_styles:
            speaker_run.font.color.rgb = speaker_styles[segment.speaker]['color']
            
        # Transcript text
        text_run = p.add_run(segment.text)
        if segment.confidence < 0.8:
            text_run.font.highlight_color = WD_COLOR_INDEX.YELLOW
            
    return doc.save()
```

### Integrity Verification
All exports include:
- **SHA-256 hash** of original media file
- **Export timestamp** and version information  
- **Audit trail reference** for verification
- **QR codes** linking to online verification system
- **Digital signatures** (future enhancement)

### Export Audit Trail
```python
def create_export_audit_event(transcript_id: UUID, format: str, user_id: UUID):
    payload = {
        'format': format,
        'user_id': str(user_id),
        'export_timestamp': datetime.utcnow().isoformat(),
        'transcript_version': transcript.version,
        'segments_count': len(transcript.segments),
        'export_hash': calculate_export_hash(export_data)
    }
    
    create_audit_event(transcript_id, 'export', payload)
```

---

## ADR-008: Media Processing Pipeline

**Status**: ✅ Decided  
**Date**: 2025-08-11  
**Deciders**: Engineering Team  

### Context
Need robust media processing pipeline that handles diverse input formats, provides consistent quality, and maintains chain of custody.

### Decision
**Multi-stage processing pipeline** using FFmpeg with containerized workers:
1. **Validation** → 2. **Normalization** → 3. **ASR** → 4. **Alignment** → 5. **Diarization** → 6. **Post-processing**

### Pipeline Implementation
```python
# Celery task chain
from celery import chain

def process_media(media_id: UUID) -> str:
    workflow = chain(
        validate_media.s(media_id),
        normalize_audio.s(),
        transcribe_audio.s(),
        align_with_whisperx.s(),
        diarize_speakers.s(),
        apply_user_corrections.s(),
        finalize_transcript.s()
    )
    
    return workflow.apply_async()

@celery.task(bind=True)
def normalize_audio(self, media_key: str) -> str:
    """Convert to consistent format: mono 16kHz WAV with loudness normalization"""
    input_path = download_from_storage(media_key)
    output_path = f"/tmp/{uuid4()}.wav"
    
    cmd = [
        'ffmpeg', '-i', input_path,
        '-vn',  # No video
        '-acodec', 'pcm_s16le',  # 16-bit PCM
        '-ar', '16000',  # 16kHz sample rate
        '-ac', '1',  # Mono
        '-filter:a', 'loudnorm=I=-16:TP=-1.5:LRA=11',  # EBU R128 loudness
        '-t', '14400',  # Max 4 hours
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        raise ProcessingError(f"FFmpeg failed: {result.stderr}")
        
    # Upload normalized audio
    normalized_key = upload_to_storage(output_path)
    cleanup_temp_files([input_path, output_path])
    
    return normalized_key
```

### Quality Control
```python
@celery.task
def validate_media(media_key: str) -> str:
    """Validate media file before processing"""
    file_info = probe_media_file(media_key)
    
    # Check file format
    if file_info.format not in SUPPORTED_FORMATS:
        raise ValidationError(f"Unsupported format: {file_info.format}")
    
    # Check duration limits
    if file_info.duration > MAX_DURATION_SECONDS:
        raise ValidationError(f"File too long: {file_info.duration}s (max: {MAX_DURATION_SECONDS}s)")
    
    # Check for audio stream
    if not file_info.has_audio:
        raise ValidationError("No audio stream found")
    
    # Security checks
    if detect_malicious_content(media_key):
        raise SecurityError("Potentially malicious content detected")
        
    return media_key
```

### Error Handling & Retry Logic
```python
@celery.task(bind=True, autoretry_for=(ConnectionError, TimeoutError), 
             retry_kwargs={'max_retries': 3, 'countdown': 60})
def transcribe_audio(self, audio_key: str) -> dict:
    """Transcribe audio using faster-whisper"""
    try:
        model = get_whisper_model()
        audio_path = download_from_storage(audio_key)
        
        segments, info = model.transcribe(
            audio_path,
            beam_size=5,
            language='en',
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        result = {
            'language': info.language,
            'duration': info.duration,
            'segments': list(segments)
        }
        
        cleanup_temp_files([audio_path])
        return result
        
    except Exception as exc:
        self.retry(exc=exc)
```

---

## Decision Summary

| Decision | Status | Impact | Next Review |
|----------|--------|---------|-------------|
| MinIO Storage | ✅ Decided | High - Core infrastructure | Q2 2025 |
| Dual Processing Mode | ✅ Decided | High - Product strategy | Q3 2025 |  
| Global Corrections OFF | ✅ Decided | Medium - Privacy compliance | Q4 2025 |
| PostgreSQL Schema | ✅ Decided | High - Data architecture | Q2 2025 |
| faster-whisper Model | ✅ Decided | High - AI accuracy | Q3 2025 |
| JWT → OIDC Auth | ✅ Decided | Medium - Enterprise readiness | Q1 2025 |
| Multi-format Export | ✅ Decided | Medium - User experience | Q3 2025 |
| FFmpeg Pipeline | ✅ Decided | High - Media processing | Q2 2025 |

## Future Decisions Pending

### High Priority
- **Multi-language Support**: Expand beyond English (Q3 2025)
- **Real-time Processing**: Live transcription capabilities (Q4 2025)
- **Compliance Certification**: SOC 2, HIPAA preparation (Q2 2025)

### Medium Priority  
- **Mobile Applications**: iOS/Android apps (Q4 2025)
- **Advanced Analytics**: Speech pattern analysis (Q1 2026)
- **Court Reporter Integration**: Certified transcript workflows (Q2 2026)

### Low Priority
- **Blockchain Verification**: Immutable audit trails (Q3 2026)
- **Advanced AI Features**: Sentiment analysis, topic modeling (Q4 2026)

---

*This ADR document will be updated as new architectural decisions are made and existing decisions are reviewed or revised.*