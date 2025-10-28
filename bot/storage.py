import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .data import SEEDED_NUMBERS

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STATE_FILE = os.path.abspath(os.path.join(DATA_DIR, "state.json"))

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _ensure_dirs() -> None:
	os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)


def _load_state() -> Dict:
	_ensure_dirs()
	if not os.path.exists(STATE_FILE):
		return {
			"numbers": SEEDED_NUMBERS,
			"rentals": {},  # user_id -> List[{number, until_iso}]
			"payments": {},  # payment_id -> {user_id, number, months, price, invoice_id, status}
		}
	with open(STATE_FILE, "r", encoding="utf-8") as f:
		return json.load(f)


def _save_state(state: Dict) -> None:
	_ensure_dirs()
	with open(STATE_FILE, "w", encoding="utf-8") as f:
		json.dump(state, f, ensure_ascii=False, indent=2)


def list_numbers() -> List[Dict]:
	state = _load_state()
	return state["numbers"]


def get_number(number: str) -> Optional[Dict]:
	for item in list_numbers():
		if item["number"] == number:
			return item
	return None


def set_number_status(number: str, status: str) -> None:
	state = _load_state()
	for item in state["numbers"]:
		if item["number"] == number:
			item["status"] = status
			break
	_save_state(state)


def add_rental(user_id: int, number: str, months: int) -> Optional[Dict]:
	state = _load_state()
	for item in state["numbers"]:
		if item["number"] == number:
			if item["status"] == "busy":
				return None
			item["status"] = "busy"
			break
	until = datetime.utcnow() + timedelta(days=30 * months)
	rental = {"number": number, "until": until.strftime(ISO_FORMAT)}
	user_key = str(user_id)
	state["rentals"].setdefault(user_key, [])
	state["rentals"][user_key].append(rental)
	_save_state(state)
	return rental


def list_rentals(user_id: int) -> List[Dict]:
	state = _load_state()
	return state["rentals"].get(str(user_id), [])


def extend_rental(user_id: int, number: str, months: int) -> Optional[Dict]:
	state = _load_state()
	user_key = str(user_id)
	rentals = state["rentals"].get(user_key, [])
	for r in rentals:
		if r["number"] == number:
			until = datetime.strptime(r["until"], ISO_FORMAT)
			until += timedelta(days=30 * months)
			r["until"] = until.strftime(ISO_FORMAT)
			_save_state(state)
			return r
	return None


def release_if_expired() -> int:
	state = _load_state()
	now = datetime.utcnow()
	released_count = 0
	num_index = {n["number"]: n for n in state["numbers"]}
	for user_key, rentals in list(state["rentals"].items()):
		remaining: List[Dict] = []
		for r in rentals:
			until = datetime.strptime(r["until"], ISO_FORMAT)
			if until <= now:
				released_count += 1
				num_index.get(r["number"], {"status": "busy"})["status"] = "free"
			else:
				remaining.append(r)
		state["rentals"][user_key] = remaining
	_save_state(state)
	return released_count

# Payments

def create_pending_payment(payment_id: str, payload: Dict) -> None:
	state = _load_state()
	state["payments"][payment_id] = payload
	_save_state(state)


def get_payment(payment_id: str) -> Optional[Dict]:
	state = _load_state()
	return state["payments"].get(payment_id)


def set_payment_status(payment_id: str, status: str, invoice_id: int = None) -> None:
	state = _load_state()
	p = state["payments"].get(payment_id)
	if not p:
		return
	p["status"] = status
	if invoice_id is not None:
		p["invoice_id"] = invoice_id
	_save_state(state)

# Admin/owner operations

def force_rental(user_id: int, number: str, months: int) -> Optional[Dict]:
	"""Force-assign a number to a user. Replaces any existing holder and marks number busy."""
	state = _load_state()
	# Ensure number exists
	n_item = None
	for item in state["numbers"]:
		if item["number"] == number:
			n_item = item
			break
	if not n_item:
		return None
	# Remove existing rentals for this number across all users
	for ukey, rentals in list(state["rentals"].items()):
		state["rentals"][ukey] = [r for r in rentals if r.get("number") != number]
	# Mark busy
	n_item["status"] = "busy"
	# Add rental to target user
	until = datetime.utcnow() + timedelta(days=30 * months)
	rental = {"number": number, "until": until.strftime(ISO_FORMAT)}
	user_key = str(user_id)
	state["rentals"].setdefault(user_key, [])
	state["rentals"][user_key].append(rental)
	_save_state(state)
	return rental
