from rembg import remove
from PIL import Image

input_path = 'static/assets/heart-frame.png'
output_path = 'static/assets/heart-frame.png'

try:
    input_image = Image.open(input_path)
    output_image = remove(input_image)
    output_image.save(output_path)
    print("Fondo eliminado con éxito.")
except Exception as e:
    print(f"Error al eliminar fondo: {e}")
