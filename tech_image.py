#!/usr/bin/env python3
"""tech_image.py — generate a header image for a tech article.

Input: --title <title> --content <content> --slug <slug>

1. Extracts a visual concept from the article (35b LLM) — the "pick the
   ideas" step. The LLM picks the most cinematic angle and writes a
   brand-matched prompt (cyan/gold/navy, no text in the image).
2. Generates the image via ComfyUI (Qwen-Image-2.1-Turbo, 8 steps, PE
   rewrite) — same pipeline as the Hopes bot's primary image gen.
3. Saves the image to tech/images/<slug>.png.

Prints `IMAGE_PATH: <path>` on the last line on success.
"""
import argparse, json, time, urllib.request, os, sys

SITE = os.path.dirname(os.path.abspath(__file__))
BASE_OLLAMA = "http://100.123.157.7:11434"
MODEL = "huihui_ai/qwen3.6-abliterated:35b"
COMFYUI = "http://100.123.157.7:8188"

NEGATIVE_PROMPT = (
    "text, letters, words, typography, captions, labels, writing, watermark, "
    "signature, chemical element labels, atom labels, molecular formula notation, "
    "haze, fog, mist, washed out, low contrast, milky, desaturated, muted colors, "
    "sepia, dusty, beige, flat lighting, blurry, heavy bokeh, empty background"
)


def extract_visual_prompt(title, content):
    """Use the 35b to extract a single visual concept from the tech article."""
    prompt = (
        "You are an art director for a tech build-log publication. Given this "
        "article, pick ONE visual concept that would make a compelling, cinematic "
        "header image. It should be abstract and atmospheric (not a literal "
        "screenshot), and it should capture the article's core subject.\n\n"
        f"TITLE: {title}\n\n"
        f"CONTENT (first 2500 chars):\n{content[:2500]}\n\n"
        "Write a visual prompt (2-4 sentences) for an image model. Rules:\n"
        "- NO text, labels, words, or typography in the image.\n"
        "- Brand aesthetic: vivid luminous cyan as the primary light source, "
        "rich metallic gold accents, deep dark-navy background, strong tonal "
        "contrast, cinematic depth (crisp hero subject, dimmer structures "
        "receding into the background).\n"
        "- Describe LIGHT, not darkness (the subject is emissive and radiant).\n"
        "- Premium editorial / cyberpunk-research aesthetic.\n"
        "Return ONLY the visual prompt. Nothing else."
    )
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "options": {"num_ctx": 4096},
    }
    req = urllib.request.Request(BASE_OLLAMA + "/api/chat",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=300))
    msg = d.get("message", {})
    return (msg.get("content", "").strip() if isinstance(msg, dict) else str(msg))


def generate_qwen21_image(prompt, negative_prompt):
    """Generate an image via ComfyUI (Qwen-Image-2.1-Turbo, 8 steps, PE rewrite).
    Returns a PIL Image (RGB) or None on failure. Reuses the Hopes bot's workflow."""
    from PIL import Image
    from io import BytesIO

    def post(path, payload):
        req = urllib.request.Request(COMFYUI + path,
                                     data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())

    def get(path):
        with urllib.request.urlopen(COMFYUI + path, timeout=60) as r:
            return r.read()

    def build_wf(seed):
        return {
            "0": {"class_type": "QwenPERewriteT8", "inputs": {
                "user_prompt": prompt, "task": "t2i", "aspect_ratio": "1:1",
                "output_language": "English", "transparent_rgba": False,
                "t2i_model": "Qwen-Image-2.1-PE-T2I.Q4_K_M.gguf",
                "edit_model": "Qwen-Image-2.1-PE-T2I.Q4_K_M.gguf",
                "vision_model": "Auto", "model_lifetime": "after_run",
                "seed": seed}},
            "1": {"class_type": "UnetLoaderGGUF", "inputs": {
                "unet_name": "qwen-image-2.1-turbo-Q4_K_M.gguf"}},
            "2": {"class_type": "CLIPLoader", "inputs": {
                "clip_name": "qwen3vl_8b_w4a8.safetensors", "type": "qwen_image"}},
            "3": {"class_type": "VAELoader", "inputs": {
                "vae_name": "qwen_image_2.1_vae_bf16.safetensors"}},
            "4": {"class_type": "TextEncodeQwenImage21", "inputs": {
                "clip": ["2", 0], "prompt": ["0", 0],
                "negative_prompt": negative_prompt, "resolution": 1280}},
            "5": {"class_type": "KSampler", "inputs": {
                "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler",
                "scheduler": "simple", "denoise": 1.0, "model": ["1", 0],
                "positive": ["4", 0], "negative": ["4", 1],
                "latent_image": ["4", 2]}},
            "6": {"class_type": "VAEDecode", "inputs": {
                "samples": ["5", 0], "vae": ["3", 0]}},
            "7": {"class_type": "SaveImage", "inputs": {
                "filename_prefix": "hopes", "format": "png", "images": ["6", 0]}},
        }

    def gen_once(seed):
        wf = build_wf(seed)
        pid = post("/prompt", {"prompt": wf})["prompt_id"]
        for _ in range(240):  # ~8 min max; warm ~2min, cold load ~3min
            time.sleep(2)
            try:
                hist = json.loads(get("/history/" + pid))
            except Exception:
                continue
            if pid in hist:
                for node, out in hist[pid].get("outputs", {}).items():
                    for img in out.get("images", []):
                        if img.get("type") == "output":
                            src = (f"/view?filename={img['filename']}"
                                   f"&subfolder={img.get('subfolder','')}"
                                   f"&type={img['type']}")
                            return Image.open(BytesIO(get(src))).convert("RGB")
                return None
        return None

    seed = int(time.time() * 1000) % (2 ** 31)
    return gen_once(seed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--content", required=True)
    ap.add_argument("--slug", required=True)
    args = ap.parse_args()

    # 1. Extract visual prompt
    visual_prompt = extract_visual_prompt(args.title, args.content)
    if not visual_prompt:
        print("prompt extraction failed")
        sys.exit(1)
    print(f"visual prompt: {visual_prompt[:120]}...")

    # 2. Generate image
    image = generate_qwen21_image(visual_prompt, NEGATIVE_PROMPT)
    if image is None:
        print("image generation failed")
        sys.exit(1)

    # 3. Save to tech/images/<slug>.png
    img_dir = os.path.join(SITE, "tech", "images")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, f"{args.slug}.png")
    image.save(img_path)
    print(f"saved: {img_path}")
    print(f"IMAGE_PATH: {img_path}")


if __name__ == "__main__":
    main()
