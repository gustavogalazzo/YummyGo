import cloudinary
import cloudinary.uploader
from flask import current_app

def upload_image(file_to_upload):
    """
    Envia uma imagem para o Cloudinary e retorna a URL segura.
    """
    # Configura o Cloudinary com as chaves do config.py
    cloudinary.config(
        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=current_app.config['CLOUDINARY_API_KEY'],
        api_secret=current_app.config['CLOUDINARY_API_SECRET']
    )
    
    try:
        # Faz o upload
        upload_result = cloudinary.uploader.upload(file_to_upload)
        # Retorna a URL pública da imagem
        return upload_result['secure_url']
    except Exception as e:
        print(f"Erro no upload para Cloudinary: {e}")
        return None