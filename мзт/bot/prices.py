PRICES = {
	1: 25,
	3: 55,
	6: 100,
	12: 120,
}


def get_price(months: int) -> int:
	return PRICES.get(months, 0)
