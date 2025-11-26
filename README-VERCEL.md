# 🚀 Vercel Deployment Guide

## ⚠️ Important Differences

The Vercel version is **fundamentally different** from the local version:

### Local Version (Original)
- ✅ Real-time webcam streaming
- ✅ Continuous monitoring (0.5s intervals)
- ✅ Audio alerts
- ✅ WebSocket connections
- ❌ Requires local machine

### Vercel Version (API-Only)
- ✅ Upload images for analysis
- ✅ Serverless API
- ✅ No infrastructure needed
- ❌ No real-time streaming
- ❌ No webcam access
- ❌ No audio alerts

---

## 📦 Files for Vercel

```
api/
├── index.py          # API info endpoint
└── analyze.py        # Image analysis endpoint

public/
└── index.html        # Upload interface

vercel.json           # Vercel configuration
requirements-vercel.txt  # Minimal dependencies (no OpenCV)
```

---

## 🚀 Deploy to Vercel

### Option 1: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd "/Users/ralgubaibet/Desktop/Video Analytics"
vercel --prod
```

### Option 2: GitHub Integration

1. Push to GitHub:
```bash
git add api/ public/ vercel.json requirements-vercel.txt README-VERCEL.md
git commit -m "Add Vercel-compatible API version"
git push origin main
```

2. Go to [vercel.com](https://vercel.com)
3. Click "Import Project"
4. Select your GitHub repo
5. Click "Deploy"

---

## 🔧 Configuration

Vercel will automatically:
- Detect Python serverless functions in `api/`
- Serve static files from `public/`
- Use `requirements-vercel.txt` for dependencies

---

## 📡 API Endpoints

Once deployed, you'll have:

### `GET /api/index`
Returns API information

### `POST /api/analyze`
Analyzes an uploaded image

**Request:**
```json
{
  "api_key": "your_groq_api_key",
  "image": "base64_encoded_image"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "hazard_present": true,
    "severity": "high",
    "hazard_types": ["No PPE", "Near machinery"],
    "description": "Worker without helmet near forklift",
    "recommended_actions": ["Wear proper PPE"]
  }
}
```

---

## 🌐 Usage

After deployment:

1. Visit your Vercel URL (e.g., `https://your-project.vercel.app`)
2. Enter your Groq API key
3. Upload an image
4. Click "Analyze Image"
5. View results!

---

## 💡 Use Cases

This Vercel version is perfect for:
- ✅ Analyzing photos from industrial sites
- ✅ Batch processing uploaded images
- ✅ Integration with other apps via API
- ✅ Mobile app backend
- ✅ Sharing with team (no installation needed)

---

## ⚙️ Environment Variables (Optional)

You can set a default API key in Vercel:

1. Go to your project settings
2. Add environment variable:
   - Name: `GROQ_API_KEY`
   - Value: `your_api_key`

Then modify `api/analyze.py` to use it as fallback.

---

## 🔄 Switching Between Versions

**For real-time monitoring:** Use the local version
```bash
python app.py
```

**For image analysis API:** Deploy to Vercel
```bash
vercel --prod
```

---

## 📊 Limitations

- ❌ No real-time video streaming
- ❌ No webcam access
- ❌ No audio alerts
- ❌ No WebSocket connections
- ✅ But: Serverless, scalable, and free tier available!

---

## 🎯 Recommendation

**Best approach:** Use both!
- **Local version** for real-time monitoring at industrial sites
- **Vercel API** for analyzing uploaded photos and mobile integration

