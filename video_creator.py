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
os.environ.setdefault("IMAGEMAGICK_BINARY", "/usr/bin/convert")

import asyncio
import edge_tts
from moviepy.config import change_settings

# Explicitly tell MoviePy where the binary is
change_settings({"IMAGEMAGICK_BINARY": os.environ.get("IMAGEMAGICK_BINARY", "/usr/bin/convert")})

from moviepy.editor import TextClip, AudioFileClip, ImageClip, ColorClip, CompositeVideoClip, VideoFileClip, concatenate_videoclips
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
            print(f"[VIDEO BG] Requesting Qwen-Image vertical visual for '{topic}'...")
            response = requests.post(
                "https://api.together.xyz/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "Qwen/Qwen-Image",
                    "prompt": prompt,
                    "width": 768,    # 768x1344 ~= 9:16, verified returned unresized by Qwen-Image
                    "height": 1344,
                    "steps": 28,
                    "n": 1,
                    "response_format": "b64_json"
                },
                timeout=60
            )
            if response.status_code != 200:
                print(f"[VIDEO BG] image API returned {response.status_code}: {response.text[:200]}")
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
            print(f"[VIDEO BG] background saved: {filename}")
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

        # 3. Dynamic Teleprompter Text Scroll (Hardened for ImageMagick)
        try:
            # Split into paragraphs, then further chunk any long paragraph.
            # REDUCED CHUNK SIZE: Drops from 600 to 200 to prevent ImageMagick memory crashes on massive scripts
            MAX_PARAGRAPH_CHARS = 200
            raw_paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            paragraphs = []
            for p in raw_paragraphs:
                if len(p) <= MAX_PARAGRAPH_CHARS:
                    paragraphs.append(p)
                    continue
                sentences = re.split(r'(?<=[.!?])\s+', p)
                buf = ""
                for sent in sentences:
                    if len(buf) + len(sent) + 1 <= MAX_PARAGRAPH_CHARS:
                        buf = (buf + " " + sent).strip() if buf else sent
                    else:
                        if buf:
                            paragraphs.append(buf)
                        while len(sent) > MAX_PARAGRAPH_CHARS:
                            paragraphs.append(sent[:MAX_PARAGRAPH_CHARS])
                            sent = sent[MAX_PARAGRAPH_CHARS:]
                        buf = sent
                if buf:
                    paragraphs.append(buf)
            
            text_clips = []
            current_y_offset = 0
            
            for p in paragraphs:
                tc = TextClip(
                    p, 
                    fontsize=55, # Slightly scaled down to prevent word-wrap clipping
                    color='white', 
                    font='Helvetica-Bold', 
                    method='caption', 
                    size=(900, None), 
                    align='center',
                    bg_color='transparent' # CRITICAL: Forces ImageMagick to preserve text opacity
                )
                text_clips.append({'clip': tc, 'y_offset': current_y_offset})
                current_y_offset += tc.h + 60  # 60px gap
                
            total_text_height = current_y_offset
            screen_height = 1920
            
            # Start lower so it glides in naturally
            start_y = screen_height * 0.8  
            end_y = (screen_height * 0.2) - total_text_height 
            total_travel = start_y - end_y

            # Enforce strict integer casting for MoviePy positional math
            def make_mover(offset):
                return lambda t: ('center', int(start_y + offset - (total_travel * (t / duration))))

            animated_clips = []
            for item in text_clips:
                clip = item['clip']
                offset = item['y_offset']
                
                animated_clip = clip.set_pos(make_mover(offset)).set_duration(duration)
                animated_clips.append(animated_clip)
            
            # 5. Composite Layers
            video = CompositeVideoClip(background_group + animated_clips, size=(1080, 1920))
            
            # CRITICAL: Force FPS inheritance before rendering
            video.fps = 24
            
        except Exception as e:
            print(f"WARNING: ImageMagick text rendering failed: {e}")
            # Fallback to a simple title if the full scroll fails
            fallback_text = TextClip("AUDIO TRANSCRIPT UNAVAILABLE", fontsize=50, color='red').set_pos('center').set_duration(duration)
            video = CompositeVideoClip(background_group + [fallback_text], size=(1080, 1920))

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
        """Higher-level production method to produce a full snippet with dynamic intro titles."""
        safe_topic = topic.replace(' ', '_').lower()
        audio_file = f"{safe_topic}_audio.mp3"
        video_file = f"{safe_topic}_video.mp4"

        # Step 1: Voiceover synthesis
        audio_path = await self.generate_voiceover(content, audio_file)
        
        # Step 2: Main Video Composition
        try:
            core_video_path = self.create_daily_short(content, audio_path, topic, video_file)
            
            # --- STEP 3: STITCHING WITH DYNAMIC INTRO OVERLAY ---
            print("Processing customized Syndicate Intro sequence...")
            
            # Load the base intro clip
            intro_clip = VideoFileClip(f"{self.base_media_path}/intro_vertical.mp4")
            
            # Clean up topic string for the visual hook
            clean_title = topic.replace('_', ' ').replace('-', ' ').upper()
            
            # Generate the transient title clip via ImageMagick
            intro_title = TextClip(
                clean_title, 
                fontsize=92, 
                color='white', 
                font='Helvetica-Bold', 
                stroke_color='black',  
                stroke_width=7,
                method='caption', 
                size=(960, None), 
                align='center'
            )
            # Use a lambda function to guarantee compatibility across MoviePy versions
            intro_title = intro_title.set_duration(intro_clip.duration).set_pos(lambda t: ('center', 150))
            
            # Layer the title directly over the intro file
            custom_intro = CompositeVideoClip([intro_clip, intro_title], size=(1080, 1920))
            
            # CRITICAL HARDENING FIX: Force FPS inheritance so the video track doesn't render black
            custom_intro.fps = intro_clip.fps
            custom_intro.audio = intro_clip.audio  # Lock and maintain native intro sound track
            
            # Load the newly generated core content video
            main_clip = VideoFileClip(core_video_path)
            
            # Stitch customized intro together with your main asset
            final_stitched_video = concatenate_videoclips([custom_intro, main_clip], method="compose")
            
            # Set the clean final output path
            final_path = os.path.join(self.output_dir, f"FINAL_{video_file}")
            print(f"Baking final video file asset to: {final_path}...")
            
            final_stitched_video.write_videofile(
                final_path, 
                fps=24, 
                codec='libx264', 
                audio_codec='aac', 
                threads=4, 
                preset='ultrafast',
                logger='bar',
                ffmpeg_params=["-nostdin"]
            )
            
            # Clean up memory allocations to prevent file lock drops
            intro_clip.close()
            intro_title.close()
            custom_intro.close()
            main_clip.close()
            final_stitched_video.close()
            
            return final_path
            
        except Exception as e:
            print(f"Critical error in video production pipeline: {e}")
            return audio_path       
    

if __name__ == "__main__":
    # Internal Test Harness
    async def test():
        creator = VideoCreator()
        test_text = "Lead researcher protocols indicate that Nicotine and Huperzine-A stacking is optimal."
        # Running this will now produce a video with "NICOTINE DETOX PROTOCOL" burned into the intro
        await creator.generate_biohacking_snippet("Nicotine Detox Protocol", test_text)

    asyncio.run(test())