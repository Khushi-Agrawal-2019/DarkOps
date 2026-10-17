"""
Return Detective — Synthetic Data Generator
Generates realistic 60-day operational quick-commerce dataset with 6 planted root causes.
Outputs Parquet files to data/out/.
"""

import os
import random
import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
from data.scenarios import SCENARIO_SETTINGS

# Set seed for reproducibility
random.seed(SCENARIO_SETTINGS.seed)
np.random.seed(SCENARIO_SETTINGS.seed)

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT_DIR, exist_ok=True)

# Anchor date: 2026-10-18 (prototype deadline)
END_DATE = datetime.datetime(2026, 10, 18, 23, 59, 59)
START_DATE = END_DATE - timedelta(days=60)

STORES = [
    {"store_id": "S1", "name": "Koramangala DarkStore", "city": "Bengaluru", "lat": 12.9352, "lon": 77.6245},
    {"store_id": "S2", "name": "Indiranagar DarkStore", "city": "Bengaluru", "lat": 12.9784, "lon": 77.6408},
    {"store_id": "S3", "name": "HSR Layout DarkStore", "city": "Bengaluru", "lat": 12.9121, "lon": 77.6446},
    {"store_id": "S4", "name": "Whitefield DarkStore", "city": "Bengaluru", "lat": 12.9698, "lon": 77.7499},
]

ZONES = []
for s in STORES:
    for z_idx in range(1, 5):
        ZONES.append({
            "zone_id": f"{s['store_id']}-Z{z_idx}",
            "store_id": s["store_id"],
            "name": f"{s['name'].split()[0]} Sector {z_idx}",
            "avg_distance_km": round(1.2 + (z_idx * 0.9) + random.uniform(-0.2, 0.2), 2)
        })

SUPPLIERS = [
    {"supplier_id": "SUP-001", "name": "GreenLeaf Farms", "category": "fresh_produce", "city": "Bengaluru", "rating": 4.1},
    {"supplier_id": "SUP-002", "name": "Heritage Dairies", "category": "dairy_frozen", "city": "Bengaluru", "rating": 4.7},
    {"supplier_id": "SUP-003", "name": "Amul India West Hub", "category": "dairy_frozen", "city": "Anand", "rating": 4.9},
    {"supplier_id": "SUP-004", "name": "The Daily Loaf Artisans", "category": "bakery", "city": "Bengaluru", "rating": 4.5},
    {"supplier_id": "SUP-005", "name": "Modern Bakery Foods", "category": "bakery", "city": "Bengaluru", "rating": 4.2},
    {"supplier_id": "SUP-006", "name": "Nandini KMF Dairy", "category": "dairy_frozen", "city": "Bengaluru", "rating": 4.8},
    {"supplier_id": "SUP-007", "name": "FreshRoots Organic", "category": "fresh_produce", "city": "Hosur", "rating": 4.4},
    {"supplier_id": "SUP-008", "name": "Godrej Tyson Poultry", "category": "dairy_frozen", "city": "Bengaluru", "rating": 4.6},
    {"supplier_id": "SUP-009", "name": "Mother Dairy South", "category": "dairy_frozen", "city": "Bengaluru", "rating": 4.7},
    {"supplier_id": "SUP-010", "name": "Kwality Ice Creams Ltd", "category": "dairy_frozen", "city": "Bengaluru", "rating": 4.6},
]

# Real Indian Q-Commerce SKUs (~300)
SKU_CATALOG = [
    # Produce
    ("SKU-001", "Fresh Hybrid Tomatoes 500g", "fresh_produce", 38, "ambient"),
    ("SKU-002", "Onion Sambhar 1kg", "fresh_produce", 45, "ambient"),
    ("SKU-003", "Potato Jyoti 1kg", "fresh_produce", 32, "ambient"),
    ("SKU-004", "Shimla Apple 4-pack", "fresh_produce", 140, "chilled"),
    ("SKU-005", "Robusta Banana 500g", "fresh_produce", 35, "ambient"),
    ("SKU-006", "Coriander Bunch 100g", "fresh_produce", 15, "chilled"),
    ("SKU-007", "Palak Spinach 250g", "fresh_produce", 22, "chilled"),
    ("SKU-008", "Cucumber English 500g", "fresh_produce", 28, "ambient"),
    # Dairy & Frozen
    ("SKU-009", "Amul Belgian Chocolate Ice Cream 500ml", "dairy_frozen", 220, "frozen"),
    ("SKU-010", "Kwality Walls Feast Dark Choco 90ml", "dairy_frozen", 50, "frozen"),
    ("SKU-011", "Farm Fresh White Eggs 6-pack", "dairy_frozen", 54, "ambient"),
    ("SKU-012", "Nandini Toned Fresh Milk 500ml", "dairy_frozen", 24, "chilled"),
    ("SKU-013", "Milky Mist Paneer 200g", "dairy_frozen", 95, "chilled"),
    ("SKU-014", "Amul Butter Salted 100g", "dairy_frozen", 58, "chilled"),
    ("SKU-015", "McCain French Fries 450g", "dairy_frozen", 135, "frozen"),
    ("SKU-016", "Mother Dairy Curd 400g", "dairy_frozen", 40, "chilled"),
    ("SKU-017", "Amul Vanilla Magic Tub 1L", "dairy_frozen", 180, "frozen"),
    ("SKU-018", "Eggoz Nutrition Brown Eggs 6-pack", "dairy_frozen", 85, "ambient"),
    # Bakery
    ("SKU-019", "Artisan Sourdough White Bread 400g", "bakery", 65, "ambient"),
    ("SKU-020", "English Oven 100% Atta Bread 400g", "bakery", 55, "ambient"),
    ("SKU-021", "The Daily Loaf Garlic Bread 200g", "bakery", 75, "ambient"),
    ("SKU-022", "Modern Pav Buns 6-pack", "bakery", 30, "ambient"),
]

# Expand catalog to ~300 items systematically
for idx in range(23, 301):
    cat = random.choice(["fresh_produce", "dairy_frozen", "bakery", "staples", "snacks", "beverages"])
    req = "frozen" if cat == "dairy_frozen" and idx % 3 == 0 else ("chilled" if cat in ("dairy_frozen", "fresh_produce") and idx % 2 == 0 else "ambient")
    price = random.randint(20, 350)
    SKU_CATALOG.append((f"SKU-{idx:03d}", f"Premium Daily Item {idx} ({cat})", cat, price, req))

# 40+ authentic Indian-English complaint templates per type
COMPLAINT_TEMPLATES = {
    "rotten": [
        "tomatoes are rotten inside and smelling horrible",
        "tamatar sad gaya hai pura, cannot use for cooking",
        "fungus on the bottom, completely spoiled vegetables",
        "black spots all over and foul smell coming out",
        "half the pack is rotten and squishy, please refund",
        "stale and rotten produce delivered, quality is getting worse",
        "smelling rotten inside sealed plastic, had to throw away",
        "vegetable is totally decayed and full of mush",
        "brown mushy rot inside, completely unusable",
        "very bad rotten smell, food safety hazard",
        "tomatoes have worms and rot, look at the photo",
        "completely spoiled and foul, refund immediately",
        "half rotten tomatoes sent, very bad selection by store",
        "black fungus inside the skin, had to throw entire 500g",
        "rotten and smelly, worst quick commerce experience",
        "spoiled completely, smelling like garbage",
        "tamatar bilkul sada hua nikla",
        "fungal rot visible clearly on all pieces",
        "rotten inside although skin looked ok outside",
        "entire packet is rotten and leaking juice",
        "bad foul rot, please credit refund to wallet",
        "stinking rotten tomatoes, family fell sick risk",
        "decayed produce sent by indiranagar store",
        "spoiled rotten batch, check your stock",
        "disgusting rotten condition on delivery",
        "badly rotten and decaying vegetables",
        "smelly fungus rot inside box",
        "completely decomposed items sent",
        "rotten and crushed rotten pieces inside",
        "full pack rotten, waste of money",
        "rotten tomato batch, please take back",
        "decayed black fungus everywhere",
        "terrible rot, unhygienic item delivered",
        "stale spoiled rotten condition",
        "rotten and smells like sewage",
        "all tomatoes rotten from inside",
        "unusable rotten veggies delivered",
        "spoiled rotten items, please refund rupee amount",
        "worst quality rotten tomatoes received",
        "rotten and damp with white mold",
        "rotten fruit delivered today morning",
        "totally decayed and smelling putrid"
    ],
    "melted": [
        "icecream fully melted when it came, pure soup",
        "pure liquid ice cream received, carton completely soggy",
        "chocolates are melted and sticky all over wrapper",
        "frozen peas thawed completely and leaking warm water",
        "kulfi melted into milkshake, packet ruined inside bag",
        "ice cream was delivered completely warm and melted",
        "melted chocolate tub leaked on other items",
        "frozen item melted and thawed, no dry ice used?",
        "total melted liquid delivered in 20 mins",
        "ice cream tub had no ice at all, pure melted cream",
        "melted ice cream leaked inside delivery bag",
        "chocolate ice cream melted into brown liquid",
        "thawed frozen snack, soggy and warm",
        "ice cream melted completely, carton soaked",
        "cone is totally soft and ice cream melted out",
        "hot liquid ice cream received in afternoon",
        "pure milk liquid, entire icecream melted away",
        "icecream bar had melted and refrozen into weird blob",
        "melted tub delivered by rider, bag was hot",
        "frozen dessert arrived as warm liquid",
        "belgian chocolate tub melted and sticky",
        "warm melted ice cream, please refund full price",
        "melted mess inside bag, everything sticky",
        "carton soaked with melted chocolate liquid",
        "totally thawed frozen dessert, warm to touch",
        "melted slush instead of solid ice cream",
        "completely melted dairy item, cannot refreeze",
        "delivered melted in afternoon sun",
        "melted cream dripping from sides of box",
        "ice cream liquid leaking out of packaging",
        "thawed and warm ice cream tub received",
        "melted into sweet water, utterly disappointed",
        "rider delivered melted ice cream after 25 mins",
        "liquid melted tub, please issue instant refund",
        "chilled frozen chain broken, melted goods",
        "ice cream completely melted down to liquid state",
        "melted and spilled inside brown bag",
        "frozen bar completely melted off the stick",
        "warm melted dessert, ruin of party plans",
        "icecream tub soft mush and liquid",
        "melted dairy product, safety concern",
        "unfrozen and warm liquid icecream"
    ],
    "crushed": [
        "eggs completely smashed inside box, yolk everywhere",
        "all 6 eggs broken and liquid leaking into paper bag",
        "doodh packet burst inside bag, everything wet and ruined",
        "chips packet crushed into powder like sand",
        "bread loaf squished flat like papad, completely damaged",
        "egg carton was squished under heavy detergent bottle",
        "four out of six eggs smashed to pieces",
        "packer packed heavy items directly on top of eggs",
        "crushed bread and damaged eggs received",
        "egg shells broken and yolk dripping from bag bottom",
        "box crushed from top, contents totally damaged",
        "crushed food packet, seal broken and leaking",
        "eggs smashed during packing, no bubble wrap used",
        "packer carelessly crushed egg carton under flour bag",
        "bread totally flattened, cannot make sandwiches",
        "eggs cracked and leaking foul yellow liquid",
        "3 eggs smashed, messy bag delivered",
        "crushed biscuits and broken eggs",
        "careless packing at store, egg pack crushed completely",
        "crushed item in delivery bag, box torn",
        "crushed eggs everywhere, spoiled rest of groceries",
        "severe crushing damage to delicate eggs",
        "flattened egg carton, multiple eggs broken",
        "half the eggs crushed to liquid mess",
        "egg packet crushed by packer",
        "crushed carton and smashed eggs",
        "delicate bakery items squashed completely",
        "eggs broke because packed without care",
        "crushed package delivered by store",
        "eggs cracked and ruined inside tray",
        "completely broken eggs, yolk everywhere in bag",
        "bread loaf crushed into ball of dough",
        "packet crushed, outer cardboard broken",
        "smashed eggs in delivery, unacceptable packing",
        "terrible packing, egg carton smashed completely",
        "crushed contents inside delivery packet",
        "cracked eggs with liquid oozing out",
        "crushed bakery box, bread ruined",
        "all eggs broke during packing/transit",
        "smashed egg shell mess in paper bag",
        "crushed items, need immediate refund",
        "yolk leaking from crushed egg box"
    ],
    "expired": [
        "expiry date passed yesterday itself, old stock sent",
        "packet already expired 2 days back, why delivering this?",
        "fungus grew because expired batch sent from warehouse",
        "date is smudged but clearly old stock past expiry",
        "milk expiry was today morning, already sour",
        "delivered product with yesterday's use-by date",
        "stale expired food sent to customer",
        "product past shelf life by 3 days",
        "item expired on 14th oct, delivered on 16th",
        "expired food item delivered, health hazard",
        "sour taste because milk is past expiry date",
        "batch date is 2 months old and expired",
        "expired goods cleared from dark store shelf",
        "passed expiry date, please refund immediately",
        "already expired on package label",
        "received expired batch of food item",
        "use by date was 2 days ago",
        "expired stock received, check inventory",
        "item past best before date",
        "selling expired stock on quick commerce",
        "expired dairy item sent",
        "date code clearly says expired yesterday",
        "moldy item past its expiry date",
        "expired grocery delivered, unacceptable",
        "stale expired product with foul taste",
        "expired pack delivered in evening",
        "check expiry before packing! expired item received",
        "packet is past expiry date",
        "expired product sent by koramangala store",
        "sour expired curd packet",
        "expired food packet received today",
        "why send expired goods? refund please",
        "use before date has expired",
        "old expired stock delivered",
        "item has crossed expiry date",
        "expired bread delivered with mold",
        "stale expired milk received",
        "expired item sent, please refund inr",
        "clearly expired according to back print",
        "product expired last week",
        "shelf life expired, please refund",
        "expired pack received in order"
    ],
    "wrong_item": [
        "ordered vanilla got butterscotch instead",
        "wrong brand delivered by dark store",
        "sent 250g instead of 500g pack that I paid for",
        "ordered brown bread received white bread",
        "received different flavor than what was ordered",
        "wrong item packed in order bag",
        "ordered toned milk got full cream",
        "item delivered is completely different SKU",
        "ordered organic tomatoes, received normal hybrid",
        "wrong quantity and wrong item delivered",
        "different product inside packaging",
        "wrong ice cream variant received",
        "picker packed incorrect item in hurry",
        "received someone else's item in bag",
        "wrong egg brand delivered",
        "ordered 1kg pack got 500g pack",
        "wrong item sent, please arrange return/refund",
        "completely wrong grocery delivered",
        "wrong brand and wrong size",
        "picker picked wrong product code",
        "item mismatch between app and bag",
        "ordered sugar-free, sent regular sweet",
        "item delivered does not match invoice",
        "wrong item received, please refund difference",
        "incorrect item sent in parcel",
        "sent salted butter instead of unsalted",
        "wrong SKU packed by darkstore picker",
        "mismatched grocery item received",
        "ordered 6-pack received 4-pack",
        "wrong flavor delivered today",
        "item does not match order summary",
        "wrong packet handed over by delivery",
        "different item from what was paid",
        "wrong product variant delivered",
        "incorrect item received in package",
        "ordered dairy milk got 5-star",
        "wrong SKU delivered, please refund",
        "item replaced without asking",
        "different brand delivered than ordered",
        "wrong item in darkstore bag",
        "incorrect grocery item sent",
        "mismatched product received"
    ],
    "damaged_pack": [
        "seal was already broken when delivered",
        "outer polybag torn and dirty, dust on food",
        "box crushed from corner and plastic seal open",
        "packaging punctured and food exposed to air",
        "torn packet leaking contents in bag",
        "open seal delivered, cannot consume safely",
        "outer wrapper torn open, unhygienic",
        "punctured pack, liquid dripping outside",
        "broken tamper seal on container",
        "packaging ripped and contents exposed",
        "torn bag, grains spilled inside grocery sack",
        "seal opened, half contents spilled",
        "torn wrapper, item damaged in transport",
        "dirty and torn package delivered",
        "burst packet with tape stuck on it",
        "damaged box with broken safety seal",
        "container lid cracked open",
        "leaking pouch with tear at corner",
        "tampered packaging delivered to door",
        "torn outer cover, contents exposed to dust",
        "damaged packaging, please issue refund",
        "pouch torn from side, milk leaking",
        "box squashed and seal broken",
        "punctured packet received from store",
        "damaged pack delivered today",
        "plastic cover ripped open",
        "torn parcel with damaged contents",
        "box opened before delivery",
        "damaged wrapping on grocery items",
        "broken bottle cap and leaking liquid",
        "torn seal, unhygienic condition",
        "punctured and dirty package",
        "damaged packet delivered, safety concern",
        "ripped polybag, food item exposed",
        "broken package seal",
        "damaged container with cracked plastic",
        "torn packet delivered in bag",
        "punctured carton leaking fluids",
        "damaged seal on food tub",
        "dirty torn packaging, unhygienic",
        "compromised packaging received",
        "tampered packet, refund needed"
    ]
}

def generate_all_data():
    print("🚀 Starting Return Detective synthetic data generation...")
    
    # 1. Stores & Zones & Suppliers
    df_stores = pd.DataFrame(STORES)
    df_zones = pd.DataFrame(ZONES)
    df_suppliers = pd.DataFrame(SUPPLIERS)
    
    # 2. SKUs
    sku_records = []
    for s in SKU_CATALOG:
        sku_records.append({
            "sku_id": s[0],
            "name": s[1],
            "category": s[2],
            "price_inr": s[3],
            "storage_req": s[4]
        })
    df_skus = pd.DataFrame(sku_records)

    # 3. Weather Daily (60 days x 4 stores)
    weather_records = []
    curr_date = START_DATE.date()
    end_d = END_DATE.date()
    while curr_date <= end_d:
        day_diff = (end_d - curr_date).days
        # Normal BLR weather: 28-32C, but hot spell 4-8 days ago reaching 36.5C
        base_temp = 36.2 if 4 <= day_diff <= 8 else 30.5
        for s in STORES:
            max_t = round(base_temp + random.uniform(-0.8, 1.2), 1)
            min_t = round(max_t - random.uniform(9.0, 12.0), 1)
            weather_records.append({
                "date": curr_date.isoformat(),
                "store_id": s["store_id"],
                "max_temp_c": max_t,
                "min_temp_c": min_t,
                "humidity_pct": random.randint(45, 80),
                "rainfall_mm": round(float(np.random.exponential(1.5)) if random.random() < 0.2 else 0.0, 1)
            })
        curr_date += timedelta(days=1)
    df_weather = pd.DataFrame(weather_records)

    # 4. Batches
    # Ensure Tomato Batch B-4471 from GreenLeaf Farms exists!
    batch_records = []
    # Planted Scenario 1 batch:
    batch_records.append({
        "batch_id": SCENARIO_SETTINGS.s1_batch_id,
        "sku_id": "SKU-001", # Fresh Hybrid Tomatoes 500g
        "supplier_id": "SUP-001", # GreenLeaf Farms
        "received_at": (END_DATE - timedelta(days=3, hours=10)).isoformat(),
        "expiry": (END_DATE + timedelta(days=4)).isoformat(),
        "storage_unit": "ambient-01"
    })
    
    # Generate remaining batches
    batch_counter = 1000
    for sku in sku_records:
        # 3-5 batches per sku across 60 days
        for b_i in range(4):
            batch_counter += 1
            rec_days_ago = random.randint(1, 58)
            rec_at = END_DATE - timedelta(days=rec_days_ago, hours=random.randint(1, 23))
            shelf_days = 7 if sku["storage_req"] == "chilled" else (180 if sku["storage_req"] == "frozen" else 14)
            exp_at = rec_at + timedelta(days=shelf_days)
            unit_prefix = "F" if sku["storage_req"] == "frozen" else ("C" if sku["storage_req"] == "chilled" else "A")
            unit_id = f"{unit_prefix}{random.choice([1, 2])}"
            sup_match = [sup["supplier_id"] for sup in SUPPLIERS if sup["category"] == sku["category"]]
            sup_id = random.choice(sup_match) if sup_match else "SUP-001"
            batch_records.append({
                "batch_id": f"B-{batch_counter}",
                "sku_id": sku["sku_id"],
                "supplier_id": sup_id,
                "received_at": rec_at.isoformat(),
                "expiry": exp_at.isoformat(),
                "storage_unit": unit_id
            })
    df_batches = pd.DataFrame(batch_records)

    # Pre-index batches by sku_id (exclude B-4471 from default pool so it only appears in planted 3-day window)
    batches_by_sku = {}
    for b in batch_records:
        if b["batch_id"] != SCENARIO_SETTINGS.s1_batch_id:
            batches_by_sku.setdefault(b["sku_id"], []).append(b)

    # 5. Orders & Order Items & Fulfilment & Deliveries & Complaints
    order_records = []
    order_item_records = []
    fulfilment_records = []
    delivery_records = []
    complaint_records = []

    # Pickers & Packers
    pickers = [f"PKR-{i:03d}" for i in range(1, 35)]
    packers = [f"PK-{i:03d}" for i in range(301, 325)] # PK-308 is the scenario 4 negligent egg packer
    riders = [f"RD-{i:03d}" for i in range(1, 90)]

    # Customers (pool of 12,000 customers + 3 fraud accounts)
    customers = [f"CUST-{i:05d}" for i in range(1, 12000)]
    fraud_customers = list(SCENARIO_SETTINGS.s5_customers)

    order_id_counter = 100000
    item_id_counter = 500000
    complaint_id_counter = 800000

    print("  Generating ~40,000 orders across 60 days...")
    
    total_days = 60
    for day_idx in range(total_days):
        day_date = START_DATE + timedelta(days=day_idx)
        is_weekend = day_date.weekday() >= 5
        # Weekend volume +20%
        daily_order_target = int(random.randint(620, 720) * (1.20 if is_weekend else 1.0))
        days_from_end = (END_DATE - day_date).days

        for _ in range(daily_order_target):
            order_id_counter += 1
            order_id = f"ORD-{order_id_counter}"
            store = random.choice(STORES)
            store_id = store["store_id"]
            
            # Realistic hour distribution: peaks 7-10 PM and 8-10 AM
            hour_weights = [1, 1, 1, 1, 1, 2, 4, 8, 9, 8, 6, 6, 7, 6, 5, 5, 6, 8, 12, 14, 13, 8, 4, 2]
            order_hour = random.choices(range(24), weights=hour_weights)[0]
            order_time = day_date.replace(hour=order_hour, minute=random.randint(0, 59), second=random.randint(0, 59))
            
            customer_id = random.choice(customers)
            # Pick 2 to 4 items per order
            num_items = random.choices([1, 2, 3, 4, 5], weights=[15, 45, 25, 10, 5])[0]
            chosen_skus = random.sample(SKU_CATALOG, num_items)
            
            order_total = 0
            order_has_egg = False
            order_has_icecream = False
            order_has_tomato_b4471 = False
            order_items_this_order = []

            for sku in chosen_skus:
                item_id_counter += 1
                item_id = f"ITEM-{item_id_counter}"
                sku_id = sku[0]
                price = sku[3]
                qty = 1 if sku[2] in ("dairy_frozen", "fresh_produce") else random.choice([1, 2])
                order_total += price * qty
                
                # Assign batch
                avail_batches = batches_by_sku.get(sku_id, [])
                assigned_batch = random.choice(avail_batches)["batch_id"] if avail_batches else "B-1001"
                
                # Check scenario 1: Planted Tomato B-4471 in last 3 days across S1, S2, S3
                if sku_id == "SKU-001" and store_id in ("S1", "S2", "S3") and days_from_end <= SCENARIO_SETTINGS.s1_days_active:
                    assigned_batch = SCENARIO_SETTINGS.s1_batch_id
                    order_has_tomato_b4471 = True
                
                if sku[4] == "frozen":
                    order_has_icecream = True
                if sku[0] == "SKU-011": # Farm fresh eggs
                    order_has_egg = True

                item_rec = {
                    "order_item_id": item_id,
                    "order_id": order_id,
                    "sku_id": sku_id,
                    "batch_id": assigned_batch,
                    "quantity": qty,
                    "unit_price_inr": price,
                    "storage_req": sku[4],
                    "category": sku[2]
                }
                order_item_records.append(item_rec)
                order_items_this_order.append(item_rec)

            order_records.append({
                "order_id": order_id,
                "store_id": store_id,
                "customer_id": customer_id,
                "ordered_at": order_time.isoformat(),
                "total_inr": order_total,
                "status": "delivered"
            })

            # Fulfilment
            picker_id = random.choice(pickers)
            # Scenario 4: At store S3, packer PK-308 handles high proportion of egg orders
            if store_id == SCENARIO_SETTINGS.s4_store_id and order_has_egg and random.random() < 0.45:
                packer_id = SCENARIO_SETTINGS.s4_packer_id
            else:
                packer_id = random.choice(packers)
            
            packing_mat = "insulated_bubble" if order_has_icecream else ("cardboard_tray" if order_has_egg else "standard_bag")
            pack_time = order_time + timedelta(minutes=random.randint(3, 8))
            fulfilment_records.append({
                "order_id": order_id,
                "picker_id": picker_id,
                "packer_id": packer_id,
                "packing_material": packing_mat,
                "packed_at": pack_time.isoformat()
            })

            # Delivery
            store_zones = [z for z in ZONES if z["store_id"] == store_id]
            zone = random.choice(store_zones)
            zone_id = zone["zone_id"]
            rider_id = random.choice(riders)

            # Scenario 3: S2 zone 3 deliveries > 18 min on hot days (>35C)
            # Find max temp for this day
            day_temp = 36.2 if 4 <= days_from_end <= 8 else 30.5
            is_s2_z3_hot = (store_id == SCENARIO_SETTINGS.s3_store_id and 
                            zone_id == SCENARIO_SETTINGS.s3_zone_id and 
                            day_temp >= SCENARIO_SETTINGS.s3_temp_threshold_c and 
                            12 <= order_hour <= 17)
            
            if is_s2_z3_hot:
                delivery_minutes = random.uniform(19.0, 24.5)
            else:
                delivery_minutes = random.uniform(8.0, 16.5)

            delivery_time = pack_time + timedelta(minutes=int(delivery_minutes), seconds=int((delivery_minutes % 1)*60))
            distance_km = round(zone["avg_distance_km"] + random.uniform(-0.3, 0.4), 2)
            delivery_records.append({
                "order_id": order_id,
                "rider_id": rider_id,
                "zone_id": zone_id,
                "distance_km": max(0.8, distance_km),
                "packed_at": pack_time.isoformat(),
                "delivered_at": delivery_time.isoformat(),
                "duration_min": round(delivery_minutes, 1)
            })

            # Complaints Generation with Planted Root Causes & Baseline Rate
            # Baseline complaint rate ~ 1.5% of order items, higher for fresh/frozen (~2.2%)
            for item in order_items_this_order:
                should_complain = False
                complaint_type = None

                # Baseline probability
                cat = item["category"]
                base_prob = 0.022 if cat in ("fresh_produce", "dairy_frozen") else 0.011
                if random.random() < base_prob:
                    should_complain = True
                    if cat == "fresh_produce":
                        complaint_type = random.choice(["rotten", "damaged_pack"])
                    elif item["storage_req"] == "frozen":
                        complaint_type = "melted"
                    elif item["sku_id"] == "SKU-011":
                        complaint_type = "crushed"
                    else:
                        complaint_type = random.choice(["wrong_item", "damaged_pack", "expired"])

                # Scenario 1 Trigger: Tomato Batch B-4471 rot rate 6x baseline in last 3 days
                if item["batch_id"] == SCENARIO_SETTINGS.s1_batch_id and days_from_end <= SCENARIO_SETTINGS.s1_days_active:
                    # Normal tomato rot is ~2%, 6x -> ~12-14%
                    if random.random() < 0.14:
                        should_complain = True
                        complaint_type = "rotten"

                # Scenario 2 Trigger: S1 freezer F2 drift to -8C in last 7 days afternoon (12-5 PM)
                if (store_id == SCENARIO_SETTINGS.s2_store_id and 
                    item["storage_req"] == "frozen" and 
                    days_from_end <= SCENARIO_SETTINGS.s2_days_active and 
                    SCENARIO_SETTINGS.s2_afternoon_hours[0] <= order_hour <= SCENARIO_SETTINGS.s2_afternoon_hours[1]):
                    # 5x baseline for melted
                    if random.random() < 0.12:
                        should_complain = True
                        complaint_type = "melted"

                # Scenario 3 Trigger: S2 Zone 3 delivery > 18 min on hot days (>35C)
                if is_s2_z3_hot and item["storage_req"] == "frozen":
                    if random.random() < 0.15:
                        should_complain = True
                        complaint_type = "melted"

                # Scenario 4 Trigger: S3 packer PK-308 crushed eggs 5x baseline
                if (store_id == SCENARIO_SETTINGS.s4_store_id and 
                    packer_id == SCENARIO_SETTINGS.s4_packer_id and 
                    item["sku_id"] == "SKU-011"):
                    if random.random() < 0.16: # Normal egg crush is ~3%, 5x is ~15-16%
                        should_complain = True
                        complaint_type = "crushed"

                if should_complain and complaint_type:
                    complaint_id_counter += 1
                    cid = f"CMP-{complaint_id_counter}"
                    complaint_time = delivery_time + timedelta(minutes=random.randint(10, 180))
                    complaint_text = random.choice(COMPLAINT_TEMPLATES[complaint_type])
                    
                    complaint_records.append({
                        "complaint_id": cid,
                        "order_item_id": item["order_item_id"],
                        "customer_id": customer_id,
                        "type": complaint_type,
                        "text": complaint_text,
                        "photo_uri": None, # Step 3 assigns photos
                        "refund_inr": item["unit_price_inr"] * item["quantity"],
                        "created_at": complaint_time.isoformat(),
                        "gemini_verdict": None,
                        "gemini_severity": None,
                        "photo_embedding": None
                    })

    # Plant Scenario 5: 3 Customer accounts reusing 2 near-identical photos across 9 claims
    print("  Planting Scenario 5 (Coordinated Refund Abuse)...")
    for abuse_idx in range(SCENARIO_SETTINGS.s5_claim_count):
        complaint_id_counter += 1
        cid = f"CMP-ABUSE-{abuse_idx+1:02d}"
        cust = fraud_customers[abuse_idx % len(fraud_customers)]
        store = random.choice(STORES)
        c_time = END_DATE - timedelta(days=random.randint(1, 4), hours=random.randint(1, 10))
        photo_base = SCENARIO_SETTINGS.s5_photo_bases[0] if abuse_idx < 5 else SCENARIO_SETTINGS.s5_photo_bases[1]
        c_type = "rotten" if "rotten" in photo_base else "melted"
        
        # Pick a dummy order item
        dummy_item = random.choice(order_item_records)
        complaint_records.append({
            "complaint_id": cid,
            "order_item_id": dummy_item["order_item_id"],
            "customer_id": cust,
            "type": c_type,
            "text": f"Severe defect detected, totally spoiled! Photo attached. Please refund instantly to my UPI.",
            "photo_uri": f"gs://rd-photos/complaints/abuse/{photo_base}_v{abuse_idx%3}.jpg",
            "refund_inr": 280,
            "created_at": c_time.isoformat(),
            "gemini_verdict": None,
            "gemini_severity": None,
            "photo_embedding": None
        })

    # Plant Scenario 6: Red herring: one-day bread spike with no consistent cause
    print("  Planting Scenario 6 (Red Herring Bread Spike)...")
    bread_date = END_DATE - timedelta(days=SCENARIO_SETTINGS.s6_day_offset)
    bakery_items = [item for item in order_item_records if item["category"] == "bakery" and bread_date.strftime("%Y-%m-%d") in item["order_id"]]
    if len(bakery_items) < 30:
        # Fallback to any recent bakery items
        bakery_items = [item for item in order_item_records if item["category"] == "bakery"][-60:]
    
    sampled_bread_items = random.sample(bakery_items, min(SCENARIO_SETTINGS.s6_spike_count, len(bakery_items)))
    for b_item in sampled_bread_items:
        complaint_id_counter += 1
        cid = f"CMP-HERRING-{complaint_id_counter}"
        b_time = bread_date.replace(hour=random.randint(8, 22), minute=random.randint(0, 59))
        complaint_records.append({
            "complaint_id": cid,
            "order_item_id": b_item["order_item_id"],
            "customer_id": random.choice(customers),
            "type": random.choice(["expired", "damaged_pack", "wrong_item"]),
            "text": random.choice(["bread tastes slightly dry today", "crust was hard", "packaging had small tear"]),
            "photo_uri": None,
            "refund_inr": b_item["unit_price_inr"] * b_item["quantity"],
            "created_at": b_time.isoformat(),
            "gemini_verdict": None,
            "gemini_severity": None,
            "photo_embedding": None
        })

    # 6. Freezer Logs: 4 stores x 4 storage units x 60 days x 96 readings/day (every 15 min)
    print("  Generating high-resolution 15-minute freezer telemetry...")
    freezer_records = []
    f_units = ["F1", "F2", "C1", "A1"]
    
    # 60 days of 15-min timestamps = 60 * 24 * 4 = 5,760 intervals
    telemetry_time = START_DATE
    while telemetry_time <= END_DATE:
        ts_str = telemetry_time.isoformat()
        t_hour = telemetry_time.hour
        days_from_end = (END_DATE - telemetry_time).days
        
        for store in STORES:
            s_id = store["store_id"]
            for u in f_units:
                if u.startswith("F"):
                    # Normal freezer: -18C to -20C
                    temp = round(random.uniform(-20.2, -18.2), 1)
                    
                    # Scenario 2: S1 freezer F2 drifts to -8C every afternoon in the last 7 days!
                    if (s_id == SCENARIO_SETTINGS.s2_store_id and 
                        u == SCENARIO_SETTINGS.s2_freezer_id and 
                        days_from_end <= SCENARIO_SETTINGS.s2_days_active and 
                        SCENARIO_SETTINGS.s2_afternoon_hours[0] <= t_hour <= SCENARIO_SETTINGS.s2_afternoon_hours[1]):
                        temp = round(random.uniform(-8.8, -7.4), 1)
                elif u.startswith("C"):
                    # Chiller: +2C to +4C
                    temp = round(random.uniform(2.1, 4.2), 1)
                else:
                    # Ambient: 21C to 24C
                    temp = round(random.uniform(21.0, 24.0), 1)

                freezer_records.append({
                    "store_id": s_id,
                    "unit_id": u,
                    "ts": ts_str,
                    "temp_c": temp
                })
        telemetry_time += timedelta(minutes=15)

    # Convert to DataFrames and Save to Parquet
    print("  Saving 12 tables to Parquet in data/out/ ...")
    tables = {
        "stores": df_stores,
        "zones": df_zones,
        "suppliers": df_suppliers,
        "skus": df_skus,
        "batches": df_batches,
        "orders": pd.DataFrame(order_records),
        "order_items": pd.DataFrame(order_item_records),
        "fulfilment": pd.DataFrame(fulfilment_records),
        "deliveries": pd.DataFrame(delivery_records),
        "complaints": pd.DataFrame(complaint_records),
        "freezer_logs": pd.DataFrame(freezer_records),
        "weather_daily": df_weather
    }

    for name, df in tables.items():
        pq_path = os.path.join(OUT_DIR, f"{name}.parquet")
        df.to_parquet(pq_path, index=False)
        print(f"    ✓ {name:15s}: {len(df):>7,d} rows -> {pq_path}")

    print("🎉 Synthetic data generation complete!")
    return tables

if __name__ == "__main__":
    generate_all_data()
