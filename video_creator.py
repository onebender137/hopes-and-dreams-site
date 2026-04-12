import os
import random
import re

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

    def _get_random_background(self, topic: str):
        """Picks a random 'wild' image from the relevant topic folder."""
        mapping = {
            "nicotine": "nicotine", "patch": "nicotine", "asprey": "nicotine",
            "astral": "astral", "dream": "astral", "vibration": "astral", "darius": "astral",
            "kratom": "kratom", "alkaloid": "kratom", "mitragynine": "kratom"
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

    def create_daily_short(self, text: str, audio_path: str, topic: str, output_name: str = "daily_short.mp4"):
        """Creates a high-impact video snippet using 'Wild' backgrounds."""
        print(f"Creating video: {output_name}...")
        output_path = os.path.join(self.output_dir, output_name)

        # 1. Load Audio and determine length
        audio = AudioFileClip(audio_path)
        duration = audio.duration

        # 2. Select and Create Background
        bg_image_path = self._get_random_background(topic)
        
        if bg_image_path:
            # Load the 'wild' image, resize for vertical (1080x1920), and center it
            bg = ImageClip(bg_image_path).set_duration(duration)
            bg = bg.resize(height=1920) 
            bg = bg.set_pos('center')
            
            # Dark overlay to make white text pop against busy images
            overlay = ColorClip(size=(1080, 1920), color=(0, 0, 0)).set_opacity(0.4).set_duration(duration)
            background_group = [bg, overlay]
        else:
            # Fallback to Syndicate Blue if no image found
            bg = ColorClip(size=(1080, 1920), color=(0, 0, 40)).set_duration(duration)
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
            video = CompositeVideoClip(background_group + [txt_clip])
        except Exception as e:
            print(f"WARNING: ImageMagick text rendering failed: {e}")
            video = CompositeVideoClip(background_group)

        video.audio = audio

        # 6. Production Render (Optimized for MSI threads)
        video.write_videofile(
            output_path, 
            fps=24, 
            codec='libx264', 
            audio_codec='aac', 
            threads=4, 
            logger=None
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