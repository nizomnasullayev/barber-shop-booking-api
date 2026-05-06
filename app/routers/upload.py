from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.models.user import User
from app.dependencies.auth import get_current_staff_user
from app.utils.cloudinary import upload_image

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/barber-image")
async def upload_barber_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_staff_user)
):
    """
    Upload barber image to Cloudinary (Admin only)
    Returns the image URL
    """
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    # Check file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 5MB"
        )

    try:
        # Upload to Cloudinary
        image_url = upload_image(contents, folder="barbers")

        return {
            "url": image_url,
            "message": "Image uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
