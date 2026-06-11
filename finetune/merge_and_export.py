"""Merge the trained LoRA adapter into the base model and import the
result into Ollama as your own named model.

Run:  python -m finetune.merge_and_export

Merging happens on CPU (needs ~16 GB free RAM, fits in your 32 GB).
Ollama imports the merged safetensors directly and quantizes it to 4-bit.
"""

import shutil
import subprocess

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from finetune.config import (
    ADAPTER_DIR,
    BASE_MODEL,
    CUSTOM_MODEL_NAME,
    MERGED_DIR,
    MODEL_SYSTEM_PROMPT,
)


def main() -> None:
    if not (ADAPTER_DIR / "adapter_config.json").exists():
        raise SystemExit(
            f"No trained adapter at {ADAPTER_DIR} — run `python -m finetune.train` first."
        )

    print(f"Loading base model {BASE_MODEL} on CPU (this takes a few minutes)...")
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, torch_dtype=torch.float16, device_map="cpu"
    )
    print("Merging LoRA adapter into base weights...")
    model = PeftModel.from_pretrained(base, str(ADAPTER_DIR))
    model = model.merge_and_unload()

    if MERGED_DIR.exists():
        shutil.rmtree(MERGED_DIR)
    model.save_pretrained(str(MERGED_DIR))
    AutoTokenizer.from_pretrained(BASE_MODEL).save_pretrained(str(MERGED_DIR))
    print(f"Merged model saved to {MERGED_DIR}")

    modelfile = MERGED_DIR / "Modelfile"
    modelfile.write_text(
        f'FROM {MERGED_DIR}\nSYSTEM """{MODEL_SYSTEM_PROMPT}"""\n'
    )

    print(f"Importing into Ollama as '{CUSTOM_MODEL_NAME}' (quantized to 4-bit)...")
    try:
        subprocess.run(
            [
                "ollama", "create", CUSTOM_MODEL_NAME,
                "-f", str(modelfile), "--quantize", "q4_K_M",
            ],
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SystemExit(
            f"Ollama import failed ({exc}). Run it manually:\n"
            f"  ollama create {CUSTOM_MODEL_NAME} -f {modelfile} --quantize q4_K_M"
        )

    print(
        f"\nSuccess! Try it:  ollama run {CUSTOM_MODEL_NAME}\n"
        f"To make the app use it, set CHAT_MODEL = \"{CUSTOM_MODEL_NAME}\" "
        f"in app/config.py.\n"
        f"You can now delete {MERGED_DIR} to reclaim ~15 GB of disk."
    )


if __name__ == "__main__":
    main()
