import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8n.pt")

IMAGE_DIR = BASE_DIR / os.getenv("IMAGE_DIR", "meeting_rooms")
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "outputs")
DATA_DIR = BASE_DIR / "data"

YOLO_CONF = float(os.getenv("YOLO_CONF", "0.25"))
SMALL_GROUP_MAX = int(os.getenv("SMALL_GROUP_MAX", "4"))
BUSY_MIN = int(os.getenv("BUSY_MIN", "5"))
MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", "4"))

IMAGE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
