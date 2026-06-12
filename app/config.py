"""Central configuration. Change models here to swap brains."""

from pathlib import Path

# --- Ollama models (must be pulled first: `ollama pull <name>`) ---
CHAT_MODEL = "qwen3:8b"           # main chat / coding model
VISION_MODEL = "qwen2.5vl:7b"     # understands images & video frames
EMBED_MODEL = "nomic-embed-text"  # embeddings for document search

# --- Generation models (downloaded from Hugging Face on first use) ---
IMAGE_MODEL = "stabilityai/sdxl-turbo"
VIDEO_MODEL = "Lightricks/LTX-Video"

# --- Voice ---
WHISPER_MODEL = "small"   # speech-to-text; "large-v3" = best accuracy, slower
TTS_VOICE = "af_heart"    # Kokoro voice for spoken replies

# --- Retrieval reranker (improves document answers) ---
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
RERANK_CANDIDATES = 20    # chunks fetched before reranking down to TOP_K

# --- Paths ---
ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = ROOT / "data" / "documents"
VECTOR_DB_DIR = ROOT / "data" / "vectordb"
OUTPUTS_DIR = ROOT / "outputs"
CHATLOG_DIR = ROOT / "data" / "chatlogs"     # raw chats, used as training data
TRAINING_DIR = ROOT / "data" / "training"    # prepared fine-tuning dataset
WORKSPACE_DIR = ROOT / "data" / "workspace"  # agent-run Python works here
PERSONAS_DIR = ROOT / "data" / "personas"    # editable specialist prompts
SKILLS_DIR = ROOT / "data" / "skills"        # functions the agent taught itself
PLAYBOOKS_DIR = ROOT / "data" / "playbooks"  # authored reusable workflows
BACKUPS_DIR = ROOT / "data" / "backups"      # originals of approved file edits

# Folders the agent may read and propose (approval-gated) edits in.
EDIT_ROOTS = [Path.home()]

# --- RAG settings ---
CHUNK_SIZE = 1200        # characters per chunk
CHUNK_OVERLAP = 200
TOP_K = 5                # chunks retrieved per question

# File types the document indexer will read
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".sql", ".sh",
    ".html", ".css", ".json", ".yaml", ".yml", ".toml", ".md", ".txt",
}

# --- Video understanding ---
VIDEO_FRAMES_TO_SAMPLE = 8  # frames sent to the vision model per video

for _dir in (
    DOCUMENTS_DIR, VECTOR_DB_DIR, OUTPUTS_DIR,
    CHATLOG_DIR, TRAINING_DIR, WORKSPACE_DIR, PERSONAS_DIR, SKILLS_DIR,
    PLAYBOOKS_DIR, BACKUPS_DIR,
):
    _dir.mkdir(parents=True, exist_ok=True)
