import os
import random
import re
import base64
import requests
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

# --- CRITICAL WSL/LINUX FIX ---
# Must be set BEFORE moviepy is imported to ensure the backend is found
os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

import asyncio
import edge_tts
from moviepy.config import change_settings

# Explicitly tell MoviePy where the binary is
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

from moviepy.editor import TextClip, AudioFileClip, ImageClip, ColorClip, CompositeVideoClip
from config import Config

class VideoCreator:
    def __init__(self, output_dir="output"):
        """Initializes the Video Automation engine with Syndicate standards."""
        self.output_dir = output_dir
        self.base_media_path = "media"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    async def generate_voiceover(self, text: str, output_name: str = "voiceover.mp3"):
        """Generates high-quality human-like voiceover using Andrew (Natural)."""
        # Andrew provides a smoother, more authoritative cadence for research intel
        voice = "en-US-AndrewNeural" 
        
        # PHONETIC PATCH: Force 'Lead' to be pronounced like 'Leader' (not the metal)
        # We replace "Lead Researcher" with "Leed Researcher" in the audio ONLY
        audio_text = re.sub(r'\bLead researcher\b', 'Leed researcher', text, flags=re.IGNORECASE)
        audio_text = re.sub(r'\bLead Researcher\b', 'Leed Researcher', audio_text)

        communicate = edge_tts.Communicate(audio_text, voice)
        output_path = os.path.join(self.output_dir, output_name)
        print(f"Generating voiceover with Andrew: {output_path}...")
        await communicate.save(output_path)
        return output_path

    def _generate_flux_background(self, topic: str):
        """
        Generates a topic-specific 1080x1920 vertical video background using FLUX.
        Returns path to saved JPEG, or None if API key missing / generation fails.
        Falls through to _get_random_background() in the caller on None.
        """
        api_key = os.environ.get("TOGETHER_API_KEY")
        if not api_key:
            print("[VIDEO BG] No TOGETHER_API_KEY found, falling back to random.")
            return None

        # Visual-only prompt — no text, FLUX can't spell reliably
        prompt = (
            f"Abstract scientific illustration representing {topic}. "
            "Vertical composition, dark navy blue background. "
            "Glowing neon cyan and gold molecular structures. "
            "Brain anatomy, neural networks, biochemical pathways. "
            "Cyberpunk cinematic lighting, deep blue and gold color palette. "
            "Atmospheric, professional pharmaceutical research aesthetic. "
            "No text, no letters, no words, pure visual imagery, dramatic depth of field."
        )

        try:
            print(f"[VIDEO BG] Requesting FLUX vertical visual for '{topic}'...")
            response = requests.post(
                "https://api.together.xyz/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "black-forest-labs/FLUX.1-schnell",
                    "prompt": prompt,
                    "width": 768,    # FLUX schnell needs multiples of 16, 768x1344 ~= 9:16 ratio
                    "height": 1344,
                    "steps": 4,
                    "n": 1,
                    "response_format": "b64_json"
                },
                timeout=60
            )
            if response.status_code != 200:
                print(f"[VIDEO BG] FLUX returned {response.status_code}: {response.text[:200]}")
                return None

            img_data = base64.b64decode(response.json()["data"][0]["b64_json"])
            img = Image.open(BytesIO(img_data)).convert("RGB")

            # Resize to exact 1080x1920 (vertical short standard)
            img = img.resize((1080, 1920), Image.LANCZOS)

            # Save it
            os.makedirs("media/video_backgrounds", exist_ok=True)
            slug = re.sub(r'[^a-z0-9-]+', '-', topic.lower()).strip('-')[:50]
            date_str = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            filename = f"media/video_backgrounds/{date_str}-{slug}.jpg"
            img.save(filename, "JPEG", quality=88, optimize=True)
            print(f"[VIDEO BG] FLUX background saved: {filename}")
            return filename

        except Exception as e:
            print(f"[VIDEO BG] FLUX generation failed ({e}), falling back to random.")
            return None

    def _get_random_background(self, topic: str):
        """Picks a random 'wild' image from the relevant topic folder. Used as fallback when FLUX is unavailable."""
        mapping = {
            "nicotine": "nicotine", "patch": "nicotine", "asprey": "nicotine",
            "astral": "astral", "dream": "astral", "vibration": "astral", "darius": "astral",
            "kratom": "kratom", "alkaloid": "kratom", "mitragynine": "kratom",
            "cannabis": "cannabis", "thc": "cannabis", "cbd": "cannabis",
        }
        
        subfolder = "general"
        for key, folder in mapping.items():
            if key in topic.lower():
                subfolder = folder
                break
        
        target_dir = os.path.join(self.base_media_path, subfolder)
        
        # Fallback to general if folder is missing or empty
        if not os.path.exists(target_dir):
            target_dir = os.path.join(self.base_media_path, "general")
            
        try:
            valid_exts = ('.jpg', '.png', '.jpeg')
            files = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.lower().endswith(valid_exts)]
            return random.choice(files) if files else None
        except Exception:
            return None

    def _select_background(self, topic: str):
        """
        Two-tier background selection:
        1. Try FLUX topic-specific generation (online, ~6-10s)
        2. Fall back to random folder image if FLUX fails or no API key
        """
        bg = self._generate_flux_background(topic)
        if bg:
            return bg
        print("[VIDEO BG] Using local fallback background.")
        return self._get_random_background(topic)

    def create_daily_short(self, text: str, audio_path: str, topic: str, output_name: str = "daily_short.mp4"):
        """Creates a high-impact video snippet using 'Wild' backgrounds."""
        print(f"Creating video: {output_name}...")
        output_path = os.path.join(self.output_dir, output_name)

        # 1. Load Audio and determine length
        audio = AudioFileClip(audio_path)
        duration = audio.duration

        # 2. Select Background — FLUX topic-specific first, random fallback
        bg_image_path = self._select_background(topic)
        
        if bg_image_path:
            # 1. Load and force image to fill the 1080x1920 vertical canvas
            bg = ImageClip(bg_image_path).set_duration(duration)
            
            # Use 'fill' strategy: Resize by height, then crop/center to avoid the offset
            bg = bg.resize(height=1920).set_position('center')
            
            # 2. Dark overlay pinned exactly to the top-left (0,0) to cover everything
            # Slightly heavier dim (0.5) to ensure text legibility on busier FLUX visuals
            overlay = ColorClip(size=(1080, 1920), color=(0, 0, 0))
            overlay = overlay.set_opacity(0.5).set_duration(duration).set_position((0, 0))
            
            background_group = [bg, overlay]
        else:
            # Fallback to Syndicate Blue pinned to top-left
            bg = ColorClip(size=(1080, 1920), color=(0, 0, 40)).set_duration(duration).set_position((0, 0))
            background_group = [bg]

        # 3. Text Safety Logic
        # ImageMagick crashes if text is too long. Cap at 450 chars.
        display_text = (text[:450] + "...") if len(text) > 450 else text

        # 4. Create Text Overlay with ImageMagick
        try:
            # 'caption' method handles word wrapping automatically
            txt_clip = TextClip(
                display_text, 
                fontsize=60, 
                color='white', 
                font='Arial-Bold', 
                method='caption', 
                size=(900, None), 
                align='center'
            )
            txt_clip = txt_clip.set_pos('center').set_duration(duration)
            
            # 5. Composite Layers
            video = CompositeVideoClip(background_group + [txt_clip], size=(1080, 1920))
        except Exception as e:
            print(f"WARNING: ImageMagick text rendering failed: {e}")
            video = CompositeVideoClip(background_group)

        video.audio = audio

        video.write_videofile(
            output_path, 
            fps=24, 
            codec='libx264', 
            audio_codec='aac', 
            threads=4, 
            preset='ultrafast',
            logger='bar',
            ffmpeg_params=["-nostdin"]
        )
        return output_path
        

    async def generate_biohacking_snippet(self, topic: str, content: str):
        """Higher-level production method to produce a full snippet."""
        safe_topic = topic.replace(' ', '_').lower()
        audio_file = f"{safe_topic}_audio.mp3"
        video_file = f"{safe_topic}_video.mp4"

        # Step 1: Voiceover
        audio_path = await self.generate_voiceover(content, audio_file)
        
        # Step 2: Video Composition
        try:
            video_path = self.create_daily_short(content, audio_path, topic, video_file)
            return video_path
        except Exception as e:
            print(f"Critical error in video production: {e}")
            return audio_path

if __name__ == "__main__":
    # Internal Test Harness
    async def test():
        creator = VideoCreator()
        test_text = "Lead researcher protocols indicate that Nicotine and Huperzine-A stacking is optimal."
        await creator.generate_biohacking_snippet("test", test_text)

    asyncio.run(test())
