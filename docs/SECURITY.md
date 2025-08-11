# CasePrep Security & Privacy Architecture

> **Comprehensive security overview for legal-grade evidence processing**

## Security Principles

### Defense in Depth
1. **Privacy by Default** - No server-side storage unless explicitly opted-in
2. **Zero Trust Architecture** - Verify every request, encrypt everything
3. **Minimal Attack Surface** - Sandboxed workers, no-egress networks
4. **Chain of Custody** - Immutable audit trails with cryptographic integrity
5. **Data Sovereignty** - Complete user control over data location and retention

## Data Protection Framework

### Data Classification
- **Level 1: Public** - Marketing content, documentation
- **Level 2: Internal** - System logs, performance metrics  
- **Level 3: Confidential** - User accounts, tenant configuration
- **Level 4: Restricted** - Legal evidence, transcripts, audio/video files

### Storage Architecture

#### Default: No Storage Mode
- All processing occurs in ephemeral containers
- Media and results exist only in memory during processing
- Complete deletion upon job completion
- Client receives results directly via secure WebSocket/polling

#### Optional: Encrypted Storage Mode
```python
# Application-layer encryption example
def encrypt_transcript(data: str, tenant_key: bytes) -> EncryptedBlob:
    nonce = os.urandom(12)  # XChaCha20-Poly1305 nonce
    cipher = ChaCha20Poly1305(tenant_key)
    ciphertext = cipher.encrypt(nonce, data.encode(), None)
    return EncryptedBlob(nonce=nonce, data=ciphertext, algorithm="xchacha20-poly1305")
```

## Encryption Implementation

### Transit Encryption
- **External**: TLS 1.3 with HSTS, OCSP stapling
- **Internal**: mTLS between all services with certificate rotation
- **Client-Server**: End-to-end encryption for sensitive payloads
- **File Uploads**: Direct browser → MinIO via pre-signed URLs over HTTPS

### At-Rest Encryption
- **Storage**: SSE-KMS (S3/MinIO) with customer-managed keys
- **Database**: Transparent Data Encryption (TDE) with application-layer encryption overlay
- **Application**: XChaCha20-Poly1305 with per-tenant envelope keys
- **Backups**: Encrypted before transfer to cold storage

### Key Management
```yaml
# HashiCorp Vault configuration
storage "consul" {
  address = "127.0.0.1:8500"
  path    = "vault/"
}

listener "tcp" {
  address = "0.0.0.0:8200"
  tls_cert_file = "/path/to/fullchain.pem"
  tls_key_file  = "/path/to/privkey.pem"
}

seal "awskms" {
  region     = "us-east-1"
  kms_key_id = "alias/vault-unseal-key"
}
```

#### Key Hierarchy
1. **Master Key** - Hardware Security Module or Cloud KMS
2. **Wrapping Keys** - Per-tenant, rotated quarterly
3. **Data Keys** - Per-document, generated on-demand
4. **Archive Keys** - Long-term retention, cold storage

## Chain of Custody

### Audit Event Structure
```sql
CREATE TABLE audit_event (
  id UUID PRIMARY KEY,
  transcript_id UUID REFERENCES transcript(id),
  event_type TEXT NOT NULL,  -- 'upload', 'process', 'edit', 'export', 'delete'
  event_payload JSONB NOT NULL,
  event_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  user_id UUID,
  prev_hash TEXT,
  curr_hash TEXT NOT NULL,  -- SHA-256 of (prev_hash || event_payload)
  signature TEXT            -- Future: digital signature
);
```

### Hash Chain Implementation
```python
def create_audit_event(transcript_id: UUID, event_type: str, payload: dict) -> str:
    prev_event = get_latest_audit_event(transcript_id)
    prev_hash = prev_event.curr_hash if prev_event else "genesis"
    
    event_data = {
        "transcript_id": str(transcript_id),
        "event_type": event_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat(),
        "prev_hash": prev_hash
    }
    
    curr_hash = hashlib.sha256(json.dumps(event_data, sort_keys=True).encode()).hexdigest()
    
    audit_event = AuditEvent(
        transcript_id=transcript_id,
        event_type=event_type,
        event_payload=payload,
        prev_hash=prev_hash,
        curr_hash=curr_hash
    )
    
    db.add(audit_event)
    db.commit()
    return curr_hash
```

### Evidence Integrity
- **File Hashing**: SHA-256 computed on original upload
- **Transcript Hashing**: Hash of processed results before any edits
- **Export Hashing**: New hash for each export format
- **Chain Validation**: Verify complete audit trail integrity
- **Tamper Detection**: Detect any unauthorized modifications

## Access Control & Authentication

### Multi-Tenant Architecture
```python
# Role-based access control
class Permission(Enum):
    VIEW_TRANSCRIPT = "transcript:view"
    EDIT_TRANSCRIPT = "transcript:edit"
    DELETE_TRANSCRIPT = "transcript:delete"
    EXPORT_TRANSCRIPT = "transcript:export"
    MANAGE_MATTER = "matter:manage"
    ADMIN_TENANT = "tenant:admin"

class Role:
    OWNER = [Permission.ADMIN_TENANT, Permission.MANAGE_MATTER, ...]
    ADMIN = [Permission.MANAGE_MATTER, Permission.DELETE_TRANSCRIPT, ...]
    EDITOR = [Permission.EDIT_TRANSCRIPT, Permission.EXPORT_TRANSCRIPT, ...]
    VIEWER = [Permission.VIEW_TRANSCRIPT]
```

### Authentication Methods
- **Development**: JWT with self-hosted validation
- **Production**: OIDC integration (Auth0, Keycloak, Azure AD)
- **API**: Bearer tokens with scope-based permissions
- **Service-to-Service**: mTLS with certificate-based authentication

## Network Security

### Container Isolation
```dockerfile
# Worker container security
FROM python:3.11-slim
RUN groupadd -r worker && useradd -r -g worker worker
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Security hardening
COPY --chown=worker:worker . /app
USER worker
WORKDIR /app

# Restrict capabilities
RUN setcap cap_sys_nice+ep /usr/bin/python3
```

```yaml
# Docker Compose security
version: "3.9"
services:
  worker:
    security_opt:
      - no-new-privileges:true
      - seccomp:./seccomp-worker.json
      - apparmor:caseprep-worker
    networks:
      - worker_network
    cap_drop:
      - ALL
    cap_add:
      - SYS_NICE  # For process priority management
```

### Network Segmentation
- **DMZ**: Web application firewall, rate limiting
- **Application Layer**: API servers, authentication services
- **Processing Layer**: Isolated worker nodes, no internet access
- **Data Layer**: Database and storage with encrypted connections

## Threat Model & Mitigations

### Attack Vectors & Controls

#### File Upload Attacks
- **Malicious Files**: Content-type validation, virus scanning, sandbox execution
- **Resource Exhaustion**: File size limits, processing timeouts, memory constraints
- **Format Exploits**: FFmpeg argument sanitization, container isolation

```python
# File validation example
ALLOWED_MIME_TYPES = {
    'video/mp4', 'video/quicktime', 'video/x-msvideo',
    'audio/wav', 'audio/mpeg', 'audio/x-wav'
}

FFMPEG_SAFE_ARGS = [
    '-i', '-vn', '-acodec', 'pcm_s16le', 
    '-ar', '16000', '-ac', '1', '-t', '3600'  # Max 1 hour
]

def validate_upload(file: UploadFile) -> bool:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError("Unsupported file type")
    
    if file.size > MAX_UPLOAD_SIZE:
        raise ValidationError("File too large")
    
    # Additional magic number validation
    header = file.file.read(12)
    file.file.seek(0)
    return validate_file_header(header, file.content_type)
```

#### Data Exfiltration
- **Insider Threats**: Role-based access, audit logging, data masking
- **External Access**: VPN requirements, IP allowlisting, geographic restrictions
- **Side Channels**: Network traffic analysis prevention, timing attack mitigation

#### Privacy Violations
- **Data Leakage**: Automatic PII detection and masking
- **Unauthorized Access**: Strong authentication, session management
- **Cross-Tenant**: Strict tenant isolation, resource quotas

## Compliance Framework

### Legal Industry Requirements
- **Attorney-Client Privilege**: No third-party access to content
- **Evidence Preservation**: Immutable storage, chain of custody
- **Court Admissibility**: Authenticated exports, provenance tracking
- **Bar Association Rules**: Competence in technology use, confidentiality

### Privacy Regulations
- **GDPR Compliance**: Right to deletion, data portability, consent management
- **CCPA Requirements**: Consumer rights, opt-out mechanisms
- **HIPAA (if applicable)**: PHI protection for medical-legal cases
- **Industry Standards**: SOC 2 Type II, ISO 27001 preparation

### Data Retention Policies
```python
class RetentionPolicy:
    EPHEMERAL = 0      # Delete immediately after processing
    SHORT_TERM = 7     # 7 days for review
    STANDARD = 30      # 30 days for typical cases  
    EXTENDED = 90      # 90 days for complex litigation
    CUSTOM = -1        # User-defined retention period

def apply_retention_policy(matter: Matter):
    if matter.retention_days == 0:
        # Immediate deletion after processing
        schedule_deletion(matter.id, delay=timedelta(hours=1))
    elif matter.retention_days > 0:
        schedule_deletion(matter.id, delay=timedelta(days=matter.retention_days))
    # Custom retention requires manual deletion
```

## Incident Response Plan

### Security Event Categories
1. **P0: Data Breach** - Unauthorized access to restricted data
2. **P1: System Compromise** - Malware, insider threat, privilege escalation
3. **P2: Service Disruption** - DDoS, infrastructure failure, data corruption
4. **P3: Policy Violation** - Misuse, compliance deviation, process failure

### Response Procedures
1. **Detection**: Automated alerts, anomaly detection, user reports
2. **Assessment**: Impact analysis, affected systems, data exposure
3. **Containment**: Isolate affected systems, preserve evidence
4. **Investigation**: Forensic analysis, root cause determination
5. **Recovery**: System restoration, data recovery, service resumption
6. **Lessons Learned**: Process improvements, security enhancements

### Communication Plan
- **Internal**: Security team, engineering, legal, executive leadership
- **External**: Affected customers, regulatory bodies, law enforcement
- **Timeline**: Within 1 hour (internal), 24 hours (customer), 72 hours (regulatory)

## Security Monitoring

### Detection Capabilities
- **Authentication**: Failed login attempts, privilege escalation, unusual access patterns
- **Data Access**: Large downloads, cross-tenant queries, sensitive data exposure  
- **System**: Resource exhaustion, configuration changes, malware indicators
- **Network**: Unusual traffic patterns, data exfiltration attempts, command & control

### Logging Requirements
```python
# Security event logging structure
security_event = {
    "timestamp": "2025-08-11T20:00:00Z",
    "event_id": "sec_12345",
    "severity": "HIGH",
    "category": "data_access",
    "source_ip": "203.0.113.1",
    "user_id": "user_67890",
    "tenant_id": "tenant_abc123",
    "resource": "transcript_def456",
    "action": "unauthorized_access_attempt",
    "outcome": "blocked",
    "details": {
        "user_agent": "Mozilla/5.0...",
        "requested_resource": "/api/v1/transcripts/def456",
        "access_method": "direct_url",
        "reason_blocked": "insufficient_permissions"
    }
}
```

## Disaster Recovery

### Backup Strategy
- **Database**: Point-in-time recovery with 15-minute RPO
- **Object Storage**: Cross-region replication with versioning
- **Configuration**: Infrastructure as Code with version control
- **Encryption Keys**: Secure key escrow with multiple recovery methods

### Recovery Testing
- Monthly disaster recovery drills
- Annual third-party security assessments
- Quarterly penetration testing
- Continuous vulnerability scanning

---

*This security framework provides the foundation for building a legally compliant, privacy-first transcription platform that meets the stringent requirements of legal evidence processing.*