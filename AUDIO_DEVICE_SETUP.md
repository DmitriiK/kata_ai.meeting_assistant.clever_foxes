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

### Step 3: Create Multi-Output Device (BlackHole + Speakers)

**Sends TTS to BlackHole AND your speakers**

1. In Audio MIDI Setup, click **"+"** → **"Create Multi-Output Device"**
2. Check both:
   - ☑️ **BlackHole 2ch**
   - ☑️ **Your Speakers/Headphones**
3. Click BlackHole → Check **"Drift Correction"**
4. **(Optional)** Rename to **"BlackHole + Speakers"**

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

**Device to select as microphone:**
- **macOS**: "Mic + BlackHole" (Aggregate Device)
- **Windows (VB-Cable)**: "CABLE Output"
- **Windows (VoiceMeeter)**: "VoiceMeeter Output"

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

1. **Profile** → **Settings** → **Devices**
2. **Microphone**: Select your aggregate/virtual device
3. **Speakers**: Keep as regular speakers

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
