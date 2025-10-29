from typing import List, Dict
import random

# Seeded numbers with categories: 'esim' or 'physical'
# status: 'busy' or 'free'
# price: price per month in USD
SEEDED_NUMBERS: List[Dict[str, str]] = []

# Generate eSIM numbers (10-23 units, price $10-$30)
esim_count = random.randint(10, 23)
for i in range(esim_count):
        price = random.randint(10, 30)
        SEEDED_NUMBERS.append({
                "number": f"+888 eSIM {1000 + i:04d}",
                "status": "free",
                "category": "esim",
                "price": price
        })

# Generate Physical numbers (10-23 units, price $4-$10)
physical_count = random.randint(10, 23)
for i in range(physical_count):
        price = random.randint(4, 10)
        SEEDED_NUMBERS.append({
                "number": f"+888 PHYS {2000 + i:04d}",
                "status": "free",
                "category": "physical",
                "price": price
        })

# Mark some as busy randomly
for num in SEEDED_NUMBERS:
        if random.random() < 0.2:  # 20% chance to be busy
                num["status"] = "busy"
