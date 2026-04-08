import os

# --- CRITICAL WSL/LINUX FIX ---
# Must be set BEFORE moviepy is imported
os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

import asyncio
import edge_tts
from moviepy.config import change_settings

# Explicitly tell MoviePy where the binary is
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

from moviepy.editor import TextClip, AudioFileClip, ColorClip, CompositeVideoClip
from config import Config

class VideoCreator:
    def __init__(self, output_dir="output"):
        """Initializes the Video Automation engine with Syndicate standards."""
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    async def generate_voiceover(self, text: str, output_name: str = "voiceover.mp3"):
        """Generates high-quality human-like voiceover using Microsoft Edge-TTS."""
        # GuyNeural provides the authoritative, gritty tone required for the Syndicate
        voice = "en-US-GuyNeural" 
        communicate = edge_tts.Communicate(text, voice)
        output_path = os.path.join(self.output_dir, output_name)
        print(f"Generating voiceover: {output_path}...")
        await communicate.save(output_path)
        return output_path

    def create_daily_short(self, text: str, audio_path: str, output_name: str = "daily_short.mp4"):
        """Creates a high-impact video snippet for FB Reels/Stories."""
        print(f"Creating video: {output_name}...")
        output_path = os.path.join(self.output_dir, output_name)

        # 1. Load Audio and determine length
        audio = AudioFileClip(audio_path)
        duration = audio.duration

        # 2. Create Background (Deep Syndicate Blue)
        # 1080x1920 is the standard for mobile vertical video
        bg = ColorClip(size=(1080, 1920), color=(0, 0, 40)).set_duration(duration)

        # 3. Text Safety Logic
        # ImageMagick crashes if text is too long (exceeds width/height limits)
        # We cap it at 450 characters for the visual overlay.
        display_text = (text[:450] + "...") if len(text) > 450 else text

        # 4. Create Text Overlay with ImageMagick
        try:
            # 'caption' method handles word wrapping automatically
            txt_clip = TextClip(
                display_text, 
                fontsize=55, # Reduced slightly for better fit
                color='white', 
                font='Arial-Bold', 
                method='caption', 
                size=(900, None), # Fixed width of 900px to give margins
                align='center'
            )
            txt_clip = txt_clip.set_pos('center').set_duration(duration)
            
            # 5. Composite Layers
            video = CompositeVideoClip([bg, txt_clip])
        except Exception as e:
            print(f"WARNING: ImageMagick text rendering failed: {e}")
            print("Falling back to background-only video with full audio.")
            video = bg

        video.audio = audio

        # 6. Production Render
        # Threads=4 speeds up rendering on multi-core MSI systems
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
            video_path = self.create_daily_short(content, audio_path, video_file)
            return video_path
        except Exception as e:
            print(f"Critical error in video production: {e}")
            # Fallback to returning audio path so Telegram can at least send the intel
            return audio_path

if __name__ == "__main__":
    # Internal Test Harness
    async def test():
        creator = VideoCreator()
        test_text = "Syndicate Protocol Alpha: Nicotine patches combined with Huperzine-A for 4-hour deep work blocks."
        await creator.generate_biohacking_snippet("Test_Protocol", test_text)

    asyncio.run(test())