import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "rifa.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = BASE_DIR / "data" / "settings.json"

DEFAULT_SETTINGS = {
    "prize_name": "iPhone 17 Pro Max 256GB - Titanio Natural",
    "prize_value": ".200.000 COP",
    "total_tickets": 10000,
    "ticket_price": 2000,
    "min_tickets": 5,
    "draw_date": "2026-12-22",
    "draw_date_display": "22 de Diciembre de 2026",
    "draw_time_display": "10:30 PM (Con el Premio Mayor)",
    "lottery_name": "Lotería Oficial (Premio Mayor de 4 cifras)",
    "nequi_number": "312 345 6789",
    "nequi_name": "Organizador Oficial",
    "daviplata_number": "312 345 6789",
    "daviplata_name": "Organizador Oficial",
    "bancolombia_account": "031-892341-12 (Ahorros)",
    "bancolombia_name": "Organizador Oficial",
    "whatsapp_number": "573123456789",
    "admin_pin": "1722",
    "smtp_enabled": False,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_password": "",
    "smtp_from": "sorteo.iphone17@gmail.com"
}

def get_settings():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                return {**DEFAULT_SETTINGS, **saved}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(new_settings: dict):
    current = get_settings()
    current.update(new_settings)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=4, ensure_ascii=False)
    return current
