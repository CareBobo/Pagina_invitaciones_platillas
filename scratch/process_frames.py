import os
from PIL import Image
import numpy as np

def make_transparent(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return
        
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # Mask for black pixels: pixels where all R, G, B are less than 45
    black_mask = (r < 45) & (g < 45) & (b < 45)
    data[black_mask, 3] = 0 # set alpha to 0
    
    # Soften the edges: for pixels with R, G, B between 45 and 90, scale alpha
    semi_mask = (r >= 45) & (r < 90) & (g >= 45) & (g < 90) & (b >= 45) & (b < 90)
    if np.any(semi_mask):
        brightness = (r[semi_mask].astype(float) + g[semi_mask] + b[semi_mask]) / 3.0
        data[semi_mask, 3] = ((brightness - 45.0) / (90.0 - 45.0) * 255.0).astype(np.uint8)
        
    out_img = Image.fromarray(data)
    
    # Crop transparent borders using getbbox
    bbox = out_img.getbbox()
    if bbox:
        out_img = out_img.crop(bbox)
        
    out_img.save(output_path, "PNG")
    print(f"Processed {input_path} -> {output_path}")

def process_galaxy_bg(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return
    img = Image.open(input_path).convert("RGB")
    img.save(output_path, "JPEG", quality=85)
    print(f"Processed galaxy background {input_path} -> {output_path}")

if __name__ == '__main__':
    # Previous assets (just in case they need to be re-run, but we focus on new ones too)
    make_transparent(
        'C:/Users/USER/.gemini/antigravity-ide/brain/6ffff7ba-cedd-49f6-bbb0-6e723eed0b9c/heart_frame_raw_1781832353006.png',
        'static/assets/heart-frame.png'
    )
    make_transparent(
        'C:/Users/USER/.gemini/antigravity-ide/brain/6ffff7ba-cedd-49f6-bbb0-6e723eed0b9c/circle_frame_raw_1781832367130.png',
        'static/assets/circle-frame.png'
    )
    make_transparent(
        'C:/Users/USER/.gemini/antigravity-ide/brain/6ffff7ba-cedd-49f6-bbb0-6e723eed0b9c/gold_garland_raw_1781832544653.png',
        'static/assets/gold-garland.png'
    )
    
    # New assets for welcome screen
    process_galaxy_bg(
        'C:/Users/USER/.gemini/antigravity-ide/brain/6ffff7ba-cedd-49f6-bbb0-6e723eed0b9c/galaxy_bg_raw_1781834061906.png',
        'static/assets/galaxy-bg.jpg'
    )
    make_transparent(
        'C:/Users/USER/.gemini/antigravity-ide/brain/6ffff7ba-cedd-49f6-bbb0-6e723eed0b9c/envelope_roses_raw_1781834099139.png',
        'static/assets/envelope-roses.png'
    )
    make_transparent(
        'C:/Users/USER/.gemini/antigravity-ide/brain/6ffff7ba-cedd-49f6-bbb0-6e723eed0b9c/wax_seal_raw_1781834134935.png',
        'static/assets/wax-seal.png'
    )
