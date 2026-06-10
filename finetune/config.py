"""Fine-tuning configuration, sized for a 16 GB NVIDIA GPU."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Base model to fine-tune (downloaded from Hugging Face, ~15 GB once).
# 7B is the sweet spot for QLoRA on 16 GB VRAM.
BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# What your personalized model will be called in Ollama
CUSTOM_MODEL_NAME = "my-ai"

CHATLOG_DIR = ROOT / "data" / "chatlogs"
TRAINING_DIR = ROOT / "data" / "training"
ADAPTER_DIR = ROOT / "finetune" / "adapter"   # LoRA weights land here
MERGED_DIR = ROOT / "finetune" / "merged"     # merged full model for Ollama

SYSTEM_PROMPT = (
    "You are a helpful personal AI assistant running entirely on the "
    "user's own computer."
)

# --- QLoRA hyperparameters (safe defaults for 16 GB) ---
LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
MAX_SEQ_LENGTH = 1024
BATCH_SIZE = 1
GRAD_ACCUMULATION = 8       # effective batch size = 8
EPOCHS = 3
LEARNING_RATE = 2e-4

MIN_EXAMPLES = 50           # warn below this — tiny datasets overfit
