from typing import List, Dict

# Seeded numbers with categories and types
# category: 'anonymous', 'esim', 'physical'
# type: 'rent' (аренда) or 'sale' (продажа)
# status: 'busy' or 'free'
# price: price per month for rent, or one-time price for sale
SEEDED_NUMBERS: List[Dict[str, str]] = []

# Anonymous numbers - for RENT (аренда)
anonymous_numbers = [
        ("+888 741 0385", "free"),
        ("+888 290 5176", "busy"),
        ("+888 618 3924", "free"),
        ("+888 054 9831", "busy"),
        ("+888 372 6098", "free"),
        ("+888 956 1407", "free"),
        ("+888 103 8259", "busy"),
        ("+888 487 7312", "free"),
        ("+888 829 0643", "busy"),
        ("+888 531 2704", "free"),
]

for number, status in anonymous_numbers:
        SEEDED_NUMBERS.append({
                "number": number,
                "status": status,
                "category": "anonymous",
                "type": "rent",
                "price": 25  # Base price for anonymous numbers rent
        })

# eSIM numbers - for SALE (продажа)
esim_numbers = [
        "+7 904 672 81 59",
        "+380 97 185 36 20",
        "+7 927 349 02 71",
        "+380 63 590 74 81",
        "+7 917 810 52 36",
        "+380 50 248 19 63",
        "+7 986 735 90 14",
        "+380 68 062 47 95",
        "+7 962 194 65 08",
        "+380 99 357 80 12",
]

for number in esim_numbers:
        SEEDED_NUMBERS.append({
                "number": number,
                "status": "free",
                "category": "esim",
                "type": "sale",
                "price": 15  # Price for eSIM sale
        })

# Physical SIM numbers - for SALE (продажа)
physical_numbers = [
        "+7 934 501 78 26",
        "+7 908 276 39 45",
        "+7 913 940 18 72",
        "+7 989 615 03 84",
        "+7 950 427 96 13",
        "+7 900 853 20 97",
        "+7 921 709 45 81",
        "+7 911 368 12 79",
        "+7 969 042 57 38",
        "+7 981 175 69 04",
]

for number in physical_numbers:
        SEEDED_NUMBERS.append({
                "number": number,
                "status": "free",
                "category": "physical",
                "type": "sale",
                "price": 8  # Price for Physical SIM sale
        })
