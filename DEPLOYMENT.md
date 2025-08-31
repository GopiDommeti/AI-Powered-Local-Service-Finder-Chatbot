# 🚀 Deployment Guide - Local Service Finder Bot

## 📋 **Pre-Deployment Checklist**

### ✅ **Essential Files**
- [ ] `app.py` - Main application
- [ ] `vector_db.py` - Database operations
- [ ] `requirements.txt` - Dependencies
- [ ] `real_justdial_comprehensive.json` - Service data
- [ ] `.env` - Environment variables (create manually)
- [ ] `README.md` - Documentation

### ✅ **API Keys Required**
- [ ] **GEMINI_API_KEY** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- [ ] **FIRECRAWL_API_KEY** - Get from [Firecrawl.dev](https://firecrawl.dev) (optional)

---

## 🌐 **Deployment Options**

### 1. **Streamlit Cloud (Recommended)**

#### **Step 1: Prepare Repository**
```bash
# Create GitHub repository
git init
git add .
git commit -m "Initial commit: Local Service Finder Bot"
git remote add origin https://github.com/yourusername/service-finder-bot.git
git push -u origin main
```

#### **Step 2: Deploy to Streamlit Cloud**
1. Visit [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select repository: `yourusername/service-finder-bot`
4. Set main file: `app.py`
5. Add environment variables:
   ```
   GEMINI_API_KEY = your_actual_gemini_api_key
   FIRECRAWL_API_KEY = your_actual_firecrawl_key
   ```
6. Click "Deploy"

#### **Step 3: Custom Domain (Optional)**
- Configure custom domain in Streamlit Cloud settings
- Update DNS records as instructed

---

### 2. **Local Production Server**

#### **Step 1: Setup Environment**
```bash
# Create virtual environment
python -m venv service_finder_env
source service_finder_env/bin/activate  # Linux/Mac
# OR
service_finder_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### **Step 2: Configure Environment**
```bash
# Create .env file
echo "GEMINI_API_KEY=your_gemini_api_key" > .env
echo "FIRECRAWL_API_KEY=your_firecrawl_key" >> .env
```

#### **Step 3: Run Production Server**
```bash
# Run with custom port and host
streamlit run app.py --server.port 8080 --server.address 0.0.0.0

# Or with specific configuration
streamlit run app.py \
  --server.port 8080 \
  --server.address 0.0.0.0 \
  --server.maxUploadSize 50 \
  --server.maxMessageSize 50
```

---

### 3. **Docker Deployment**

#### **Step 1: Create Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directory for ChromaDB
RUN mkdir -p chroma_db

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run application
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

#### **Step 2: Build and Run**
```bash
# Build Docker image
docker build -t service-finder-bot .

# Run container
docker run -p 8501:8501 \
  -e GEMINI_API_KEY=your_key \
  -e FIRECRAWL_API_KEY=your_key \
  service-finder-bot
```

#### **Step 3: Docker Compose (Optional)**
```yaml
version: '3.8'
services:
  service-finder:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
    volumes:
      - ./chroma_db:/app/chroma_db
    restart: unless-stopped
```

---

### 4. **Cloud Platforms**

#### **Heroku Deployment**
```bash
# Create Procfile
echo "web: streamlit run app.py --server.port \$PORT --server.address 0.0.0.0" > Procfile

# Deploy to Heroku
heroku create your-service-finder-app
heroku config:set GEMINI_API_KEY=your_key
heroku config:set FIRECRAWL_API_KEY=your_key
git push heroku main
```

#### **Railway Deployment**
```bash
# railway.json
{
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT --server.address 0.0.0.0"
  }
}
```

#### **DigitalOcean App Platform**
```yaml
# .do/app.yaml
name: service-finder-bot
services:
- name: web
  source_dir: /
  github:
    repo: yourusername/service-finder-bot
    branch: main
  run_command: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: GEMINI_API_KEY
    value: your_key
    type: SECRET
```

---

## 🔧 **Configuration Options**

### **Streamlit Configuration**
Create `.streamlit/config.toml`:
```toml
[server]
port = 8501
address = "0.0.0.0"
maxUploadSize = 50
maxMessageSize = 50

[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[browser]
gatherUsageStats = false
```

### **Environment Variables**
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

---

## 📊 **Monitoring & Maintenance**

### **Health Checks**
```python
# Add to app.py for monitoring
import streamlit as st

def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "database": "connected" if st.session_state.get('vector_db') else "disconnected",
        "ai_model": "ready" if st.session_state.get('model') else "not_ready"
    }
```

### **Logging Setup**
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('service_finder.log'),
        logging.StreamHandler()
    ]
)
```

### **Performance Monitoring**
```python
# Add performance tracking
import time

def track_search_performance(start_time, num_results):
    duration = time.time() - start_time
    logging.info(f"Search completed: {num_results} results in {duration:.2f}s")
```

---

## 🔐 **Security Considerations**

### **API Key Security**
- ✅ Use environment variables (never hardcode keys)
- ✅ Add `.env` to `.gitignore`
- ✅ Use different keys for development and production
- ✅ Regularly rotate API keys

### **Data Protection**
- ✅ No personal data storage (only service information)
- ✅ Location data handled client-side only
- ✅ No sensitive user information logged
- ✅ HTTPS enforcement in production

---

## 📈 **Scaling Recommendations**

### **For High Traffic**
1. **Upgrade Gemini Plan**: Move from free tier to paid plan
2. **Database Optimization**: Consider PostgreSQL + pgvector for larger datasets
3. **Caching Layer**: Add Redis for frequent queries
4. **Load Balancing**: Multiple app instances behind load balancer

### **For Enterprise Use**
1. **Custom Domain**: Professional domain name
2. **Authentication**: Add user login and personalization
3. **Analytics**: Google Analytics or custom tracking
4. **Backup Strategy**: Regular database backups

---

## 🎯 **Go-Live Checklist**

### **Final Steps Before Launch**
- [ ] Test all features (search, location, contact, export)
- [ ] Verify API keys are working
- [ ] Check mobile responsiveness
- [ ] Test Google Maps integration
- [ ] Validate WhatsApp and call links
- [ ] Review error handling
- [ ] Test export functionality
- [ ] Verify location detection
- [ ] Check conversational AI responses
- [ ] Ensure data is loading correctly

### **Post-Launch Monitoring**
- [ ] Monitor API usage and costs
- [ ] Track user engagement
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Gather user feedback
- [ ] Plan feature updates

---

## 🎉 **Congratulations!**

Your **Local Service Finder Bot** is now **production-ready** with:
- ✅ **22 Complete Features**
- ✅ **Professional UI/UX**
- ✅ **AI-Powered Intelligence**
- ✅ **Location-Based Services**
- ✅ **Multiple Contact Methods**
- ✅ **Export Capabilities**
- ✅ **Comprehensive Documentation**

**Ready to help users find local services with style!** 🚀🌟
