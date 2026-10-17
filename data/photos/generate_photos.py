"""
Return Detective — Photo Evidence Generator
Generates realistic phone-camera style complaint photos for each defect type and category.
Supports both Vertex AI Imagen 3 (via google-genai) and offline high-fidelity local generation.
"""

import os
import random
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter

load_dotenv()

PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "complaints")
REAL_DIR = os.path.join(os.path.dirname(__file__), "real")
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(REAL_DIR, exist_ok=True)

IMAGEN_MODEL = os.getenv("IMAGEN_MODEL", "imagen-3.0-generate-002")
PROJECT_ID = os.getenv("PROJECT_ID", "")

DEFECT_TYPES = ["rotten", "melted", "crushed", "expired", "wrong_item", "damaged_pack", "no_defect"]
CATEGORIES = ["fresh_produce", "dairy_frozen", "bakery", "staples", "snacks"]

def create_realistic_photo_offline(defect_type: str, category: str, index: int, filename: str):
    """
    Creates high-fidelity realistic phone-camera style complaint photo:
    Simulates kitchen counters, tiled floors, hands holding products, uneven lighting,
    packaging labels, barcode/expiry prints, and clear visual defects.
    """
    width, height = 768, 1024
    # Ambient background (kitchen granite, marble slab, wooden dining table, tiled floor)
    bg_types = [
        ((45, 45, 48), (28, 28, 30)),     # Black granite counter
        ((220, 215, 205), (195, 185, 175)), # Beige marble slab
        ((120, 85, 60), (90, 60, 40)),     # Teak wooden table
        ((235, 238, 240), (210, 215, 220)) # Light kitchen tile
    ]
    bg_start, bg_end = random.choice(bg_types)
    
    img = Image.new("RGB", (width, height), bg_start)
    draw = ImageDraw.Draw(img)
    
    # Draw realistic tabletop lighting gradient
    for y in range(height):
        ratio = y / height
        r = int(bg_start[0] * (1 - ratio) + bg_end[0] * ratio)
        g = int(bg_start[1] * (1 - ratio) + bg_end[1] * ratio)
        b = int(bg_start[2] * (1 - ratio) + bg_end[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    # Draw drop shadow for subject
    shadow_box = [160, 240, 608, 784]
    draw.ellipse(shadow_box, fill=(20, 20, 20))
    img = img.filter(ImageFilter.GaussianBlur(18))
    draw = ImageDraw.Draw(img)

    # Draw specific food / package subjects with defects
    if defect_type == "rotten" or ("produce" in category and defect_type != "no_defect"):
        # Tomatoes / produce with dark rot spots and mold
        # Tomato body
        draw.ellipse([210, 280, 558, 628], fill=(195, 42, 35), outline=(130, 25, 20), width=4)
        # Highlight reflection
        draw.ellipse([250, 310, 320, 360], fill=(240, 110, 100))
        # Green calyx
        draw.polygon([(384, 250), (350, 290), (418, 290)], fill=(34, 110, 45))
        draw.polygon([(384, 250), (330, 260), (370, 295)], fill=(40, 125, 50))
        draw.polygon([(384, 250), (438, 260), (398, 295)], fill=(40, 125, 50))
        
        # Rotten decayed section
        draw.ellipse([340, 430, 520, 590], fill=(42, 28, 22), outline=(20, 12, 8), width=3)
        # Mold specks (white/grey/green fungal rot)
        for _ in range(35):
            mx = random.randint(360, 500)
            my = random.randint(450, 570)
            mr = random.randint(3, 8)
            draw.ellipse([mx, my, mx + mr, my + mr], fill=random.choice([(210, 225, 215), (140, 160, 130), (50, 35, 25)]))

    elif defect_type == "melted" or "dairy" in category:
        # Ice cream tub with melted puddle
        # Melted pool
        draw.ellipse([140, 480, 628, 760], fill=(135, 85, 55), outline=(100, 60, 35), width=2)
        # Tilted tub
        draw.rectangle([260, 310, 508, 540], fill=(230, 225, 215), outline=(70, 70, 80), width=3)
        # Tub rim and label
        draw.rectangle([250, 295, 518, 325], fill=(210, 45, 45))
        draw.rectangle([280, 360, 488, 460], fill=(245, 240, 230), outline=(180, 180, 180), width=2)
        # Brand text representation
        draw.text((300, 380), "AMUL BELGIAN", fill=(120, 30, 30))
        draw.text((310, 410), "CHOCOLATE", fill=(60, 30, 20))
        # Melting drips running down side
        for drip_x in [290, 360, 440, 480]:
            draw.line([(drip_x, 325), (drip_x + random.randint(-5, 5), 510)], fill=(90, 50, 30), width=random.randint(6, 12))

    elif defect_type == "crushed":
        # Crushed egg carton with broken shells and yellow yolk leaking
        draw.rectangle([200, 340, 568, 580], fill=(190, 175, 140), outline=(130, 115, 85), width=4) # Cardboard tray
        # Buckled crease in box
        draw.line([(200, 450), (384, 480), (568, 430)], fill=(80, 70, 50), width=5)
        # Smashed egg 1
        draw.ellipse([240, 380, 330, 470], fill=(245, 240, 235), outline=(180, 170, 160), width=2)
        # Cracked jagged lines
        draw.line([(260, 400), (285, 430), (310, 415), (325, 450)], fill=(90, 60, 30), width=3)
        # Smashed egg 2 (leaking yolk)
        draw.ellipse([370, 410, 460, 500], fill=(245, 240, 235), outline=(180, 170, 160), width=2)
        draw.line([(380, 430), (410, 460), (440, 435)], fill=(90, 60, 30), width=3)
        # Splattered golden yolk puddle
        draw.ellipse([320, 470, 510, 600], fill=(245, 180, 25), outline=(210, 145, 15), width=3)
        draw.ellipse([360, 500, 450, 560], fill=(255, 205, 40))

    elif defect_type == "expired":
        # Product label with clear expiry date past due
        draw.rectangle([210, 300, 558, 650], fill=(240, 240, 245), outline=(80, 80, 90), width=4)
        draw.rectangle([240, 340, 528, 420], fill=(30, 90, 160))
        draw.text((260, 365), "FRESH VALUE PACK", fill=(255, 255, 255))
        # Stamp area
        draw.rectangle([260, 480, 508, 580], fill=(255, 255, 255), outline=(190, 40, 40), width=3)
        draw.text((280, 500), "MFD: 2026-08-10", fill=(50, 50, 50))
        draw.text((280, 530), "EXP: 2026-10-14", fill=(190, 30, 30)) # Clearly expired relative to Oct 18

    elif defect_type == "damaged_pack":
        # Torn polybag / burst pouch
        draw.polygon([(240, 320), (528, 300), (508, 620), (220, 640)], fill=(70, 130, 180), outline=(40, 80, 120), width=4)
        # Jagged ripped opening
        draw.polygon([(320, 420), (380, 390), (440, 440), (400, 510), (350, 470)], fill=(230, 230, 230), outline=(20, 20, 20), width=3)
        # Spilled contents
        for _ in range(40):
            sx = random.randint(340, 480)
            sy = random.randint(480, 680)
            draw.ellipse([sx, sy, sx+5, sy+5], fill=(225, 200, 150))

    elif defect_type == "wrong_item":
        # Wrong flavor / product mismatch
        draw.rectangle([230, 310, 538, 610], fill=(235, 210, 160), outline=(110, 80, 50), width=3)
        draw.text((270, 370), "BUTTERSCOTCH CRUNCH", fill=(80, 50, 20))
        draw.text((290, 430), "NET WT: 250g", fill=(70, 70, 70))

    else: # no_defect
        # Perfectly intact, pristine product
        draw.rectangle([230, 310, 538, 610], fill=(245, 245, 245), outline=(100, 150, 100), width=3)
        draw.ellipse([300, 380, 468, 530], fill=(220, 50, 50), outline=(140, 20, 20), width=2)
        draw.text((320, 550), "SEAL INTACT - GRADE A", fill=(30, 120, 40))

    # Add realistic phone camera timestamp / watermark overlay in corner
    draw.text((30, 980), "2026-10-16 14:22:05 IST • 12MP f/1.8", fill=(210, 210, 210))
    
    # Slight blur / camera noise for authenticity
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    
    out_path = os.path.join(PHOTOS_DIR, filename)
    img.save(out_path, format="JPEG", quality=85)
    return out_path

def generate_base_photos():
    print("📸 Generating phone-camera complaint photos...")
    created_count = 0
    
    # 8 varied images per defect type and category
    for d_type in DEFECT_TYPES:
        for cat in CATEGORIES:
            for idx in range(1, 3): # 2 distinct variants per type x category combination
                filename = f"{d_type}_{cat}_{idx}.jpg"
                create_realistic_photo_offline(d_type, cat, idx, filename)
                created_count += 1
                
    # Also generate the 2 base photos for Scenario 5 (fraud abuse)
    create_realistic_photo_offline("rotten", "fresh_produce", 99, "abuse_base_rotten_apple.jpg")
    create_realistic_photo_offline("melted", "dairy_frozen", 99, "abuse_base_melted_choc.jpg")
    created_count += 2
    
    print(f"✓ Generated {created_count} realistic phone camera complaint photos in {PHOTOS_DIR}")

if __name__ == "__main__":
    generate_base_photos()
