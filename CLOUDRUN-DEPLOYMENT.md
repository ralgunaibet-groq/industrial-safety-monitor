# 🚀 Google Cloud Run Deployment Guide

Deploy your Industrial Safety Monitor to Google Cloud Run with full features preserved!

---

## ✨ Why Cloud Run?

- ✅ **Generous Free Tier**: 2 million requests/month free
- ✅ **Auto-scaling**: Scales to zero when not in use
- ✅ **Fast**: Global CDN and edge locations
- ✅ **WebSocket Support**: Full duplex communication
- ✅ **Docker Support**: Uses your existing Dockerfile
- ✅ **Pay-per-use**: Only pay when requests are being processed

---

## 📋 Prerequisites

1. **Google Cloud Account**
   - Sign up at [cloud.google.com](https://cloud.google.com)
   - $300 free credit for 90 days
   - Free tier continues after trial

2. **Install Google Cloud SDK**
   ```bash
   # macOS
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   
   # Or with Homebrew
   brew install --cask google-cloud-sdk
   ```

3. **Project Setup**
   ```bash
   # Initialize gcloud
   gcloud init
   
   # Create new project (or use existing)
   gcloud projects create industrial-safety-monitor --name="Industrial Safety Monitor"
   
   # Set project
   gcloud config set project industrial-safety-monitor
   
   # Enable required APIs
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

---

## 🚀 Deployment Methods

### **Method 1: One-Command Deploy (Easiest)**

```bash
cd "/Users/ralgubaibet/Desktop/Video Analytics"

# Deploy directly from source
gcloud run deploy industrial-safety-monitor \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10
```

**That's it!** Cloud Run will:
1. Build your Docker image
2. Push to Container Registry
3. Deploy to Cloud Run
4. Give you a URL like: `https://industrial-safety-monitor-xxx-uc.a.run.app`

---

### **Method 2: Build & Deploy Separately**

```bash
cd "/Users/ralgubaibet/Desktop/Video Analytics"

# 1. Build the container
gcloud builds submit --tag gcr.io/industrial-safety-monitor/app

# 2. Deploy to Cloud Run
gcloud run deploy industrial-safety-monitor \
  --image gcr.io/industrial-safety-monitor/app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300
```

---

### **Method 3: Using Cloud Build (CI/CD)**

The `cloudbuild.yaml` file is already configured. Deploy with:

```bash
# Trigger build and deploy
gcloud builds submit --config cloudbuild.yaml
```

---

## ⚙️ Configuration Options

### **Memory & CPU**

Adjust based on your needs:

```bash
# Minimum (cheaper, slower)
--memory 1Gi --cpu 1

# Recommended (balanced)
--memory 2Gi --cpu 2

# Maximum (faster, more expensive)
--memory 4Gi --cpu 4
```

### **Scaling**

```bash
# Auto-scale between 0-10 instances
--min-instances 0 --max-instances 10

# Keep 1 instance always warm (no cold starts)
--min-instances 1 --max-instances 10
```

### **Timeout**

```bash
# Default: 300 seconds (5 minutes)
--timeout 300

# Maximum: 3600 seconds (1 hour)
--timeout 3600
```

### **Region**

Choose closest to your users:

```bash
--region us-central1      # Iowa (default)
--region us-east1         # South Carolina
--region us-west1         # Oregon
--region europe-west1     # Belgium
--region asia-northeast1  # Tokyo
```

---

## 🔐 Environment Variables

Set your Groq API key as a secret:

```bash
# Create secret
echo -n "your_groq_api_key" | gcloud secrets create groq-api-key --data-file=-

# Grant Cloud Run access to secret
gcloud secrets add-iam-policy-binding groq-api-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Deploy with secret
gcloud run deploy industrial-safety-monitor \
  --source . \
  --update-secrets=GROQ_API_KEY=groq-api-key:latest \
  --region us-central1
```

---

## 📊 Monitoring & Logs

### **View Logs**

```bash
# Stream logs in real-time
gcloud run services logs tail industrial-safety-monitor --region us-central1

# View logs in Cloud Console
gcloud run services describe industrial-safety-monitor --region us-central1
```

### **Metrics**

View in Cloud Console:
- Request count
- Request latency
- Container CPU/Memory usage
- Error rate
- Billable time

---

## 💰 Cost Estimation

**Free Tier (per month):**
- 2 million requests
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds

**After free tier:**
- $0.40 per million requests
- $0.00002400 per GB-second
- $0.00001000 per vCPU-second

**Example cost for 10,000 requests/month:**
- Usually **FREE** (within free tier)

---

## 🔧 Update Deployment

After making code changes:

```bash
# Quick update
gcloud run deploy industrial-safety-monitor \
  --source . \
  --region us-central1

# Or with specific image
gcloud builds submit --tag gcr.io/industrial-safety-monitor/app
gcloud run deploy industrial-safety-monitor \
  --image gcr.io/industrial-safety-monitor/app \
  --region us-central1
```

---

## 🌐 Custom Domain

Add your own domain:

```bash
# Map domain
gcloud run domain-mappings create \
  --service industrial-safety-monitor \
  --domain your-domain.com \
  --region us-central1

# Follow DNS instructions provided
```

---

## 🛑 Delete Service

To stop charges:

```bash
# Delete Cloud Run service
gcloud run services delete industrial-safety-monitor --region us-central1

# Delete container images
gcloud container images delete gcr.io/industrial-safety-monitor/app
```

---

## 🐛 Troubleshooting

### **Error: Permission Denied**
```bash
# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### **Error: Out of Memory**
```bash
# Increase memory
gcloud run services update industrial-safety-monitor \
  --memory 4Gi \
  --region us-central1
```

### **Cold Starts Too Slow**
```bash
# Keep 1 instance warm
gcloud run services update industrial-safety-monitor \
  --min-instances 1 \
  --region us-central1
```

### **Timeout Errors**
```bash
# Increase timeout
gcloud run services update industrial-safety-monitor \
  --timeout 600 \
  --region us-central1
```

---

## 📝 Important Notes

### **Webcam Access**
- ❌ Cloud Run cannot access local webcams
- ✅ Use IP cameras or RTSP streams
- ✅ Modify `app.py` to use network cameras:

```python
# Replace:
camera = cv2.VideoCapture(0)

# With:
camera = cv2.VideoCapture('rtsp://camera-ip:554/stream')
```

### **WebSocket Support**
- ✅ Cloud Run supports WebSockets
- ✅ Your Socket.IO implementation works out of the box
- ✅ No additional configuration needed

### **Persistent Storage**
- ❌ Cloud Run is stateless
- ✅ Use Cloud Storage for persistent files
- ✅ `speech.wav` is regenerated each time (no issue)

---

## 🎯 Complete Deployment Example

```bash
# 1. Navigate to project
cd "/Users/ralgubaibet/Desktop/Video Analytics"

# 2. Set up GCP
gcloud config set project industrial-safety-monitor
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# 3. Deploy!
gcloud run deploy industrial-safety-monitor \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10

# 4. Get your URL
gcloud run services describe industrial-safety-monitor \
  --region us-central1 \
  --format 'value(status.url)'
```

---

## ✅ Checklist

- [ ] Google Cloud account created
- [ ] gcloud CLI installed
- [ ] Project created and set
- [ ] APIs enabled
- [ ] Code deployed
- [ ] Service is running
- [ ] URL accessible
- [ ] Login with Groq API key works
- [ ] (Optional) Custom domain configured
- [ ] (Optional) Monitoring set up

---

## 🆘 Need Help?

- **Cloud Run Docs**: [cloud.google.com/run/docs](https://cloud.google.com/run/docs)
- **Pricing**: [cloud.google.com/run/pricing](https://cloud.google.com/run/pricing)
- **Support**: [cloud.google.com/support](https://cloud.google.com/support)

---

**Your app is now deployed on Google Cloud Run with all features intact!** 🎉

