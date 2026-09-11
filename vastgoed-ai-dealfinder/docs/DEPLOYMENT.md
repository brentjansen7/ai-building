# Deployment Guide — Vastgoed AI Dealfinder

---

## 🚀 Option 1: Railway (Aanbevolen - Gemakkelijks)

Railway host automatisch FastAPI, PostgreSQL, Redis, en workers.

### Stappen

1. **Account aanmaken**
   ```bash
   # https://railway.app
   npm install -g @railway/cli
   railway login
   ```

2. **Project initialiseren**
   ```bash
   railway new
   # Selecteer: Node.js (voor worker) + PostgreSQL + Redis
   ```

3. **Backend uploaden**
   ```bash
   # Voeg Dockerfile toe aan backend
   railway add
   # Selecteer: vastgoed-ai-dealfinder/backend
   ```

4. **Environment variables stellen**
   ```bash
   railway variables set ANTHROPIC_API_KEY=sk-ant-...
   railway variables set TELEGRAM_TOKEN=...
   railway variables set DISCORD_WEBHOOK_URL=...
   ```

5. **Deploy**
   ```bash
   railway deploy
   ```

6. **Chrome Extension configureren**
   ```
   API Endpoint: https://your-railway-app.railway.app
   API Key: (je EXTENSION_API_KEY uit .env)
   ```

**Voordelen:**
- ✅ Zero-config deployment
- ✅ Automatic scaling
- ✅ Built-in monitoring
- ✅ $5-10/maand

---

## 🛠️ Option 2: VPS (Hetzner / DigitalOcean)

Voor meer controle en lagere kosten op schaal.

### Vereisten
- 4GB RAM (8GB+ aanbevolen)
- 2 vCPU
- 50GB SSD
- Ubuntu 22.04 LTS

### Setup

1. **SSH in je server**
   ```bash
   ssh root@your-vps-ip
   ```

2. **Update systeem**
   ```bash
   apt update && apt upgrade -y
   apt install -y curl git docker.io docker-compose
   usermod -aG docker $USER
   ```

3. **Clone repo**
   ```bash
   git clone https://github.com/brent/vastgoed-ai-dealfinder
   cd vastgoed-ai-dealfinder
   ```

4. **Setup environment**
   ```bash
   cp backend/.env.example backend/.env
   nano backend/.env
   # Vul je API keys in
   ```

5. **Start services**
   ```bash
   cd deploy
   docker-compose up -d

   # Controleer status
   docker-compose ps
   docker-compose logs -f api
   ```

6. **Nginx SSL setup (gratis via Let's Encrypt)**
   ```bash
   apt install -y certbot python3-certbot-nginx
   certbot certonly --nginx -d yourdomain.com

   # Update nginx.conf met SSL certs
   ```

### Monitoring

```bash
# Logs bekijken
docker-compose logs api
docker-compose logs worker
docker-compose logs scheduler

# Database backup
docker exec vastgoed-postgres pg_dump \
  -U vastgoed_user vastgoed_ai > backup.sql
```

### Performance Tuning

**PostgreSQL** (`deploy/postgres-init.sql`):
```sql
-- Verhoog cache voor meer speed
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
```

**Redis** (`deploy/redis.conf`):
```
maxmemory 512mb
maxmemory-policy allkeys-lru
```

---

## 🐳 Option 3: Docker Swarm (Multi-Node Scaling)

Voor high-availability setup met meerdere machines.

```bash
# Op manager node
docker swarm init

# Op worker nodes
docker swarm join --token SWMTKN-... manager-ip:2377

# Deploy stack
docker stack deploy -c docker-compose.yml vastgoed
```

---

## 📱 Option 4: Kubernetes (Enterprise)

Voor massieve schaling (100K+ listings/day).

```bash
# Install kubectl + helm
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml

# Auto-scaling op CPU > 70%
kubectl autoscale deployment api --min=2 --max=5
```

---

## 🔒 Security Checklist

- [ ] SSL/TLS certificates (Let's Encrypt)
- [ ] Firewall: Open port 80, 443 only
- [ ] API key rotation (30 dagen)
- [ ] Database password 30+ characters
- [ ] Redis password enabled (`requirepass`)
- [ ] No debug mode in production
- [ ] Logging: No sensitive data
- [ ] Rate limiting enabled
- [ ] DDoS protection (Cloudflare / WAF)
- [ ] Backups automated (daily)

---

## 🔄 CI/CD Pipeline

### GitHub Actions (Recommended)

Bestand: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build Docker image
        run: |
          docker build -t vastgoed-api:${{ github.sha }} backend/

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login \
            -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push vastgoed-api:${{ github.sha }}

      - name: Deploy to VPS
        run: |
          ssh deploy@your-vps-ip \
            "docker pull vastgoed-api:${{ github.sha }} && \
             docker-compose up -d"
```

---

## 📊 Monitoring & Alerts

### Prometheus + Grafana

```bash
# Docker Compose voeg toe:
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
```

Dashboards:
- API response time
- Database query latency
- Worker job queue length
- Disk usage
- Memory usage

### Sentry (Error Tracking)

```python
# backend/app/main.py
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-sentry-key@sentry.io/123456",
    environment="production",
    traces_sample_rate=0.1,
)
```

---

## 🚨 Maintenance

### Daily
- Monitor error rates (target: <0.1%)
- Check API response times (target: <2s)
- Verify scraper jobs completed

### Weekly
- Review deal distribution (should be balanced)
- Check database disk usage
- Rotate API keys

### Monthly
- Database optimization (`VACUUM ANALYZE`)
- Review & update proxy list
- Update dependencies (`pip list --outdated`)
- Backup restoration test

### Quarterly
- Performance benchmarking
- Load testing (simulate 1000 concurrent users)
- Security audit
- Contractor price data refresh

---

## 💰 Cost Estimates (Monthly)

| Option | CPU | RAM | Storage | Price |
|--------|-----|-----|---------|-------|
| Railway | Shared | 1GB | 5GB | $5-20 |
| Hetzner VPS | 2vCPU | 4GB | 40GB | $10 |
| DigitalOcean | 2vCPU | 4GB | 80GB | $24 |
| AWS EC2 | 2vCPU | 4GB | 100GB | $40-80 |
| Google Cloud | 2vCPU | 4GB | 100GB | $50-100 |

**Aanvullende kosten:**
- LLM API (Claude): ~$0.01-0.10 per analyse (variabel)
- Proxy service: $20-50/maand (Bright Data)
- Domain: $10-15/jaar

---

## 🔧 Troubleshooting

### API geeft 502 Bad Gateway

```bash
# Controleer container logs
docker-compose logs api

# Restart API
docker-compose restart api

# Check database connection
docker exec vastgoed-api \
  python -c "from app.database import engine; print(engine.url)"
```

### Scraper blijft steken

```bash
# Check RQ worker status
docker-compose logs worker

# Lees failed jobs
redis-cli LRANGE rq:failed:default 0 -1

# Restart worker
docker-compose restart worker
```

### Chrome Extension geeft API error

1. Controleer API URL in extension instellingen
2. Controleer API key (moet matchen in `.env`)
3. Controleer CORS headers
4. Browser console: `Ctrl+Shift+J` → check errors

### Database full

```bash
# Check disk usage
docker exec vastgoed-postgres df -h

# Vacuum tables
docker exec vastgoed-postgres \
  vacuumdb -U vastgoed_user vastgoed_ai

# Archive oude analyses
DELETE FROM analyses
WHERE created_at < NOW() - INTERVAL '90 days';
```

---

## 📈 Scaling Strategy

### Tot 10K listings/dag

- **Single VPS** (4GB RAM)
- 2 worker processes
- Basic monitoring

### Tot 100K listings/dag

- **VPS Cluster** (3x machines)
  - 1x API server
  - 2x worker servers
  - Shared PostgreSQL (separate instance)
  - Redis cluster
- Auto-scaling workers op job queue length

### Tot 1M listings/dag

- **Kubernetes cluster** (AWS EKS)
  - Managed PostgreSQL (AWS RDS)
  - Managed Redis (AWS ElastiCache)
  - Auto-scaling API pods (HPA)
  - Distributed workers (50+ pods)
  - CDN voor images (CloudFront)

---

## 🚀 Launch Checklist

- [ ] Domain configured
- [ ] SSL certificate installed
- [ ] API keys alle geconfigureerd
- [ ] Database backups ingesteld
- [ ] Monitoring alerts enabled
- [ ] Chrome extension tested
- [ ] Rate limiting enabled
- [ ] Proxy rotation working
- [ ] Alerts (Telegram/Discord) tested
- [ ] Documentation up-to-date
- [ ] Logging configured
- [ ] Database indexes verified
- [ ] Load testing passed
- [ ] Security audit completed
- [ ] Team trained on deployment

---

## 🎓 Post-Launch Monitoring (First Week)

Monitor intensief:
- API error rate (aim: <0.1%)
- Average response time (aim: <2s)
- Scraper success rate (aim: >95%)
- Database performance
- Memory/CPU usage
- Deal alert accuracy

Adjust thresholds op basis van werkelijke data.
