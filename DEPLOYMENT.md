# 🚀 Deployment Guide - Full Features Preserved

This guide shows how to deploy the **full-featured** Industrial Safety Monitor with real-time video analysis, WebSocket support, and audio alerts.

---

## ⚠️ Important Note About Webcams

Cloud deployments **cannot access your local webcam**. You have two options:

1. **IP Cameras / RTSP Streams** - Modify code to use network cameras
2. **Edge Deployment** - Deploy on a local machine/Raspberry Pi with camera

---

## 🌟 Option 1: Render.com (Recommended - Easiest)

### Features:
- ✅ Free tier (750 hours/month)
- ✅ Docker support
- ✅ WebSocket support
- ✅ Auto-deploy from GitHub
- ✅ HTTPS included

### Steps:

1. **Go to [render.com](https://render.com) and sign up**

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select repository: `industrial-safety-monitor`

3. **Configure Service**
   - Name: `industrial-safety-monitor`
   - Environment: `Docker`
   - Plan: `Free`
   - Click "Create Web Service"

4. **Set Environment Variables** (Optional)
   - In service settings, add:
   - Key: `GROQ_API_KEY`
   - Value: Your API key

5. **Deploy!**
   - Render automatically builds and deploys
   - You'll get a URL like: `https://industrial-safety-monitor.onrender.com`

### Note:
- Free tier sleeps after 15 min of inactivity
- First request after sleep takes ~30 seconds to wake up
- No webcam access (need IP camera modification)

---

## 🚂 Option 2: Railway.app

### Features:
- ✅ $5 free credit/month (~500 hours)
- ✅ Docker support
- ✅ WebSocket support
- ✅ Fast deployments

### Steps:

1. **Go to [railway.app](https://railway.app) and sign up**

2. **New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `industrial-safety-monitor`

3. **Configure**
   - Railway auto-detects Dockerfile
   - Add environment variable: `GROQ_API_KEY` (optional)

4. **Generate Domain**
   - Go to Settings → Generate Domain
   - You'll get: `https://your-app.up.railway.app`

5. **Deploy!**
   - Automatic deployment on every push

---

## ✈️ Option 3: Fly.io (Most Control)

### Features:
- ✅ Free tier (3 shared VMs)
- ✅ Global deployment
- ✅ Full Docker support
- ✅ CLI-based

### Steps:

1. **Install Fly CLI**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Login**
```bash
flyctl auth login
```

3. **Launch App**
```bash
cd "/Users/ralgubaibet/Desktop/Video Analytics"
flyctl launch
```

4. **Deploy**
```bash
flyctl deploy
```

5. **Set Secrets** (Optional)
```bash
flyctl secrets set GROQ_API_KEY=your_api_key
```

6. **Open App**
```bash
flyctl open
```

---

## 🏠 Option 4: Self-Host (Best for Webcam Access)

### A. Oracle Cloud (Always Free)

**Free Forever:**
- 2 VMs with 1GB RAM each
- 200GB storage
- 10TB bandwidth/month

**Steps:**
1. Sign up at [oracle.com/cloud/free](https://www.oracle.com/cloud/free/)
2. Create Ubuntu instance
3. SSH into instance
4. Install Docker:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```
5. Clone and run:
```bash
git clone https://github.com/ralgunaibet-groq/industrial-safety-monitor.git
cd industrial-safety-monitor
sudo docker-compose up -d
```

### B. Local Machine / Raspberry Pi

**Best for actual webcam monitoring:**

```bash
# Clone repo
git clone https://github.com/ralgunaibet-groq/industrial-safety-monitor.git
cd industrial-safety-monitor

# Option 1: Docker
docker-compose up -d

# Option 2: Native
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Expose to internet with:**
- [ngrok](https://ngrok.com): `ngrok http 8080`
- [Tailscale](https://tailscale.com): Secure VPN
- Port forwarding on router (less secure)

---

## 🎯 Comparison Table

| Platform | Free Tier | Webcam | WebSocket | Docker | Ease |
|----------|-----------|--------|-----------|--------|------|
| **Render** | 750h/mo | ❌ | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Railway** | $5 credit | ❌ | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Fly.io** | 3 VMs | ❌ | ✅ | ✅ | ⭐⭐⭐⭐ |
| **Oracle Cloud** | Forever | ✅* | ✅ | ✅ | ⭐⭐⭐ |
| **Local + ngrok** | Free | ✅ | ✅ | ✅ | ⭐⭐⭐⭐ |

*With USB camera or IP camera

---

## 🔧 Modifying for IP Cameras

If you want to use cloud deployment with IP cameras, modify `app.py`:

```python
# Replace this line:
camera = cv2.VideoCapture(0)

# With this (for RTSP stream):
camera = cv2.VideoCapture('rtsp://username:password@camera-ip:554/stream')

# Or for HTTP stream:
camera = cv2.VideoCapture('http://camera-ip:8080/video')
```

---

## 💡 My Recommendation

### For Development/Testing:
**Run locally** with `python app.py`

### For Demo/Sharing:
**Render.com** - Easiest, free, works great

### For Production with Webcam:
**Oracle Cloud** or **Local + ngrok**

### For Production with IP Cameras:
**Railway.app** or **Fly.io**

---

## 📝 Files Included

- `render.yaml` - Render.com configuration
- `.fly.toml` - Fly.io configuration  
- `Dockerfile` - Works with all platforms
- `docker-compose.yml` - Local deployment

---

## 🆘 Need Help?

- Render: [render.com/docs](https://render.com/docs)
- Railway: [docs.railway.app](https://docs.railway.app)
- Fly.io: [fly.io/docs](https://fly.io/docs)

---

**Choose the platform that fits your needs and deploy with confidence! All core features are preserved.** 🚀

