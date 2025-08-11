# CasePrep - Legal Transcription & Case Preparation SaaS

> **Privacy-first legal transcription tool for evidence processing**  
> Extract and analyze audio/video evidence with AI transcription, speaker diarization, and secure case preparation workflows.

## 🎯 Vision
Transform how law offices handle evidence by providing accurate, secure transcription of videos, audio recordings, and depositions with privacy-first design and chain-of-custody integrity.

## ⚡ Key Features

### Core Functionality
- **Multi-format Support** - Process video/audio evidence (MP4, MOV, WAV, MP3, etc.)
- **AI Transcription** - Faster-Whisper large-v3 for high accuracy
- **Speaker Identification** - Automatic diarization with manual refinement
- **Interactive Editor** - Real-time transcript editing with media sync
- **Smart Clipping** - Extract precise segments with context
- **Multiple Exports** - SRT, DOCX, PDF Quote Packs, CSV

### Security & Privacy
- **Zero Storage Default** - Process and delete unless explicitly opted-in
- **End-to-End Encryption** - XChaCha20-Poly1305 with per-tenant keys
- **Chain of Custody** - SHA-256 hashing with immutable audit trails
- **Flexible Retention** - 0/7/30/90 day policies per case
- **Air-gapped Workers** - Sandboxed processing with no internet access

### Professional Features
- **Case Management** - Organize by matter/client with role-based access
- **Learning Dictionaries** - Custom terminology and correction rules
- **Audit Reports** - Complete provenance tracking for legal admissibility
- **Quality Metrics** - Confidence scoring and accuracy indicators

## 📅 Development Timeline

### Phase 1: MVP Foundation (Weeks 1-4)
- [ ] **Project Setup** - Monorepo structure with Next.js frontend, FastAPI backend
- [ ] **Basic Infrastructure** - Docker Compose with Postgres, Redis, MinIO
- [ ] **Core Pipeline** - Audio normalization → ASR → Alignment → Export
- [ ] **Simple UI** - Two-pane player with basic transcript editing
- [ ] **Local Processing** - CPU-based transcription for development

### Phase 2: Production Features (Weeks 5-8)
- [ ] **Security Implementation** - JWT auth, encryption, audit logging
- [ ] **Advanced Pipeline** - Speaker diarization, user dictionaries, corrections
- [ ] **Professional UI** - Dark/light themes, keyboard shortcuts, find/replace
- [ ] **Export System** - Multiple formats with embedded audit data
- [ ] **Case Management** - Multi-tenant architecture with role permissions

### Phase 3: Scale & Polish (Weeks 9-12)
- [ ] **GPU Workers** - CUDA acceleration for production workloads
- [ ] **Advanced Editing** - Speaker renaming, confidence filtering, bulk operations
- [ ] **Quality Assurance** - Golden file testing, performance benchmarks
- [ ] **Documentation** - API docs, admin guides, security procedures
- [ ] **Deployment Ready** - Production infrastructure, monitoring, scaling

### Phase 4: Advanced Features (3-6 months)
- [ ] **Client-Side Encryption** - Browser-only processing with encrypted bundles
- [ ] **Real-time Processing** - Live transcription capabilities
- [ ] **Multi-language Support** - Beyond English-only processing
- [ ] **Court Reporter Integration** - Certified transcript workflows
- [ ] **Advanced Analytics** - Speech patterns, keyword extraction, sentiment analysis

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js UI   │────│   FastAPI       │────│  GPU Workers    │
│   (Browser)     │    │   Gateway       │    │  (Celery)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐             │
         │              │     Redis       │             │
         └──────────────│     Queue       │─────────────┘
                        └─────────────────┘
                                 │
                    ┌─────────────────────────────────┐
                    │        Storage Layer            │
                    │  ┌─────────────┐ ┌─────────────┐ │
                    │  │  Postgres   │ │   MinIO     │ │
                    │  │  (Metadata) │ │  (Objects)  │ │
                    │  └─────────────┘ └─────────────┘ │
                    └─────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd caseprep

# Start development environment
make up

# Run frontend (development)
cd apps/web && npm run dev

# Access application
open http://localhost:3000
```

## 📊 Business Model

**Target Market**: Small to medium law firms, solo practitioners, legal assistants

**Pricing Tiers**: 
- **Starter**: $29/month - 10 hours processing
- **Professional**: $99/month - 50 hours + advanced features  
- **Enterprise**: $299/month - Unlimited + custom integrations

**Revenue Projections**:
- Year 1: $50K ARR (100 customers)
- Year 2: $250K ARR (500 customers) 
- Year 3: $750K ARR (1,200 customers)

## 📚 Documentation

- [Implementation Plan](./IMPLEMENTATION_PLAN.md) - Detailed technical specifications
- [Security Overview](./docs/SECURITY.md) - Privacy, encryption, and compliance
- [Deployment Guide](./docs/DEPLOYMENT.md) - Infrastructure and scaling
- [Architectural Decisions](./docs/DECISIONS.md) - Key design choices
- [Future Options](./docs/OPTIONS.md) - Alternative approaches and enhancements

## 💡 Core Principles

1. **Privacy First** - No data stored by default, user controls all retention
2. **Accuracy Over Speed** - Legal-grade transcription quality prioritized  
3. **Chain of Custody** - Complete audit trails for legal admissibility
4. **Self-Hostable** - Full control over sensitive legal data
5. **Professional Grade** - Built for legal industry standards and workflows

---

**Status**: Active Development | **License**: Commercial | **Contact**: [Your Contact Info]