import aiohttp
from typing import Optional, Dict

API_URL = "https://pay.crypt.bot/api/"

class CryptoPay:
	def __init__(self, token: str):
		self.token = token

	async def _post(self, method: str, data: Dict) -> Dict:
		headers = {"Crypto-Pay-API-Token": self.token}
		async with aiohttp.ClientSession() as session:
			async with session.post(API_URL + method, json=data, headers=headers) as resp:
				resp.raise_for_status()
				return await resp.json()

	async def create_invoice(self, amount: float, asset: str, description: str, payload: str) -> Optional[Dict]:
		data = {
			"asset": asset,
			"amount": str(amount),
			"description": description,
			"payload": payload,
		}
		res = await self._post("createInvoice", data)
		if res.get("ok"):
			return res["result"]
		return None

	async def get_invoice(self, invoice_id: int) -> Optional[Dict]:
		res = await self._post("getInvoices", {"invoice_ids": [invoice_id]})
		if res.get("ok") and res["result"]["items"]:
			return res["result"]["items"][0]
		return None
