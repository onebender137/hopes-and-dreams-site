import os
import asyncio
import edge_tts
from moviepy.editor import TextClip, AudioFileClip, ColorClip, CompositeVideoClip
from config import Config

class VideoCreator:
    def __init__(self, output_dir="output"):
        """Initializes the Video Automation engine (Video Production tool #3 and #2)."""
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    async def generate_voiceover(self, text: str, output_name: str = "voiceover.mp3"):
        """Generates high-quality human-like voiceover using Microsoft Edge-TTS."""
        voice = "en-US-GuyNeural" # Natural sounding male voice
        communicate = edge_tts.Communicate(text, voice)
        output_path = os.path.join(self.output_dir, output_name)
        print(f"Generating voiceover: {output_path}...")
        await communicate.save(output_path)
        return output_path

    def create_daily_short(self, text: str, audio_path: str, output_name: str = "daily_short.mp4"):
        """Creates a simple, high-impact video snippet for YouTube/FB Reels."""
        print(f"Creating video: {output_name}...")
        output_path = os.path.join(self.output_dir, output_name)

        # 1. Load Audio
        audio = AudioFileClip(audio_path)
        duration = audio.duration

        # 2. Create Background (Simple Blue/Black for biohacking feel)
        bg = ColorClip(size=(1080, 1920), color=(0, 0, 50)).set_duration(duration)

        # 3. Create Text Overlay
        # Note: MoviePy requires ImageMagick for TextClip.
        # For simplicity, we'll use a very basic setup.
        # Use a multi-line wrap if the text is long
        wrapped_text = "\n".join([text[i:i+30] for i in range(0, len(text), 30)])

        txt_clip = TextClip(wrapped_text, fontsize=70, color='white', font='Arial-Bold', method='caption', size=(900, None))
        txt_clip = txt_clip.set_pos('center').set_duration(duration)

        # 4. Composite
        video = CompositeVideoClip([bg, txt_clip])
        video.audio = audio

        # 5. Write Video
        video.write_videofile(output_path, fps=24, codec='libx264')
        return output_path

    async def generate_biohacking_snippet(self, topic: str, content: str):
        """Higher-level method to produce a full video snippet from a topic and text."""
        audio_file = f"{topic.replace(' ', '_')}_audio.mp3"
        video_file = f"{topic.replace(' ', '_')}_video.mp4"

        audio_path = await self.generate_voiceover(content, audio_file)
        # Check if moviepy can render text (requires ImageMagick)
        # If it fails, we at least have the voiceover!
        try:
            video_path = self.create_daily_short(content, audio_path, video_file)
            return video_path
        except Exception as e:
            print(f"Error creating video clip: {e}. Voiceover generated: {audio_path}")
            return audio_path

if __name__ == "__main__":
    # Test Video Engine
    async def test():
        creator = VideoCreator()
        text = "Magnesium Glycinate is a powerful biohacking supplement that promotes deep, restful sleep. Take 400 milligrams before bed for maximum results!"
        await creator.generate_biohacking_snippet("Magnesium", text)

    asyncio.run(test())
