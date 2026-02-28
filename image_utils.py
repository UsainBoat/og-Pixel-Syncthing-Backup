from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime

def get_date_taken(path):
    """
    Extracts the date taken from an image's EXIF data.
    Falls back to file modification time if EXIF is missing.
    """
    try:
        image = Image.open(path)
        exif_data = image.getexif()
        
        date_taken_str = None
        
        if exif_data:
            # Look for common date tags
            # 36867: DateTimeOriginal
            # 36868: DateTimeDigitized
            # 306: DateTime
            for tag_id in [36867, 36868, 306]:
                if tag_id in exif_data:
                    date_taken_str = exif_data[tag_id]
                    break
        
        if date_taken_str:
            # Format usually: "YYYY:MM:DD HH:MM:SS"
            return datetime.datetime.strptime(date_taken_str, "%Y:%m:%d %H:%M:%S")

    except Exception:
        # If Pillow fails or no EXIF, fallback to modification time
        pass
        
    # Fallback to modification time
    timestamp = os.path.getmtime(path)
    return datetime.datetime.fromtimestamp(timestamp)
