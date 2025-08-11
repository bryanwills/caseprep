# CasePrep Deployment & Scaling Guide

> **Infrastructure and scaling architecture for production legal transcription platform**

## Architecture Overview

### Reference Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │  GPU Worker     │
│   (Vercel)      │────│   (FastAPI)     │────│  Pool (Auto)    │
│   Next.js       │    │   + Auth        │    │  CUDA + Celery  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐             │
         │              │   Message       │             │
         └──────────────│   Queue         │─────────────┘
                        │   (Redis)       │
                        └─────────────────┘
                                 │
                    ┌─────────────────────────────────┐
                    │        Storage Tier             │
                    │  ┌─────────────┐ ┌─────────────┐ │
                    │  │  PostgreSQL │ │   MinIO     │ │
                    │  │  (Metadata) │ │ (S3 Objects)│ │
                    │  └─────────────┘ └─────────────┘ │
                    └─────────────────────────────────┘
```

**Data Flow**: Browser → CDN → API → Queue → GPU Workers → Storage → Results → Client notification

## Deployment Options

### Option A: Full Self-Hosted
**Best for**: Maximum control, sensitive data, custom compliance requirements

```yaml
# docker-compose.prod.yml
version: "3.9"
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@yourfirm.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "letsencrypt:/letsencrypt"
    labels:
      - "traefik.enable=true"

  api:
    image: caseprep/api:latest
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/caseprep
      - REDIS_URL=redis://redis:6379/0
      - S3_ENDPOINT=http://minio:9000
      - SECRET_KEY=${API_SECRET_KEY}
      - KMS_PROVIDER=vault
      - VAULT_URL=http://vault:8200
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.caseprep.yourfirm.com`)"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
    depends_on:
      - db
      - redis
      - minio
      - vault

  gpu-worker:
    image: caseprep/worker-gpu:latest
    deploy:
      replicas: 2
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    environment:
      - REDIS_URL=redis://redis:6379/0
      - NVIDIA_VISIBLE_DEVICES=all
    depends_on:
      - redis
```

**Hardware Requirements**:
- **GPU Server**: 2x NVIDIA RTX 4090 or A6000, 128GB RAM, 4TB NVMe SSD
- **Database Server**: 16 vCPU, 64GB RAM, 2TB SSD (PostgreSQL + Redis)
- **Storage**: 10TB+ for media files (expandable)
- **Network**: 10Gbps uplink, dedicated IP ranges

### Option B: Hybrid Cloud
**Best for**: Scalability with cost control, geographic distribution

#### Frontend: Vercel/Netlify
```json
// vercel.json
{
  "build": {
    "env": {
      "NEXT_PUBLIC_API_URL": "https://api.caseprep.yourfirm.com"
    }
  },
  "functions": {
    "app/api/auth/[...nextauth].js": {
      "maxDuration": 30
    }
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "https://app.caseprep.yourfirm.com"
        }
      ]
    }
  ]
}
```

#### API: Cloud Run / ECS / AKS
```yaml
# kubernetes-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: caseprep-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: caseprep-api
  template:
    metadata:
      labels:
        app: caseprep-api
    spec:
      containers:
      - name: api
        image: caseprep/api:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: caseprep-secrets
              key: database-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

#### GPU Workers: Specialized Cloud
- **Lambda Labs**: On-demand A100/H100 instances
- **RunPod**: Serverless GPU with auto-scaling
- **CoreWeave**: Kubernetes-native GPU cloud
- **Paperspace**: Gradient workflows for ML pipelines

### Option C: Enterprise SaaS
**Best for**: Rapid deployment, managed operations, enterprise features

```yaml
# Enterprise architecture
Production:
  Frontend: Multi-region CDN (CloudFlare)
  API: Load-balanced across 3 regions
  Workers: Auto-scaling GPU pools (spot instances)
  Database: RDS Multi-AZ with read replicas
  Storage: S3 with intelligent tiering
  Monitoring: DataDog, PagerDuty integration
  Security: WAF, DDoS protection, compliance audits
```

## GPU Infrastructure

### Self-Hosted GPU Setup

#### Hardware Recommendations
```bash
# High-Performance Setup
GPU: 2-4x NVIDIA RTX 4090 (24GB VRAM each)
CPU: AMD Threadripper PRO or Intel Xeon W (32+ cores)
RAM: 256GB DDR4/DDR5 ECC
Storage: 8TB NVMe SSD (transcription cache) + 32TB HDD (archive)
Network: 25Gbps+ with redundant connections

# Budget-Conscious Setup  
GPU: 1-2x NVIDIA RTX 4060 Ti (16GB VRAM each)
CPU: AMD Ryzen 9 7950X (16 cores)
RAM: 128GB DDR5
Storage: 4TB NVMe + 16TB HDD
Network: 10Gbps
```

#### GPU Worker Docker Configuration
```dockerfile
# Dockerfile.gpu
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY requirements-gpu.txt .
RUN pip install --no-cache-dir -r requirements-gpu.txt

# Install NVIDIA optimized libraries
RUN pip install \
    torch==2.1.0+cu121 \
    torchaudio==2.1.0+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# Copy application code
COPY . .

# Set environment variables
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,video
ENV CUDA_VISIBLE_DEVICES=0,1

# Create non-root user
RUN groupadd -r worker && useradd -r -g worker worker
RUN chown -R worker:worker /app
USER worker

CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=INFO", "-Q", "gpu", "-c", "2"]
```

#### Performance Optimization
```python
# worker/config.py
import torch

class GPUConfig:
    # Optimize for multiple concurrent jobs
    BATCH_SIZE = 16 if torch.cuda.device_count() > 1 else 8
    
    # Memory management
    TORCH_CACHE_SIZE = "2GB"
    CUDA_MEMORY_FRACTION = 0.9
    
    # Model loading
    FASTER_WHISPER_DEVICE = "cuda"
    FASTER_WHISPER_COMPUTE_TYPE = "float16"
    
    # Concurrency settings
    MAX_CONCURRENT_JOBS = torch.cuda.device_count() * 2
    WORKER_PREFETCH_MULTIPLIER = 1

# Memory cleanup after each job
def cleanup_gpu_memory():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
```

### Cloud GPU Options

#### AWS GPU Instances
```yaml
# AWS ECS Task Definition
{
  "family": "caseprep-gpu-worker",
  "requiresAttributes": [
    {
      "name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"
    },
    {
      "name": "ecs.capability.execution-role-aws-logs"
    }
  ],
  "taskRoleArn": "arn:aws:iam::123456789012:role/caseprep-task-role",
  "networkMode": "awsvpc",
  "cpu": "4096",
  "memory": "16384",
  "containerDefinitions": [
    {
      "name": "gpu-worker",
      "image": "caseprep/worker-gpu:latest",
      "resourceRequirements": [
        {
          "type": "GPU",
          "value": "1"
        }
      ],
      "environment": [
        {
          "name": "REDIS_URL",
          "value": "redis://elasticache-cluster:6379"
        }
      ]
    }
  ]
}
```

**Instance Types**:
- **g5.xlarge**: 1x A10G, 4 vCPU, 16GB RAM - $1.006/hour
- **g5.2xlarge**: 1x A10G, 8 vCPU, 32GB RAM - $1.212/hour
- **g5.4xlarge**: 1x A10G, 16 vCPU, 64GB RAM - $1.624/hour
- **g6.xlarge**: 1x L4, 4 vCPU, 16GB RAM - $0.7584/hour (newest)

#### Google Cloud GPU
```yaml
# GKE Node Pool Configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: gpu-worker-config
data:
  node-pool.yaml: |
    name: gpu-pool
    initialNodeCount: 1
    autoscaling:
      enabled: true
      minNodeCount: 0
      maxNodeCount: 10
    config:
      machineType: a2-highgpu-1g
      accelerators:
      - acceleratorCount: 1
        acceleratorType: nvidia-tesla-a100
      preemptible: true  # 70% cost savings
```

**Instance Types**:
- **a2-highgpu-1g**: 1x A100, 12 vCPU, 85GB RAM - $3.673/hour
- **g2-standard-4**: 1x L4, 4 vCPU, 16GB RAM - $0.8524/hour
- **g2-standard-8**: 1x L4, 8 vCPU, 32GB RAM - $1.1886/hour

#### Azure GPU
```yaml
# Azure Container Instances
apiVersion: '2019-12-01'
location: eastus
properties:
  containers:
  - name: gpu-worker
    properties:
      image: caseprep/worker-gpu:latest
      resources:
        requests:
          cpu: 4
          memoryInGb: 16
          gpu:
            count: 1
            sku: V100
      environmentVariables:
      - name: REDIS_URL
        value: caseprep-redis.redis.cache.windows.net:6380
```

**Instance Types**:
- **NC6s_v3**: 1x V100, 6 vCPU, 112GB RAM - $3.168/hour
- **NC4as_T4_v3**: 1x T4, 4 vCPU, 28GB RAM - $0.526/hour

## Auto-Scaling Configuration

### Queue-Based Scaling
```python
# autoscaler.py
import redis
import boto3
from datetime import datetime, timedelta

class WorkerAutoscaler:
    def __init__(self):
        self.redis = redis.Redis(host='redis-cluster')
        self.ecs = boto3.client('ecs')
        self.metrics = boto3.client('cloudwatch')
    
    def get_queue_metrics(self):
        queue_length = self.redis.llen('celery')
        processing_jobs = self.redis.llen('celery:processing')
        
        # Calculate average job time from recent completions
        recent_jobs = self.get_recent_job_metrics()
        avg_job_time = sum(job['duration'] for job in recent_jobs) / len(recent_jobs)
        
        return {
            'queue_length': queue_length,
            'processing_jobs': processing_jobs,
            'avg_job_time_minutes': avg_job_time / 60,
            'estimated_wait_time': (queue_length * avg_job_time) / max(processing_jobs, 1)
        }
    
    def calculate_target_capacity(self, metrics):
        queue_length = metrics['queue_length']
        avg_job_time = metrics['avg_job_time_minutes']
        
        # Target: Process queue within 15 minutes
        target_processing_time = 15
        
        if queue_length == 0:
            return 1  # Keep minimum capacity
        
        required_workers = max(1, min(10, 
            math.ceil(queue_length * avg_job_time / target_processing_time)
        ))
        
        return required_workers
    
    def scale_workers(self, target_capacity):
        current_capacity = self.get_current_worker_count()
        
        if target_capacity > current_capacity:
            self.scale_up(target_capacity - current_capacity)
        elif target_capacity < current_capacity:
            self.scale_down(current_capacity - target_capacity)
    
    def scale_up(self, additional_workers):
        # Launch new ECS tasks or start EC2 instances
        for i in range(additional_workers):
            response = self.ecs.run_task(
                cluster='caseprep-gpu-cluster',
                taskDefinition='caseprep-gpu-worker:latest',
                launchType='EC2'
            )
            print(f"Started worker task: {response['tasks'][0]['taskArn']}")
```

### Cost Optimization
```python
# Spot instance management
class SpotInstanceManager:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
        
    def request_spot_instances(self, count, instance_type='g5.xlarge'):
        # Use spot instances for 70% cost savings
        response = self.ec2.request_spot_instances(
            SpotPrice='0.50',  # Max price per hour
            InstanceCount=count,
            LaunchSpecification={
                'ImageId': 'ami-gpu-worker-123',
                'InstanceType': instance_type,
                'SecurityGroups': ['caseprep-worker-sg'],
                'UserData': base64.b64encode(self.get_user_data().encode()).decode()
            }
        )
        return response
        
    def handle_spot_interruption(self, instance_id):
        # Gracefully drain jobs before instance termination
        self.drain_worker_jobs(instance_id)
        self.notify_autoscaler_of_interruption(instance_id)
```

## Security & Networking

### Network Architecture
```yaml
# VPC Configuration (Terraform)
resource "aws_vpc" "caseprep" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "caseprep-vpc"
  }
}

# Public subnet for load balancers
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.caseprep.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
}

# Private subnet for workers (no internet access)
resource "aws_subnet" "private_workers" {
  vpc_id            = aws_vpc.caseprep.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "us-east-1a"
}

# Security group for GPU workers
resource "aws_security_group" "gpu_workers" {
  name_prefix = "caseprep-gpu-workers"
  vpc_id      = aws_vpc.caseprep.id
  
  # No inbound internet access
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.caseprep.cidr_block]
  }
  
  # Allow outbound to Redis and S3 only
  egress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [aws_subnet.private_data.cidr_block]
  }
  
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # S3 access
  }
}
```

### mTLS Between Services
```yaml
# Certificate management with cert-manager
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: caseprep-api-tls
  namespace: caseprep
spec:
  secretName: caseprep-api-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.caseprep.yourfirm.com
  - worker.caseprep.yourfirm.com
```

## Monitoring & Observability

### Metrics Collection
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Business metrics
TRANSCRIPTION_JOBS = Counter('transcription_jobs_total', 
                           'Total transcription jobs', ['status', 'model'])

PROCESSING_TIME = Histogram('transcription_processing_seconds',
                          'Time spent processing transcriptions',
                          ['model', 'duration_bucket'])

QUEUE_DEPTH = Gauge('transcription_queue_depth',
                   'Number of jobs waiting in queue')

GPU_UTILIZATION = Gauge('gpu_utilization_percent',
                       'GPU utilization percentage', ['gpu_id'])

# System metrics
API_REQUEST_DURATION = Histogram('api_request_duration_seconds',
                                'API request duration', ['method', 'endpoint'])

ACTIVE_CONNECTIONS = Gauge('active_websocket_connections',
                          'Number of active WebSocket connections')

def track_transcription_job(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            TRANSCRIPTION_JOBS.labels(status='success', 
                                    model=kwargs.get('model', 'unknown')).inc()
            return result
        except Exception as e:
            TRANSCRIPTION_JOBS.labels(status='error',
                                    model=kwargs.get('model', 'unknown')).inc()
            raise
        finally:
            processing_time = time.time() - start_time
            PROCESSING_TIME.labels(model=kwargs.get('model', 'unknown'),
                                 duration_bucket=classify_duration(processing_time)).observe(processing_time)
    return wrapper
```

### Logging Configuration
```yaml
# fluentd-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/caseprep-api-*.log
      pos_file /var/log/fluentd-api.log.pos
      tag kubernetes.api
      format json
    </source>
    
    <source>
      @type tail
      path /var/log/containers/caseprep-worker-*.log
      pos_file /var/log/fluentd-worker.log.pos
      tag kubernetes.worker
      format json
    </source>
    
    <filter kubernetes.**>
      @type record_transformer
      <record>
        hostname "#{Socket.gethostname}"
        environment "#{ENV['ENVIRONMENT']}"
      </record>
    </filter>
    
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name caseprep
      type_name _doc
    </match>
```

### Alerting Rules
```yaml
# prometheus-alerts.yaml
groups:
- name: caseprep.rules
  rules:
  - alert: HighQueueDepth
    expr: transcription_queue_depth > 50
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Transcription queue depth is high"
      description: "Queue has {{ $value }} jobs waiting for processing"
      
  - alert: GPUWorkerDown
    expr: up{job="gpu-worker"} == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "GPU worker is down"
      description: "GPU worker {{ $labels.instance }} is not responding"
      
  - alert: HighErrorRate
    expr: rate(transcription_jobs_total{status="error"}[5m]) > 0.1
    for: 3m
    labels:
      severity: warning
    annotations:
      summary: "High transcription error rate"
      description: "Error rate is {{ $value }} errors per second"
```

## Cost Management

### Resource Optimization
```python
# Cost tracking and optimization
class CostOptimizer:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.pricing = boto3.client('pricing', region_name='us-east-1')
        
    def get_hourly_costs(self):
        # Track costs by service component
        costs = {
            'api_servers': self.get_ec2_costs('api'),
            'gpu_workers': self.get_ec2_costs('gpu'),
            'database': self.get_rds_costs(),
            'storage': self.get_s3_costs(),
            'data_transfer': self.get_bandwidth_costs()
        }
        
        total_hourly = sum(costs.values())
        return costs, total_hourly
    
    def optimize_gpu_usage(self):
        # Recommend optimal instance types based on usage patterns
        avg_queue_time = self.get_avg_metric('transcription_queue_depth', '24h')
        avg_job_duration = self.get_avg_metric('transcription_processing_seconds', '24h')
        
        if avg_queue_time < 5 and avg_job_duration < 300:  # 5 minutes
            return "Consider using smaller GPU instances (g5.xlarge vs g5.4xlarge)"
        elif avg_queue_time > 20:
            return "Consider scaling up or using more powerful GPUs"
        
        return "Current GPU configuration appears optimal"
    
    def recommend_spot_instances(self):
        # Analyze job patterns for spot instance suitability
        job_interruption_tolerance = self.analyze_job_fault_tolerance()
        current_spot_savings = self.calculate_spot_savings_potential()
        
        if job_interruption_tolerance > 0.8 and current_spot_savings > 0.5:
            return f"Switch to spot instances for {current_spot_savings*100:.0f}% savings"
        
        return "Spot instances not recommended for current workload"
```

### Billing Alerts
```yaml
# CloudWatch billing alarm
{
  "AlarmName": "CasePrep-MonthlyBilling",
  "AlarmDescription": "Alert when monthly AWS costs exceed threshold",
  "ActionsEnabled": true,
  "AlarmActions": [
    "arn:aws:sns:us-east-1:123456789012:billing-alerts"
  ],
  "MetricName": "EstimatedCharges",
  "Namespace": "AWS/Billing",
  "Statistic": "Maximum",
  "Dimensions": [
    {
      "Name": "Currency",
      "Value": "USD"
    }
  ],
  "Period": 86400,
  "EvaluationPeriods": 1,
  "Threshold": 1000.0,
  "ComparisonOperator": "GreaterThanThreshold"
}
```

---

*This deployment guide provides the foundation for scalable, secure production deployment of CasePrep across various infrastructure configurations, from self-hosted to cloud-native solutions.*