# Virtual Audio Setup Guide

## Why You Need Virtual Audio

To capture system audio (meeting participants, videos, music) along with your microphone, you need a virtual audio device that creates an audio "loop" from your system output back to an input that the app can record.

**What Gets Captured:**
- 🎤 **Microphone Input**: Your voice speaking
- 🔊 **System Audio Output**: Everything you hear (Teams, Zoom, YouTube, etc.)

---

## 🍎 macOS Setup (Tested & Working)

### Step 1: Install BlackHole

**Download:** https://github.com/ExistentialAudio/BlackHole

1. Download **BlackHole 2ch** (2-channel version is sufficient)
2. Install the package
3. Restart your computer (recommended)

### Step 2: Create Multi-Output Device

This step routes your audio to BOTH your headset (so you hear it) AND BlackHole (so the app captures it).

1. **Open Audio MIDI Setup:**
   - Press `Cmd + Space`
   - Type "Audio MIDI Setup"
   - Press Enter

2. **Create Multi-Output Device:**
   - Click the **`+`** button (bottom left)
   - Select **"Create Multi-Output Device"**

3. **Configure the Multi-Output Device:**
   - Check these boxes:
     - ✅ **Your Headset/Speakers** (e.g., "Jabra EVOLVE 20 MS", "AirPods", etc.)
     - ✅ **BlackHole 2ch**
   
4. **Enable Drift Correction:**
   - Click on **"BlackHole 2ch"** in the list
   - Check the **"Drift Correction"** box (prevents audio sync issues)

5. **Set as System Output:**
   - Right-click on **"Multi-Output Device"**
   - Select **"Use This Device For Sound Output"**
   
   **OR** use System Settings:
   - Go to **System Settings → Sound → Output**
   - Select **"Multi-Output Device"**

### Step 3: Test the Setup

1. **Start the app:**
   ```bash
   uv run python main.py
   ```

2. **Verify devices detected:**
   - 🎤 Microphone: Your headset or built-in mic
   - 🔊 System Audio: BlackHole 2ch

3. **Test with audio:**
   - Play a YouTube video or music
   - Speak into your microphone
   - Both should be transcribed separately!

### Important Notes for macOS

**✅ Recommended Usage:**
- **Keep Multi-Output as default** when using the app for meetings
- Your audio plays through both your headset AND BlackHole simultaneously
- You hear everything normally, app captures everything

**⚠️ If You Experience Issues:**
- Make sure Multi-Output Device is your system output
- Check that both devices are checked in Multi-Output
- Verify BlackHole is installed by checking available devices
- Restart the app after changing audio settings

**🔄 Switching Back to Normal:**
- System Settings → Sound → Output
- Select your normal headset/speakers
- Multi-Output only needed when transcribing

---

## 🌐 Cross-Platform Alternative: VB-Audio VoiceMeeter

**Download:** https://vb-audio.com/Voicemeeter/

**Benefits:**
- ✅ Free and cross-platform (Windows/Mac/Linux)
- ✅ Professional-grade audio routing
- ✅ More control over audio mixing
- ✅ Works with all meeting apps

**Setup:**
1. Download and install VoiceMeeter
2. Restart your computer
3. Open VoiceMeeter application
4. Configure routing (similar to Multi-Output concept)
5. Run our app - VoiceMeeter devices will appear

---

## 🪟 Windows Setup

### Option 1: VB-Cable (Recommended)

**Download:** https://vb-audio.com/Cable/

1. Download and install VB-Cable
2. Restart your computer
3. Set VB-Cable as your default output in Windows Sound Settings
4. Run the app and select VB-Cable as system audio source

### Option 2: VoiceMeeter (Advanced)

Follow the VoiceMeeter setup above for more control.

---

## How It Works

**Normal Audio Flow:**
```
Your Voice → Microphone → Computer → App ✅
System Audio → Speakers → 🚫 (Can't capture)
```

**With Virtual Audio:**
```
Your Voice → Microphone → Computer → App ✅
System Audio → Multi-Output → Speakers ✅ (You hear it)
                           → BlackHole → App ✅ (App captures it)
```

---

## Meeting App Compatibility

**✅ Works with ALL meeting apps:**
- Microsoft Teams
- Zoom
- Google Meet
- Discord
- Slack
- WhatsApp
- Any other audio/video app

**Configuration:**
- **Microphone:** Keep your normal microphone selected in the meeting app
- **Speakers:** System uses Multi-Output Device (no change needed in meeting app)
- **Transcription:** App automatically captures both microphone and system audio

---

## Troubleshooting

### No System Audio Captured?

1. **Check Multi-Output Device is set as default:**
   - System Settings → Sound → Output → Multi-Output Device

2. **Verify BlackHole is in Multi-Output:**
   - Open Audio MIDI Setup
   - Multi-Output Device should have BlackHole checked

3. **Test with system sound:**
   ```bash
   say "Testing audio routing"
   ```
   The app should transcribe this.

### No Microphone Audio?

1. **Check microphone permissions:**
   - System Settings → Privacy & Security → Microphone
   - Ensure Terminal has permission

2. **Verify correct device detected:**
   - Look at app startup messages for device selection

### Audio Quality Issues?

1. **Enable Drift Correction** on BlackHole in Multi-Output Device
2. **Match sample rates** (48000 Hz recommended)
3. **Use headphones** to prevent echo/feedback

### App Doesn't See BlackHole?

1. Restart the app after installing BlackHole
2. Verify BlackHole is installed:
   ```bash
   system_profiler SPAudioDataType | grep BlackHole
   ```

---

## Testing

### Quick Test:

1. **Play audio:**
   ```bash
   say "This is a system audio test. The transcription app should capture this."
   ```

2. **Speak into microphone:** Say something

3. **Check output:** App should show:
   - 🎤 MICROPHONE: Your spoken words
   - 🔊 SYSTEM_AUDIO: The test message

### Meeting Test:

1. Start the app
2. Join a test meeting (Zoom/Teams)
3. Play a video or have someone speak
4. Speak yourself
5. Check transcriptions show both sources

---

## FAQ

**Q: Will this affect my normal audio?**
A: No, you still hear everything normally through your headset.

**Q: Do I need to configure Teams/Zoom?**
A: No, keep your normal microphone in the meeting app. The Multi-Output routing happens at the system level.

**Q: Can I use this for recording music/videos?**
A: Yes! It captures any system audio output.

**Q: How do I switch back to normal audio?**
A: System Settings → Sound → Output → Select your headset instead of Multi-Output Device

**Q: Does this work with AirPods/Bluetooth?**
A: Yes, works with any output device.

**Q: What if I unplug my headset?**
A: The Multi-Output Device will break since it's configured for your headset. To fix:

1. **Quick Fix (Temporary):**
   - Open **Audio MIDI Setup**
   - Select **Multi-Output Device**
   - Uncheck your headset (now unavailable)
   - Check **MacBook Pro Speakers**
   - Audio routing restored

2. **Permanent Solution:**
   - Create multiple Multi-Output Devices:
     - **Multi-Output Device 1**: Headset + BlackHole (when headset plugged in)
     - **Multi-Output Device 2**: MacBook Speakers + BlackHole (when no headset)
   - Switch between them in System Settings → Sound → Output as needed

---

## Summary

**For macOS Users (Recommended):**
1. ✅ Install BlackHole 2ch
2. ✅ Create Multi-Output Device (Your Headset + BlackHole)
3. ✅ Set Multi-Output as system output
4. ✅ Run the app
5. ✅ Everything just works!

**Result:** Your voice and all system audio are automatically captured and transcribed separately.