"""
Return Detective — Scenario Definitions & Configuration
Controls the 6 planted root-cause scenarios with deterministic seeds and parameters.
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ScenarioConfig:
    enabled: bool = True
    seed: int = 42

    # Scenario 1: Supplier Batch Quality
    # Batch B-4471 (GreenLeaf Farms, Tomatoes): rot complaints 6x baseline, S1-S3 over last 3 days
    s1_batch_id: str = "B-4471"
    s1_supplier_name: str = "GreenLeaf Farms"
    s1_sku_name: str = "Fresh Hybrid Tomatoes 500g"
    s1_rot_multiplier: float = 6.0
    s1_days_active: int = 3

    # Scenario 2: Dark Store Equipment Failure
    # S1 freezer F2 drifts to -8C every afternoon for 7 days -> melt complaints at S1
    s2_store_id: str = "S1"
    s2_freezer_id: str = "F2"
    s2_drift_temp_c: float = -8.0
    s2_days_active: int = 7
    s2_afternoon_hours: tuple = (12, 17) # 12 PM to 5 PM
    s2_melt_multiplier: float = 5.0

    # Scenario 3: Cold Chain Transit Break
    # S2 zone 3 deliveries > 18 min on days > 35C -> melt complaints; freezer normal
    s3_store_id: str = "S2"
    s3_zone_id: str = "S2-Z3"
    s3_temp_threshold_c: float = 35.0
    s3_delivery_min_threshold: float = 18.0
    s3_melt_multiplier: float = 4.5

    # Scenario 4: Human Negligence / Improper Packing
    # One packer at S3 with crushed-egg rate 5x store average
    s4_store_id: str = "S3"
    s4_packer_id: str = "PK-308"
    s4_sku_name: str = "Farm Fresh White Eggs 6-pack"
    s4_crush_multiplier: float = 5.2

    # Scenario 5: Coordinated Refund Abuse
    # 3 customer accounts reusing 2 near-identical photos across 9 claims
    s5_customers: tuple = ("CUST-ABUSE-101", "CUST-ABUSE-102", "CUST-ABUSE-103")
    s5_photo_bases: tuple = ("abuse_base_rotten_apple.jpg", "abuse_base_melted_choc.jpg")
    s5_claim_count: int = 9

    # Scenario 6: Red Herring (Bread Spike)
    # One-day bread complaint spike with no consistent cause -> no action / watching
    s6_sku_category: str = "bakery"
    s6_day_offset: int = 2 # 2 days ago
    s6_spike_count: int = 28 # concentrated within 24h across all stores, different suppliers/packers

SCENARIO_SETTINGS = ScenarioConfig()
