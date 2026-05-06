import cloudinary
import cloudinary.uploader
from app.config import get_settings

settings = get_settings()

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret
)


def upload_image(file_content: bytes, folder: str = "barbers") -> str:
    """
    Upload image to Cloudinary and return the URL

    Args:
        file_content: Image file content as bytes
        folder: Cloudinary folder name (default: barbers)

    Returns:
        Cloudinary image URL
    """
    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file_content,
            folder=folder,
            transformation=[
                {'width': 500, 'height': 500, 'crop': 'fill', 'gravity': 'face'},
            ]
        )

        # Return the secure URL
        return result['secure_url']
    except Exception as e:
        raise Exception(f"Failed to upload image: {str(e)}")


def delete_image(image_url: str) -> bool:
    """
    Delete image from Cloudinary

    Args:
        image_url: The Cloudinary URL of the image

    Returns:
        True if deleted successfully
    """
    try:
        # Extract public_id from URL
        # Example URL: https://res.cloudinary.com/cloud_name/image/upload/v1234567890/barbers/abc123.jpg
        parts = image_url.split('/')
        if 'cloudinary.com' in image_url:
            # Find the public_id (folder/filename without extension)
            public_id_index = parts.index('upload') + 2  # Skip version number
            public_id = '/'.join(parts[public_id_index:]).rsplit('.', 1)[0]

            cloudinary.uploader.destroy(public_id)
            return True
    except Exception as e:
        print(f"Failed to delete image: {str(e)}")
        return False
