from PIL import Image
import io
import math
import base64

class ImageProcessor:
    @staticmethod
    def split_image(image_bytes: bytes, chunks: int = 2):
        """
        Divide una imagen en N partes horizontales.
        Retorna una lista de dicts con metadata y bytes (base64).
        """
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        chunk_height = math.ceil(height / chunks)
        parts = []
        
        for i in range(chunks):
            top = i * chunk_height
            bottom = min((i + 1) * chunk_height, height)
            
            if top >= height: break
            
            # Crop: (left, top, right, bottom)
            crop = img.crop((0, top, width, bottom))
            
            # Convertir a bytes
            buf = io.BytesIO()
            crop.save(buf, format="PNG") # Usar PNG para lossless
            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            
            parts.append({
                "index": i,
                "total": chunks,
                "data_b64": img_b64,
                "width": width,
                "height": bottom - top
            })
            
        return parts

    @staticmethod
    def merge_images(parts_data: list):
        """
        Reconstruye la imagen final desde las partes procesadas.
        parts_data: lista de dicts {index, data_b64, ...}
        """
        # Ordenar por índice
        parts_data.sort(key=lambda x: x["index"])
        
        images = []
        total_height = 0
        max_width = 0
        
        for part in parts_data:
            img_data = base64.b64decode(part["data_b64"])
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
            total_height += img.height
            max_width = max(max_width, img.width)
            
        # Crear lienzo final
        final_img = Image.new("RGB", (max_width, total_height))
        
        y_offset = 0
        for img in images:
            final_img.paste(img, (0, y_offset))
            y_offset += img.height
            
        # Retornar bytes
        buf = io.BytesIO()
        final_img.save(buf, format="PNG")
        return buf.getvalue()
