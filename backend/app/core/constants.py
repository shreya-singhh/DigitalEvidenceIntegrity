from pathlib import Path

ALLOWED_FILE_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "mp4", "mp3", "docx", "txt"}
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
DEFAULT_UPLOAD_DIRECTORY = Path("uploads")
DEFAULT_REPORT_DIRECTORY = Path("reports")
APP_DESCRIPTION = "Backend API for Digital Evidence Integrity System"
