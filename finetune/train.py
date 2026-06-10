"""QLoRA fine-tuning on your own chats. Sized for a 16 GB NVIDIA GPU.

Run:  python -m finetune.train

Expects data/training/dataset.jsonl (run `python -m finetune.export_data`
first). Trains a LoRA adapter on a 4-bit quantized base model — the base
stays frozen, only the small adapter learns. Takes roughly 1-3 hours
depending on dataset size.
"""

import json

import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

from finetune.config import (
    ADAPTER_DIR,
    BASE_MODEL,
    BATCH_SIZE,
    EPOCHS,
    GRAD_ACCUMULATION,
    LEARNING_RATE,
    LORA_ALPHA,
    LORA_DROPOUT,
    LORA_RANK,
    MAX_SEQ_LENGTH,
    MIN_EXAMPLES,
    TRAINING_DIR,
)


def load_dataset() -> Dataset:
    path = TRAINING_DIR / "dataset.jsonl"
    if not path.exists():
        raise SystemExit(
            f"{path} not found — run `python -m finetune.export_data` first."
        )
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) < MIN_EXAMPLES:
        print(f"WARNING: only {len(rows)} examples — results may be poor.")
    return Dataset.from_list(rows)


def main() -> None:
    if not torch.cuda.is_available():
        raise SystemExit("CUDA GPU not available — fine-tuning needs your NVIDIA GPU.")

    dataset = load_dataset()
    print(f"Training on {len(dataset)} examples · base model: {BASE_MODEL}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    lora_config = LoraConfig(
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )
    training_args = SFTConfig(
        output_dir=str(ADAPTER_DIR),
        model_init_kwargs={
            "quantization_config": quant_config,
            "torch_dtype": torch.bfloat16,
            "device_map": "auto",
        },
        max_length=MAX_SEQ_LENGTH,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        gradient_checkpointing=True,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        optim="paged_adamw_8bit",
        bf16=True,
        logging_steps=5,
        save_strategy="epoch",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=BASE_MODEL,
        args=training_args,
        train_dataset=dataset,
        peft_config=lora_config,
        processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(ADAPTER_DIR))
    print(f"\nDone. LoRA adapter saved to {ADAPTER_DIR}")
    print("Next: python -m finetune.merge_and_export")


if __name__ == "__main__":
    main()
