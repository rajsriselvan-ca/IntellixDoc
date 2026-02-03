# Deployment Guide - IntellixDoc

This guide will help you deploy IntellixDoc on Oracle Free VM or any other cloud provider.

## Prerequisites

- Oracle Free VM (or any Linux VM)
- Docker and Docker Compose installed
- Domain name (optional, for production)

## Step 1: Prepare Your VM

### Install Docker and Docker Compose

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group (optional)
sudo usermod -aG docker $USER
```

## Step 2: Clone and Configure

```bash
# Clone your repository
git clone <your-repo-url>
cd IntellixDoc

# Create environment file
cat > .env << EOF
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_claude_key_here
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EOF
```

### Get API Keys

1. **Groq (Recommended - Free Tier)**:
   - Visit https://console.groq.com
   - Sign up and get your API key
   - Free tier: 14,400 requests/day

2. **OpenAI**:
   - Visit https://platform.openai.com
   - Get API key (requires credit card)

3. **Anthropic Claude**:
   - Visit https://console.anthropic.com
   - Get API key (requires credit card)

4. **Ollama (Local - No API Key)**:
   - Install Ollama on your VM
   - Run: `ollama pull llama2`
   - Set `LLM_PROVIDER=ollama`

## Step 3: Build and Start Services

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Check service status
docker-compose ps
```

## Step 4: Configure Firewall

```bash
# Allow ports (if using UFW)
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8000/tcp  # Backend API
sudo ufw allow 22/tcp    # SSH
sudo ufw enable
```

## Step 5: Access Your Application

- Frontend: http://your-vm-ip:3000
- Backend API: http://your-vm-ip:8000
- API Docs: http://your-vm-ip:8000/docs

## Step 6: Production Setup (Optional)

### Using Nginx as Reverse Proxy

```bash
# Install Nginx
sudo apt-get install nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/intellixdoc
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/intellixdoc /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Step 7: Monitoring and Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d
```

### Backup Database

```bash
# Backup SQLite database
docker-compose exec backend cp rag.db rag.db.backup

# Backup Qdrant data (stored in volume)
docker run --rm -v intellixdoc_qdrant_storage:/data -v $(pwd):/backup alpine tar czf /backup/qdrant-backup.tar.gz /data
```

## Troubleshooting

### Services Not Starting

```bash
# Check service status
docker-compose ps

# Check logs for errors
docker-compose logs backend
docker-compose logs worker

# Verify environment variables
docker-compose exec backend env | grep LLM
```

### Redis Connection Issues

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Qdrant Connection Issues

```bash
# Check Qdrant health
curl http://localhost:6333/health
```

### Worker Not Processing Jobs

```bash
# Check worker logs
docker-compose logs worker

# Check Redis queue
docker-compose exec redis redis-cli
> KEYS *
> LLEN rq:queue:default
```

## Performance Optimization

### For Oracle Free VM (Limited Resources)

1. **Reduce Worker Instances**: Edit `docker-compose.yml` to use fewer workers
2. **Use Smaller Embedding Model**: Change `EMBEDDING_MODEL` to a smaller model
3. **Limit Concurrent Requests**: Configure Nginx rate limiting
4. **Use Ollama Locally**: Avoid API rate limits

### Resource Monitoring

```bash
# Check resource usage
docker stats

# Check disk space
df -h
docker system df
```

## Security Considerations

1. **Change Default Ports**: Modify ports in `docker-compose.yml`
2. **Use Environment Variables**: Never commit API keys
3. **Enable Authentication**: Add authentication layer for production
4. **Regular Updates**: Keep Docker images updated
5. **Firewall Rules**: Only expose necessary ports

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Review documentation in README.md
- Check GitHub issues

