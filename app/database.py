import sqlite3
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from app.config import DB_PATH, get_settings

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Tabla de compradores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buyers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                cedula TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                city TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_buyers_cedula ON buyers(cedula);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_buyers_phone ON buyers(phone);")

        # Tabla de órdenes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                buyer_id INTEGER NOT NULL,
                ticket_count INTEGER NOT NULL,
                unit_price INTEGER NOT NULL,
                total_amount INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', -- pending, approved, rejected
                payment_method TEXT NOT NULL,
                receipt_url TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                FOREIGN KEY (buyer_id) REFERENCES buyers(id)
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")

        # Tabla de boletas (0000 - 9999)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                number TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'available', -- available, reserved, sold
                order_id TEXT,
                reserved_at TIMESTAMP,
                sold_at TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_order ON tickets(order_id);")

        # Verificar si las 10,000 boletas ya existen
        cursor.execute("SELECT COUNT(*) FROM tickets;")
        count = cursor.fetchone()[0]
        if count == 0:
            print("[DB] Generando 10,000 números iniciales (0000 - 9999)...")
            batch = [(f"{i:04d}", 'available', None, None, None) for i in range(10000)]
            cursor.executemany(
                "INSERT INTO tickets (number, status, order_id, reserved_at, sold_at) VALUES (?, ?, ?, ?, ?)",
                batch
            )
            print("[DB] 10,000 números generados exitosamente.")
        conn.commit()

def get_stats() -> Dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status")
        counts = dict(cursor.fetchall())
        
        sold = counts.get('sold', 0)
        reserved = counts.get('reserved', 0)
        available = counts.get('available', 0)
        total = 10000

        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = 'approved'")
        revenue = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = 'pending'")
        pending_revenue = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
        pending_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT id) FROM buyers")
        buyers_count = cursor.fetchone()[0]

        percent_sold = round((sold / total) * 100, 2) if total > 0 else 0

        return {
            "total_tickets": total,
            "sold_tickets": sold,
            "reserved_tickets": reserved,
            "available_tickets": available,
            "percent_sold": percent_sold,
            "total_revenue": revenue,
            "pending_revenue": pending_revenue,
            "pending_orders": pending_orders,
            "total_buyers": buyers_count
        }

def get_random_available_tickets(count: int) -> List[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT number FROM tickets WHERE status = 'available'")
        all_available = [row[0] for row in cursor.fetchall()]
        
        if len(all_available) < count:
            return all_available
        return random.sample(all_available, count)

def check_ticket(number: str) -> Dict:
    num_str = number.strip().zfill(4)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT number, status FROM tickets WHERE number = ?", (num_str,))
        row = cursor.fetchone()
        if not row:
            return {"number": num_str, "valid": False, "status": "invalid"}
        return {"number": row["number"], "valid": True, "status": row["status"]}

def search_tickets(query: str = "", limit: int = 40, status: str = "all") -> List[Dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        sql = "SELECT number, status FROM tickets WHERE 1=1"
        params = []
        if query:
            sql += " AND number LIKE ?"
            params.append(f"%{query}%")
        if status != "all":
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY number ASC LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        return [{"number": r["number"], "status": r["status"]} for r in cursor.fetchall()]

def register_order(
    full_name: str,
    cedula: str,
    phone: str,
    email: str,
    city: str,
    tickets: List[str],
    payment_method: str,
    receipt_url: Optional[str] = None,
    notes: Optional[str] = None,
    auto_approve: bool = False
) -> Dict:
    import uuid
    settings = get_settings()
    unit_price = settings.get("ticket_price", 2000)
    
    clean_tickets = [str(t).strip().zfill(4) for t in tickets]
    clean_tickets = list(dict.fromkeys(clean_tickets)) # Remover duplicados
    count = len(clean_tickets)

    if count < settings.get("min_tickets", 5):
        raise ValueError(f"La cantidad mínima de boletas es {settings.get('min_tickets', 5)}.")

    total_amount = count * unit_price
    order_id = f"ORD-{datetime.now().strftime('%m%d%H%M')}-{uuid.uuid4().hex[:4].upper()}"

    with get_connection() as conn:
        cursor = conn.cursor()
        # Verificar que todos los números estén disponibles
        placeholders = ','.join(['?'] * count)
        cursor.execute(
            f"SELECT number, status FROM tickets WHERE number IN ({placeholders})",
            clean_tickets
        )
        found = cursor.fetchall()
        not_available = [r["number"] for r in found if r["status"] != 'available']
        if not_available:
            raise ValueError(f"Los siguientes números ya no están disponibles: {', '.join(not_available)}")
        if len(found) != count:
            raise ValueError("Uno o más números especificados no existen.")

        # Obtener o crear comprador
        cursor.execute("SELECT id FROM buyers WHERE cedula = ? LIMIT 1", (cedula.strip(),))
        existing_buyer = cursor.fetchone()
        if existing_buyer:
            buyer_id = existing_buyer["id"]
            cursor.execute(
                "UPDATE buyers SET full_name = ?, phone = ?, email = ?, city = ? WHERE id = ?",
                (full_name.strip(), phone.strip(), email.strip().lower(), city.strip(), buyer_id)
            )
        else:
            cursor.execute(
                "INSERT INTO buyers (full_name, cedula, phone, email, city) VALUES (?, ?, ?, ?, ?)",
                (full_name.strip(), cedula.strip(), phone.strip(), email.strip().lower(), city.strip())
            )
            buyer_id = cursor.lastrowid

        # Crear orden
        status = 'approved' if auto_approve else 'pending'
        approved_at = datetime.now().isoformat() if auto_approve else None
        cursor.execute(
            """INSERT INTO orders 
               (id, buyer_id, ticket_count, unit_price, total_amount, status, payment_method, receipt_url, notes, approved_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, buyer_id, count, unit_price, total_amount, status, payment_method, receipt_url, notes, approved_at)
        )

        # Actualizar estado de boletas
        ticket_status = 'sold' if auto_approve else 'reserved'
        now_ts = datetime.now().isoformat()
        cursor.execute(
            f"""UPDATE tickets 
                SET status = ?, order_id = ?, reserved_at = ?, sold_at = ? 
                WHERE number IN ({placeholders})""",
            [ticket_status, order_id, now_ts, now_ts if auto_approve else None] + clean_tickets
        )
        conn.commit()

    return {
        "order_id": order_id,
        "buyer_id": buyer_id,
        "full_name": full_name,
        "cedula": cedula,
        "phone": phone,
        "email": email,
        "city": city,
        "tickets": clean_tickets,
        "ticket_count": count,
        "total_amount": total_amount,
        "status": status,
        "payment_method": payment_method
    }

def approve_order(order_id: str) -> Dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise ValueError("Orden no encontrada.")
        if order["status"] == "approved":
            return {"status": "already_approved", "order_id": order_id}

        now_ts = datetime.now().isoformat()
        cursor.execute("UPDATE orders SET status = 'approved', approved_at = ? WHERE id = ?", (now_ts, order_id))
        cursor.execute("UPDATE tickets SET status = 'sold', sold_at = ? WHERE order_id = ?", (now_ts, order_id))
        conn.commit()
        return {"status": "approved", "order_id": order_id}

def reject_order(order_id: str) -> Dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise ValueError("Orden no encontrada.")

        cursor.execute("UPDATE orders SET status = 'rejected' WHERE id = ?", (order_id,))
        cursor.execute(
            "UPDATE tickets SET status = 'available', order_id = NULL, reserved_at = NULL, sold_at = NULL WHERE order_id = ?",
            (order_id,)
        )
        conn.commit()
        return {"status": "rejected", "order_id": order_id}

def get_order_by_id(order_id: str) -> Optional[Dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, b.full_name, b.cedula, b.phone, b.email, b.city 
            FROM orders o
            JOIN buyers b ON o.buyer_id = b.id
            WHERE o.id = ?
        """, (order_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        order = dict(row)
        cursor.execute("SELECT number, status FROM tickets WHERE order_id = ? ORDER BY number ASC", (order_id,))
        order["tickets"] = [r["number"] for r in cursor.fetchall()]
        return order

def find_purchases_by_query(query: str) -> List[Dict]:
    cleaned = query.strip()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.id as order_id, o.ticket_count, o.total_amount, o.status, o.created_at, o.payment_method,
                   b.full_name, b.cedula, b.phone, b.email, b.city
            FROM orders o
            JOIN buyers b ON o.buyer_id = b.id
            WHERE b.cedula = ? OR b.phone LIKE ? OR o.id = ?
            ORDER BY o.created_at DESC
        """, (cleaned, f"%{cleaned}%", cleaned))
        orders = [dict(r) for r in cursor.fetchall()]
        
        for ord_item in orders:
            cursor.execute("SELECT number, status FROM tickets WHERE order_id = ? ORDER BY number ASC", (ord_item["order_id"],))
            ord_item["tickets"] = [r["number"] for r in cursor.fetchall()]
            
        return orders

def check_winning_number(number: str) -> Dict:
    num_str = number.strip().zfill(4)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.number, t.status, o.id as order_id, o.created_at, o.approved_at,
                   b.full_name, b.cedula, b.phone, b.email, b.city
            FROM tickets t
            LEFT JOIN orders o ON t.order_id = o.id
            LEFT JOIN buyers b ON o.buyer_id = b.id
            WHERE t.number = ?
        """, (num_str,))
        row = cursor.fetchone()
        if not row:
            return {"number": num_str, "found": False}
        
        data = dict(row)
        return {
            "number": num_str,
            "found": True,
            "status": data["status"],
            "has_winner": data["status"] == "sold",
            "order_id": data.get("order_id"),
            "buyer_name": data.get("full_name"),
            "buyer_cedula": data.get("cedula"),
            "buyer_phone": data.get("phone"),
            "buyer_email": data.get("email"),
            "buyer_city": data.get("city"),
            "approved_at": data.get("approved_at")
        }

def get_all_orders(status: str = "all", limit: int = 100) -> List[Dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        sql = """
            SELECT o.*, b.full_name, b.cedula, b.phone, b.email, b.city
            FROM orders o
            JOIN buyers b ON o.buyer_id = b.id
        """
        params = []
        if status != "all":
            sql += " WHERE o.status = ?"
            params.append(status)
        sql += " ORDER BY o.created_at DESC LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        orders = [dict(r) for r in cursor.fetchall()]

        for ord_item in orders:
            cursor.execute("SELECT number FROM tickets WHERE order_id = ? ORDER BY number ASC", (ord_item["id"],))
            ord_item["tickets"] = [r["number"] for r in cursor.fetchall()]

        return orders
