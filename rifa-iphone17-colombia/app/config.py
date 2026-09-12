import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "rifa.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = BASE_DIR / "data" / "settings.json"

DEFAULT_SETTINGS = {
    "prize_name": "iPhone 17 Pro Max 256GB - Sunset Orange Titanium",
    "prize_value": "$6.500.000 COP",
    "total_tickets": 10000,
    "ticket_price": 2000,
    "min_tickets": 5,
    "draw_date": "2026-12-22",
    "draw_date_display": "22 de Diciembre de 2026",
    "draw_time_display": "10:30 PM (Con el Premio Mayor)",
    "lottery_name": "Lotería Oficial (Premio Mayor de 4 cifras)",
    "reservation_timeout_minutes": 30,
    
    # Cuentas Bancarias Oficiales
    "bancolombia_account": "78635749848",
    "bancolombia_type": "Cuenta de Ahorros",
    "bancolombia_name": "Edwin Garavito Vargas",
    "bancolombia_cc": "1047475150",
    
    "transfiya_key": "@garavito150",
    
    "nequi_number": "321 235 8924",
    "nequi_name": "Edwin Garavito Vargas",
    
    "daviplata_number": "321 235 8924",
    "daviplata_name": "Edwin Garavito Vargas",
    
    "whatsapp_number": "573212358924",
    "admin_pin": "1722",
    
    "smtp_enabled": False,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_password": "",
    "smtp_from": "sorteos@rifacentercolombia.lat"
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
