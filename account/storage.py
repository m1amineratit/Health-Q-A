import os
import base64
from django.core.files.storage import Storage
from django.core.files.uploadedfile import UploadedFile
from django.utils.deconstruct import deconstructible
from django.conf import settings
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

@deconstructible
class ImageKitIOStorage(Storage):
    """
    Custom Storage backend for ImageKit.io using the official v3 SDK.
    """
    def __init__(self):
        self.imagekit = ImageKit(
            private_key=settings.IMAGEKIT_PRIVATE_KEY,
            public_key=settings.IMAGEKIT_PUBLIC_KEY,
            url_endpoint=settings.IMAGEKIT_URL_ENDPOINT
        )

    def _save(self, name, content):
        """
        Save the file to ImageKit.io
        """
        # Read content
        if hasattr(content, 'read'):
            file_content = content.read()
        else:
            file_content = content

        # Encode to base64 if needed or pass directly if SDK supports bytes
        # The SDK supports binary data, base64, or URL. 
        # Typically passing bytes/file object works best.
        
        # Prepare upload options
        options = UploadFileRequestOptions(
            use_unique_file_name=True,
            folder='/django-media/',  # Default folder
            overwrite_file=True
        )

        # Upload file
        try:
            upload_response = self.imagekit.upload_file(
                file=file_content,
                file_name=os.path.basename(name),
                options=options
            )
            # Return the file path/name as stored in ImageKit
            return upload_response.name
        except Exception as e:
            # Log error
            raise e

    def url(self, name):
        """
        Return the URL for the file
        """
        return self.imagekit.url({
            "path": name,
            "url_endpoint": settings.IMAGEKIT_URL_ENDPOINT
        })

    def exists(self, name):
        """
        Check if file exists - naive implementation returning False to always allow upload
        Optimally should check API but for storage backend False is safer to trigger _save
        """
        return False
    
    def delete(self, name):
        """
        Delete file from ImageKit - Not strictly required for basic upload but good practice
        Requires file_id which we might not have easily from name unless we query
        """
        pass

    def _open(self, name, mode='rb'):
        """
        We don't support opening files in read mode from this storage directly 
        users should use the URL to access the file.
        """
        raise NotImplementedError("ImageKitIOStorage does not support opening files.")
