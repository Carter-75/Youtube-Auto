# 🎵 Automated Lo-Fi YouTube Channel Generator

**Windows Only** | Fully automated system for generating and uploading lo-fi study music videos to YouTube using AI.

---

## What This Does

This automation pipeline:

1. **Generates lo-fi music** using Suno API
2. **Downloads audio** as MP3
3. **Creates metadata** (title, description, tags) using OpenAI GPT-4
4. **Generates thumbnail** (1280x720) using DALL-E 3
5. **Creates video** from audio + thumbnail using FFmpeg
6. **Uploads to YouTube** with all metadata (set to private)
7. **Saves metadata** locally as JSON

**Smart Features:**
- ✅ Keeps PC awake during generation (3-5 min per video)
- ✅ Lets PC sleep during delays between videos
- ✅ Independent wake lock (won't conflict with other projects)
- ✅ Timestamps all files to prevent duplicates
- ✅ Error handling with retry logic

---

## Setup

### 1. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Install FFmpeg

```powershell
winget install ffmpeg
```

After installation, restart your terminal.

### 3. Configure API Keys

Copy the template:
```powershell
Copy-Item env_template.txt .env
```

Edit `.env` and add your API keys:

**Suno API** (https://suno.ai)
- Sign up, subscribe to a plan, generate API key

**OpenAI API** (https://platform.openai.com/api-keys)
- Create account, generate API key

**YouTube Data API** (https://console.cloud.google.com)
1. Create Google Cloud project
2. Enable "YouTube Data API v3"
3. Create OAuth credentials (Desktop app)
4. Copy Client ID and Client Secret to `.env`
5. Leave `YOUTUBE_REFRESH_TOKEN` empty (will be generated on first run)

Your `.env` should look like:
```env
SUNO_API_KEY=your_actual_suno_key
OPENAI_API_KEY=sk-your_actual_openai_key
YOUTUBE_CLIENT_ID=your_google_client_id
YOUTUBE_CLIENT_SECRET=your_google_client_secret
YOUTUBE_REFRESH_TOKEN=
```

### 4. Verify Setup

```powershell
python check_setup.py
```

---

## Run

### Single Video (Admin Mode)

**Right-click** `run_admin.bat` → **Run as administrator**

OR from PowerShell (as admin):

```powershell
cd "C:\path\to\Youtube-Auto"
.\run_admin.bat
```

### Multiple Videos (Admin Mode)

**Right-click** `run_admin_loop.bat` → **Run as administrator**

You'll be prompted for:
- Number of videos to generate (e.g., `5`)
- Delay between videos in seconds (e.g., `120`)

OR from PowerShell (as admin):

```powershell
cd "C:\path\to\Youtube-Auto"
.\run_admin_loop.bat
```

### Manual Run (No Admin)

If you don't need wake lock (system may sleep during generation):

```powershell
# Single video
python runner.py

# Multiple videos
cd src
python main.py --loop 5        # 5 videos, 60 sec delay
python main.py --loop 10 120   # 10 videos, 120 sec delay
```

---

## Output

Generated files are saved to:
- **Audio**: `audio/` folder (`.mp3` and `.mp4` files)
- **Thumbnails**: `thumbnails/` folder (`.png` files, 1280x720)
- **Metadata**: `metadata/` folder (`.json` files)
- **YouTube**: Videos uploaded as **private** (review before publishing)

---

## Wake Lock Behavior

| Phase | System State |
|-------|--------------|
| During video generation (~3-5 min) | 🔒 Awake |
| During delays between videos | 💤 Can sleep |
| After completion | 🔓 Released |

**Note:** Wake lock only works with admin privileges and won't interfere with other applications.

---

## 🔒 Copyright

This code is proprietary and confidential. All rights reserved.

No license is granted for use, modification, or distribution of this code. Any unauthorized use is strictly prohibited.
