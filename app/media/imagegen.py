"""Local image generation with SDXL Turbo (fast, fits in 16 GB VRAM).

The pipeline is loaded on first use and released afterwards so the GPU
is free for the LLM between generations.
"""

import datetime
import gc

from app.core.config import IMAGE_MODEL, OUTPUTS_DIR


def generate_image(prompt: str, steps: int = 4):
    """Return (PIL image, saved path). SDXL Turbo needs only 1-4 steps."""
    if not prompt.strip():
        return None, "Type a prompt first."

    import torch
    from diffusers import AutoPipelineForText2Image

    pipe = AutoPipelineForText2Image.from_pretrained(
        IMAGE_MODEL, torch_dtype=torch.float16, variant="fp16"
    )
    pipe.to("cuda")

    try:
        image = pipe(
            prompt=prompt,
            num_inference_steps=int(steps),
            guidance_scale=0.0,  # turbo models are trained for no CFG
        ).images[0]
    finally:
        del pipe
        gc.collect()
        torch.cuda.empty_cache()

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUTS_DIR / f"image_{stamp}.png"
    image.save(out_path)
    return image, f"Saved to {out_path}"
