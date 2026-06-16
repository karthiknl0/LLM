"""Local text-to-video with LTX-Video. Experimental on 16 GB VRAM:
uses CPU offload, so expect several minutes per short clip.

The model (~10 GB) downloads from Hugging Face on first use.
"""

import datetime
import gc

from app.core.config import OUTPUTS_DIR, VIDEO_MODEL


def generate_video(prompt: str, seconds: float = 3.0):
    """Return (video path, status message)."""
    if not prompt.strip():
        return None, "Type a prompt first."

    import torch
    from diffusers import LTXPipeline
    from diffusers.utils import export_to_video

    pipe = LTXPipeline.from_pretrained(VIDEO_MODEL, torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()  # required to fit in 16 GB

    fps = 24
    # LTX requires num_frames to be a multiple of 8 plus 1
    num_frames = max(9, int(round(seconds * fps / 8)) * 8 + 1)

    try:
        frames = pipe(
            prompt=prompt,
            negative_prompt="worst quality, blurry, jittery, distorted",
            width=704,
            height=480,
            num_frames=num_frames,
            num_inference_steps=30,
        ).frames[0]
    finally:
        del pipe
        gc.collect()
        torch.cuda.empty_cache()

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUTS_DIR / f"video_{stamp}.mp4"
    export_to_video(frames, str(out_path), fps=fps)
    return str(out_path), f"Saved to {out_path}"
