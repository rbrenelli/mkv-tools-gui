
class ErrorService:
    @staticmethod
    def get_friendly_message(exception: Exception) -> str:
        msg = str(exception)
        if "FileNotFoundError" in msg:
            return "A required file was not found."
        if "PermissionError" in msg:
            return "Permission denied. Check file access rights."
        if "mkvmerge not found" in msg:
            return "MKVToolNix is missing. Please install it."
        if "ffmpeg" in msg and "not found" in msg:
            return "FFmpeg is missing. Please install it."

        return f"An unexpected error occurred: {msg}"
