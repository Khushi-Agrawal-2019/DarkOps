"""
Return Detective — Photo Assignment & GCS Sync
Assigns photos to ~70% of complaints matching defect type and category.
Handles Scenario 5 near-duplicate photo transformations (light cropping/recompression).
Updates DuckDB, Parquet, and BigQuery.
"""

import os
import glob
import random
from dotenv import load_dotenv
from PIL import Image
import pandas as pd
import duckdb

load_dotenv()

PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "complaints")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "out")
COMPLAINTS_PARQUET = os.path.join(OUT_DIR, "complaints.parquet")
DUCKDB_PATH = os.path.join(OUT_DIR, "return_detective.duckdb")
PROJECT_ID = os.getenv("PROJECT_ID", "")
BUCKET_NAME = os.getenv("GCS_BUCKET", f"{PROJECT_ID}-rd-photos")

def prepare_scenario_5_duplicates():
    """Generates 9 slightly transformed versions of the 2 base abuse photos."""
    abuse_dir = os.path.join(PHOTOS_DIR, "abuse")
    os.makedirs(abuse_dir, exist_ok=True)
    
    base_rotten = os.path.join(PHOTOS_DIR, "abuse_base_rotten_apple.jpg")
    base_melted = os.path.join(PHOTOS_DIR, "abuse_base_melted_choc.jpg")
    
    transformed_paths = []
    for idx in range(9):
        base_src = base_rotten if idx < 5 else base_melted
        if not os.path.exists(base_src):
            continue
        im = Image.open(base_src)
        # Apply slight random crop (2-5 pixels off edges)
        w, h = im.size
        crop_box = (idx % 4, (idx + 1) % 4, w - (idx % 3), h - ((idx + 2) % 4))
        cropped = im.crop(crop_box)
        # Apply slight recompression quality (78-86)
        dest_filename = f"abuse_claim_{idx+1}.jpg"
        dest_path = os.path.join(abuse_dir, dest_filename)
        cropped.save(dest_path, format="JPEG", quality=80 + (idx % 6))
        transformed_paths.append((dest_filename, dest_path))
        
    print(f"✓ Created {len(transformed_paths)} near-duplicate photos for Scenario 5 in {abuse_dir}")
    return transformed_paths

def assign_photos_to_complaints():
    print("📸 Assigning complaint photos matching defect types and categories...")
    prepare_scenario_5_duplicates()
    
    # Load complaints
    df_complaints = pd.read_parquet(COMPLAINTS_PARQUET)
    df_items = pd.read_parquet(os.path.join(OUT_DIR, "order_items.parquet"))
    
    item_cat_map = dict(zip(df_items["order_item_id"], df_items["category"]))
    
    # Exclude abuse photos from standard catalog so they are unique to Scenario 5
    available_photos = [p for p in glob.glob(os.path.join(PHOTOS_DIR, "*.jpg")) if "abuse" not in os.path.basename(p)]
    photos_by_type = {}
    for p in available_photos:
        fname = os.path.basename(p)
        t = fname.split("_")[0]
        photos_by_type.setdefault(t, []).append(fname)
        
    assigned_count = 0
    updated_uris = []
    
    for idx, row in df_complaints.iterrows():
        cid = row["complaint_id"]
        c_type = row["type"]
        item_id = row["order_item_id"]
        cat = item_cat_map.get(item_id, "fresh_produce")
        
        # Scenario 5 already has planted abuse photo uris
        if "CMP-ABUSE" in str(cid):
            abuse_num = int(str(cid).split("-")[-1])
            photo_file = f"abuse/abuse_claim_{abuse_num}.jpg"
            uri = f"gs://{BUCKET_NAME}/complaints/{photo_file}"
            updated_uris.append(uri)
            assigned_count += 1
            continue
            
        # ~70% of regular complaints get a photo
        if random.random() < 0.72:
            candidates = photos_by_type.get(c_type, [])
            if not candidates:
                candidates = [os.path.basename(p) for p in available_photos]
            # 10% get a no_defect photo (claim not supported path)
            if random.random() < 0.10 and photos_by_type.get("no"):
                chosen_photo = random.choice(photos_by_type["no"])
            else:
                chosen_photo = random.choice(candidates)
                
            uri = f"gs://{BUCKET_NAME}/complaints/{chosen_photo}"
            updated_uris.append(uri)
            assigned_count += 1
        else:
            updated_uris.append(None)
            
    df_complaints["photo_uri"] = updated_uris
    
    # Save back to Parquet
    df_complaints.to_parquet(COMPLAINTS_PARQUET, index=False)
    print(f"✓ Assigned photos to {assigned_count} / {len(df_complaints)} complaints ({assigned_count/len(df_complaints)*100:.1f}%)")
    
    # Update local DuckDB
    con = duckdb.connect(DUCKDB_PATH)
    con.execute("CREATE OR REPLACE TABLE complaints AS SELECT * FROM read_parquet(?)", [COMPLAINTS_PARQUET])
    con.close()
    print("✓ Synced updated complaints with photo_uris to DuckDB.")
    
    # Upload to GCS if configured
    if PROJECT_ID and PROJECT_ID != "your-gcp-project-id":
        try:
            from google.cloud import storage
            client = storage.Client(project=PROJECT_ID)
            bucket = client.bucket(BUCKET_NAME)
            print(f"☁️  Uploading complaint photos to gs://{BUCKET_NAME}/complaints/ ...")
            all_imgs = glob.glob(os.path.join(PHOTOS_DIR, "**", "*.jpg"), recursive=True)
            for img_path in all_imgs:
                rel = os.path.relpath(img_path, PHOTOS_DIR)
                blob = bucket.blob(f"complaints/{rel}")
                blob.upload_from_filename(img_path)
            print("✅ Photos uploaded to GCS bucket!")
        except Exception as e:
            print(f"ℹ️  GCS upload skipped: {e}")

if __name__ == "__main__":
    assign_photos_to_complaints()
