# Audio Device Setup Guide 🎤🔊

Complete guide for setting up virtual audio devices for the Meeting Assistant application. This includes configuration for both system audio capture (transcription) and TTS translation routing on macOS, Windows, and Linux.

## Table of Contents

- [Overview](#overview)
- [What You'll Achieve](#what-youll-achieve)
- [Required Software](#required-software)
- [macOS Complete Setup](#macos-complete-setup)
- [Windows Complete Setup](#windows-complete-setup)
- [Linux Setup](#linux-setup)
- [Meeting Application Configuration](#meeting-application-configuration)
- [Testing Your Setup](#testing-your-setup)
- [Troubleshooting](#troubleshooting)
- [Advanced Configurations](#advanced-configurations)

---

## Overview

This guide helps you set up virtual audio devices for two key features:

### 1. **System Audio Capture** (Transcription)
Capture audio from meeting applications (Zoom, Teams, Telegram, etc.) so the Meeting Assistant can transcribe what other participants say, not just your microphone input.

### 2. **TTS Translation Routing**
Route AI-generated speech translations to your meeting app's microphone input so your conversation partners hear the translation as if you spoke it.

---

## What You'll Achieve

After completing this setup:

✅ **Capture system audio** from meeting apps for transcription  
✅ **Route TTS translations** to meeting app microphone  
✅ **Use your real voice** AND translations simultaneously  
✅ **Hear TTS translations** yourself while they play  
✅ **Your peers hear** both your voice and translations  
✅ **Transcribe all participants** in the meeting  

**Complete Audio Flow:**
```
Your Voice → Real Mic ──────┐
                            ├→ Aggregate Device → Meeting App ──→ Peer hears you + TTS ✅
TTS Audio → Virtual Device ─┘           ↓
            ↓                    (System Audio Output)
   Multi-Output splits:                  ↓
   ├→ Virtual Device Input      Meeting Assistant captures ──→ Transcribes peer ✅
   └→ Your Speakers ──→ You hear TTS + peer ✅
```

---

## Required Software

### macOS

**BlackHole** (Free, Open Source)
- Virtual audio driver for macOS
- Download: https://github.com/ExistentialAudio/BlackHole

**Installation:**
```bash
# Via Homebrew (recommended)
brew install blackhole-2ch
```

**⚠️ Important**: **Restart your Mac** after installation!

### Windows

Choose **ONE** of these:

**VB-Cable** (Free - Recommended for beginners)
- Download: https://vb-audio.com/Cable/
- Simple virtual audio cable
- Run installer as Administrator → Restart Windows

**VoiceMeeter** (Free - Advanced users)
- Download: https://vb-audio.com/Voicemeeter/
- Advanced audio mixer with more control
- Run installer as Administrator → Restart Windows

### Linux

**PulseAudio** (Built-in on most distributions)
```bash
# Create virtual sink
pactl load-module module-null-sink sink_name=virtual_speaker sink_properties=device.description="Virtual_Speaker"
```

---

## macOS Complete Setup

### Step 1: Install BlackHole

Install from [Required Software](#macos) section.

**Verify:**
```bash
system_profiler SPAudioDataType | grep -i blackhole
```

### Step 2: Create Aggregate Device (Mic + BlackHole)

**Combines your microphone with BlackHole**

1. Open **Audio MIDI Setup** (Cmd+Space → "Audio MIDI Setup")
2. Click **"+"** → **"Create Aggregate Device"**
3. Check both devices:
   - ☑️ **Your Real Microphone** (e.g., Jabra EVOLVE)
   - ☑️ **BlackHole 2ch**
4. **⚠️ IMPORTANT - Set Device Order:**
   - In the "Subdevices" section at the top, make sure your **Real Microphone appears FIRST (leftmost)**
   - If BlackHole is first, drag your microphone button to the left to reorder
   - Order should be: `[Your Mic] [BlackHole]`
5. Enable **"Drift Correction"**:
   - Click **your real microphone** in the list → Check **"Drift Correction"** ✅
   - Click **BlackHole 2ch** in the list → Check **"Drift Correction"** ✅
6. **(Optional)** Rename to **"Mic + BlackHole"**

**Visual Guide:**

![Aggregate Device Setup](../static/aggregate-device-setup.png)

**Key points in the screenshot:**
- ✅ Jabra EVOLVE 20 MS is FIRST (leftmost) in Subdevices
- ✅ Both devices have Drift Correction enabled
- ✅ Clock Source is set to your real microphone

### Step 3: Create Multi-Output Device (BlackHole + Speakers)

**Sends audio to BlackHole AND your speakers simultaneously**

1. In Audio MIDI Setup, click **"+"** → **"Create Multi-Output Device"**
2. Check both:
   - ☑️ **BlackHole 2ch**
   - ☑️ **Your Speakers/Headphones** (e.g., Jabra EVOLVE 20 MS)
3. Click BlackHole → Check **"Drift Correction"**
4. Set **Primary Device** to your speakers for proper audio routing
5. **(Optional)** Rename to **"BlackHole + Speakers"** or **"Multi-Output Device"**

**Visual Guide:**

![Multi-Output Device Setup](../static/multi-output-device-setup.png)

**Key points in the screenshot:**
- ✅ Both Jabra EVOLVE (speakers) and BlackHole 2ch are checked
- ✅ Drift Correction is enabled on BlackHole
- ✅ Primary Device is set to Jabra EVOLVE 20 MS 2
- ⚠️ This device will be used as **Speaker** in Teams desktop app!

### Step 4: Configure System Settings

1. Open **System Settings** → **Sound** → **Output**
2. Select **"BlackHole + Speakers"**

---

## Windows Complete Setup

### Step 1: Install Virtual Audio Device

Install VB-Cable or VoiceMeeter from [Required Software](#windows) section.

**Verify**: Check **Sound settings** → **Recording** tab for CABLE Output or VoiceMeeter Output.

### Step 2: Configure VB-Cable

**If you installed VB-Cable:**

1. Right-click **Speaker icon** → **"Sounds"** → **"Recording"** tab
2. Right-click **"CABLE Output"** → **"Set as Default Device"**
3. Right-click **"CABLE Output"** → **"Properties"** → **"Listen"** tab
4. Check **"Listen to this device"** → Select your speakers → **"OK"**
5. Go to **"Playback"** tab → Right-click **"CABLE Input"** → **"Set as Default Device"**

### Step 2 (Alt): Configure VoiceMeeter

**If you installed VoiceMeeter:**

1. Open **VoiceMeeter** application
2. Set **A1** to your **Speakers**
3. Set **A2** to **VoiceMeeter VAIO**
4. Right-click **Speaker icon** → **"Sounds"** → **"Playback"**
5. Set **"VoiceMeeter Input"** as default
6. Go to **"Recording"** → Set **"VoiceMeeter Output"** as default

---

## Linux Setup

```bash
# Create virtual sink
pactl load-module module-null-sink sink_name=virtual_speaker sink_properties=device.description="Virtual_Speaker"

# Loopback to your speakers
pactl load-module module-loopback source=virtual_speaker.monitor sink=$(pactl get-default-sink)

# Set as default
pactl set-default-sink virtual_speaker
```

---

## Meeting Application Configuration

**⚠️ CRITICAL FOR DESKTOP APPS (Teams, Zoom):**

To capture audio from desktop meeting applications, you **MUST** configure BOTH:

**Microphone:**
- **macOS**: "Aggregate Device" (your Mic + BlackHole device)
- **Windows (VB-Cable)**: "CABLE Output"
- **Windows (VoiceMeeter)**: "VoiceMeeter Output"

**Speaker (⚠️ IMPORTANT):**
- **macOS**: "Multi-Output Device" (BlackHole + Speakers)
- **Windows (VB-Cable)**: "CABLE Input"
- **Windows (VoiceMeeter)**: "VoiceMeeter Input"

**Why speaker matters:**
Desktop meeting apps use protected audio that bypasses system routing. Setting the speaker explicitly to your Multi-Output Device forces audio through BlackHole for capture while still playing through your speakers.

**Browser-based apps (teams.microsoft.com, zoom.us) don't need speaker configuration - they work automatically!**

### Telegram Desktop

1. Go to **Calls** tab → Click **⋮** (three dots)
2. Select **"Call Settings"**
3. **Microphone**: Select your aggregate/virtual device
4. **Speakers**: Keep as regular speakers

### Zoom

1. **Settings** (gear icon) → **Audio**
2. **Microphone**: Select your aggregate/virtual device
3. **Speaker**: Keep as regular speakers

### Microsoft Teams

**⚠️ IMPORTANT FOR TEAMS DESKTOP APP:**

To capture Teams audio, you MUST set the speaker output to your Multi-Output Device.

1. **Profile** → **Settings** → **Devices**
2. **Microphone**: Select **"Aggregate Device"** (your aggregate device)
3. **Speaker**: Select **"Multi-Output Device"** ⚠️ (NOT your regular speakers!)

**Why this is necessary:**
- Teams desktop app uses protected audio streams that bypass system audio routing
- Setting Teams speaker to Multi-Output Device forces audio through BlackHole
- You'll still hear calls because Multi-Output includes both BlackHole AND your speakers

**Visual Guide:**

![Teams Audio Settings](../static/teams-audio-settings.png)

**Configuration checklist:**
- ✅ Microphone: Aggregate Device
- ✅ Speaker: Multi-Output Device
- ✅ Automatically adjust mic sensitivity: On (recommended)

**Alternative for Teams Web:**
- If using browser version (teams.microsoft.com), keep speakers as regular output
- Browser audio is captured automatically through system audio routing

### Discord

1. **User Settings** (gear icon) → **Voice & Video**
2. **Input Device**: Select your aggregate/virtual device
3. **Output Device**: Keep as regular speakers

### Browser-Based Apps (Meet, Zoom web, etc.)

**In-meeting controls:**
- Click microphone icon → Select your aggregate/virtual device

**Browser settings:**
- Chrome/Edge: Settings → Privacy → Site Settings → Microphone
- Safari: Safari → Settings → Websites → Microphone
- Firefox: Settings → Privacy → Permissions → Microphone

**Test online**: https://www.onlinemictest.com/

---

## Testing Your Setup

1. **Start Meeting Assistant**: `uv run python gui_app.py`
2. **Enable translation**: Check ☑️ "Enable TTS to Microphone"
3. **Select language**: Choose target language
4. **Test voice**: Speak into mic → Peer should hear you ✅
5. **Test TTS**: Wait for translation → Click "Speak to Mic" → Peer hears translation ✅
6. **Verify you hear TTS**: Should play through your speakers ✅

---

## Troubleshooting

### macOS

**Peer doesn't hear my voice:**
- ✅ Check real microphone is in Aggregate Device
- ✅ **Verify real microphone is FIRST (leftmost) in Subdevices order**
- ✅ Enable "Drift Correction" on real mic AND BlackHole
- ✅ Test Aggregate in System Settings → Sound → Input

**Peer doesn't hear TTS:**
- ✅ System output set to Multi-Output Device
- ✅ Meeting app mic set to Aggregate Device
- ✅ BlackHole included in both devices
- ✅ Real microphone is first in Aggregate Device order

**I don't hear TTS:**
- ✅ Set Multi-Output as system output
- ✅ Speakers included in Multi-Output
- ✅ Enable "Drift Correction" on BlackHole

### Windows

**No sound through speakers:**
- VB-Cable: Check "Listen to this device" enabled
- VoiceMeeter: Check A1 set to speakers and enabled

**Peer doesn't hear me:**
- VB-Cable: Meeting app should use CABLE Output
- VoiceMeeter: Check Hardware Input 1 set to your mic, B1 enabled

### General

**Virtual device not found:**
```bash
# Check devices
python -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]; p.terminate()"
```

**Audio choppy:**
- ✅ Enable "Drift Correction" 
- ✅ Increase buffer size in code: `tts_audio_router.py` line 110 (1024 → 2048)

### ⚠️ Meeting Apps Not Captured (Teams, Zoom)

**Problem:** YouTube/browser audio works, but Teams/Zoom audio is NOT captured by the app.

**Root Cause:** Meeting applications use **protected audio streams** or **exclusive audio modes** that bypass the system audio mixer, preventing BlackHole/VB-Cable from capturing their output.

**Why It Happens:**
- Meeting apps prioritize audio quality and use direct hardware access
- They may use exclusive WASAPI mode (Windows) or CoreAudio HAL (macOS)
- Security/DRM features prevent system-level audio capture
- Browser audio (YouTube) works because it goes through the regular system mixer

**Solutions:**

#### ✅ Solution 1: Configure Meeting App to Use Multi-Output Device (RECOMMENDED & FREE)

**This is the BEST solution for desktop meeting apps!**

**For Teams:**
1. Teams → Settings → Devices
2. **Speaker**: Select **"Multi-Output Device"** (the one you created in Step 3)
3. **Microphone**: Select **"Aggregate Device"**
4. Test: You should hear calls AND Meeting Assistant should capture audio ✅

**For Zoom:**
1. Zoom → Settings → Audio
2. **Speaker**: Select **"Multi-Output Device"**
3. **Microphone**: Select **"Aggregate Device"**
4. Test call to verify

**Why this works:**
- You explicitly tell the meeting app to output to Multi-Output Device
- Multi-Output includes both BlackHole (for capture) AND your speakers (so you hear it)
- No additional software needed!
- Works with full desktop app features (screen sharing, etc.)

**See screenshot:** [Teams Audio Settings](../static/teams-audio-settings.png)

#### Solution 2: Use App-Specific Audio Routing (macOS - Professional)

Install commercial audio routing software that can capture individual app audio:

**Loopback by Rogue Amoeba** ($99) - **BEST SOLUTION**
- https://rogueamoeba.com/loopback/
- Create virtual audio source from specific apps
- Route Teams/Zoom → Virtual Device → Meeting Assistant
- Non-invasive, works with all meeting apps
- **Setup:**
  1. Install Loopback
  2. Create new virtual device
  3. Add Teams/Zoom as audio source
  4. Route to BlackHole or new virtual output
  5. Set Meeting Assistant to capture this device

**Audio Hijack** ($64) - Alternative
- https://rogueamoeba.com/audiohijack/
- Record specific application audio
- More complex but powerful

**SoundSource** ($39) - Simpler option
- https://rogueamoeba.com/soundsource/
- Per-app audio routing
- Easier to use but less flexible

#### Solution 2: Use Meeting App Settings (Partial Solution)

Some meeting apps allow output device selection:

**Teams:**
1. Settings → Devices
2. **Speaker**: Set to "BlackHole 2ch" instead of regular speakers
3. **Limitation**: You won't hear the call through your regular speakers
4. **Workaround**: Use Multi-Output Device (BlackHole + Speakers)

**Zoom:**
1. Settings → Audio
2. **Speaker**: Set to "BlackHole 2ch"
3. Same limitations as Teams

**⚠️ Important:** This means the meeting app will output to BlackHole, but you may need to adjust your Multi-Output Device configuration.

#### Solution 3: Browser-Based Meetings (Workaround)

Use **browser versions** of meeting apps instead of desktop apps:
- ✅ Teams Web (teams.microsoft.com)
- ✅ Zoom Web (zoom.us/join)
- ✅ Google Meet (meet.google.com)

Browser audio goes through the system mixer and CAN be captured by BlackHole!

**Steps:**
1. Join meetings via browser instead of desktop app
2. Keep your existing BlackHole/Multi-Output setup
3. Browser audio will be captured automatically ✅

**Limitations:**
- Some features may be missing in web versions
- Browser performance may be lower
- Camera/screenshare might be limited

#### Solution 4: Screen Recording Audio (macOS)

Use macOS built-in screen recording with audio capture:

1. Open **QuickTime Player** → **File** → **New Screen Recording**
2. Click **Options** → Select **BlackHole 2ch** as microphone
3. Record during meeting
4. Use recorded audio file later with `transcribe_audio_file.py`

**Limitations:**
- Not real-time transcription
- Post-meeting processing only
- Creates large video files

#### Solution 5: Virtual Machine or Second Device

Run meeting app in VM or on second device:
- Route audio from VM/device to main computer
- Capture via BlackHole
- Complex setup, not recommended for most users

**Recommendation Priority:**

1. **🥇 Best:** Configure meeting app speaker to Multi-Output Device - **FREE & Full Features** ✅
2. **🥈 Good:** Browser-based meetings - Free but limited screen sharing
3. **🥉 Professional:** Loopback by Rogue Amoeba ($99) - Advanced features
4. **📝 Fallback:** Record and transcribe later - Not real-time

#### Verification Test

To verify if meeting app audio is being captured:

1. **Start Meeting Assistant**: `python gui_app.py`
2. **Join test meeting** or play test audio in meeting app
3. **Check transcription window**: Do you see the meeting audio transcribed?
   - ✅ **YES**: Audio is being captured
   - ❌ **NO**: Audio is protected, use one of the solutions above

**Test with YouTube first:**
- If YouTube works but Teams doesn't → Protected audio issue
- If YouTube also doesn't work → Configuration issue (check BlackHole setup)

---

## Advanced Configurations

### Per-App Audio Routing (macOS)

**SoundSource** ($39): https://rogueamoeba.com/soundsource/  
**Audio Hijack** ($64): https://rogueamoeba.com/audiohijack/  
**Loopback** ($99): https://rogueamoeba.com/loopback/

### Using Different Virtual Devices

Edit `tts_audio_router.py` line 11:
```python
def __init__(self, virtual_device_name: str = "YourDeviceName"):
```

---

## Summary

✅ **Virtual Device Installed**  
✅ **Aggregate Device Created** (macOS) or Virtual Device Configured (Windows)  
✅ **Multi-Output Created** (macOS)  
✅ **System Settings Configured**  
✅ **Meeting App Configured**  
✅ **Tested Successfully**  
✅ **Result**: Real-time multilingual communication! 🌍🦊

---

## Resources

- **BlackHole**: https://github.com/ExistentialAudio/BlackHole/wiki
- **VB-Cable**: https://vb-audio.com/Cable/VBCABLEManual.pdf
- **VoiceMeeter**: https://vb-audio.com/Voicemeeter/VoicemeeterManual.pdf
- **Main README**: [README.md](README.md)

**Happy Translating! 🎤🌍**
