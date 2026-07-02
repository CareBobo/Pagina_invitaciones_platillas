import os
from PIL import Image
import numpy as np

def remove_checkerboard_rosas():
    # borde-rosas.png has a white and grey (238,238,238) checkerboard background.
    # The roses are red and leaves are green, which do not contain bright white/grey.
    img_path = 'static/assets/borde-rosas.png'
    if not os.path.exists(img_path):
        print(f"File not found: {img_path}")
        return
    
    img = Image.open(img_path).convert("RGBA")
    data = np.array(img)
    
    # Threshold: if all R, G, B are greater than 200, it's background
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    bg_mask = (r > 200) & (g > 200) & (b > 200)
    data[bg_mask, 3] = 0  # set alpha to 0
    
    out_img = Image.fromarray(data)
    out_img.save(img_path, "PNG")
    print(f"Successfully processed {img_path}")

def remove_background_anillos():
    # anillos.png has a white background. Let's do a flood fill from the corners
    # to preserve highlights inside the rings.
    img_path = 'static/assets/anillos.png'
    if not os.path.exists(img_path):
        print(f"File not found: {img_path}")
        return
    
    img = Image.open(img_path).convert("RGBA")
    width, height = img.size
    data = np.array(img)
    
    # We will perform a BFS flood fill from the edges for pixels close to white/grey.
    # A pixel is background-like if R > 200, G > 200, B > 200.
    visited = np.zeros((height, width), dtype=bool)
    queue = []
    
    # Add all edge pixels to the queue
    for x in range(width):
        queue.append((0, x))
        queue.append((height - 1, x))
    for y in range(1, height - 1):
        queue.append((y, 0))
        queue.append((y, width - 1))
        
    for y, x in queue:
        visited[y, x] = True
        
    # BFS
    head = 0
    while head < len(queue):
        cy, cx = queue[head]
        head += 1
        
        # Check if the pixel is background-like
        r, g, b, a = data[cy, cx]
        if r > 180 and g > 180 and b > 180: # background-like
            data[cy, cx, 3] = 0 # set alpha to 0
            
            # Add neighbors
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < height and 0 <= nx < width and not visited[ny, nx]:
                    visited[ny, nx] = True
                    queue.append((ny, nx))
                    
    out_img = Image.fromarray(data)
    out_img.save(img_path, "PNG")
    print(f"Successfully processed {img_path} (flood-filled)")

def generate_silhouette_variants():
    # novios-silueta.png is black with transparent background.
    # Let's create:
    # 1. novios-silueta-gold.png (using #E2B96B)
    # 2. novios-silueta-white.png
    # 3. Overwrite novios-silueta.png with a cleaned version if needed, but let's keep it black.
    img_path = 'static/assets/novios-silueta.png'
    if not os.path.exists(img_path):
        print(f"File not found: {img_path}")
        return
        
    img = Image.open(img_path).convert("RGBA")
    data = np.array(img)
    
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # Blackish mask (R, G, B are low and Alpha is high)
    black_mask = (r < 100) & (g < 100) & (b < 100) & (a > 50)
    
    # 1. Gold variant (#E2B96B -> R=226, G=185, B=107)
    gold_data = data.copy()
    gold_data[black_mask, 0] = 226
    gold_data[black_mask, 1] = 185
    gold_data[black_mask, 2] = 107
    # Make sure alpha is fully opaque for the silhouette
    gold_data[black_mask, 3] = 255
    
    gold_img = Image.fromarray(gold_data)
    gold_img.save('static/assets/novios-silueta-gold.png', "PNG")
    print("Generated static/assets/novios-silueta-gold.png")
    
    # 2. White variant (R=255, G=255, B=255)
    white_data = data.copy()
    white_data[black_mask, 0] = 255
    white_data[black_mask, 1] = 255
    white_data[black_mask, 2] = 255
    white_data[black_mask, 3] = 255
    
    white_img = Image.fromarray(white_data)
    white_img.save('static/assets/novios-silueta-white.png', "PNG")
    print("Generated static/assets/novios-silueta-white.png")

if __name__ == '__main__':
    remove_checkerboard_rosas()
    remove_background_anillos()
    generate_silhouette_variants()
