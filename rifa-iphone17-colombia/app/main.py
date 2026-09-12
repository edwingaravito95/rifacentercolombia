import os
import io
import json
import shutil
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from bottle import Bottle, request, response, static_file, HTTPResponse
import jinja2
import openpyxl

from app.config import get_settings, save_settings, BASE_DIR
from app.database import (
    init_db, get_stats, get_random_available_tickets, check_ticket,
    search_tickets, register_order, approve_order, reject_order,
    get_order_by_id, find_purchases_by_query, check_winning_number,
    get_all_orders, get_tickets_by_range, cleanup_expired_reservations
)
from app.email_service import send_order_confirmation

app = Bottle()

STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "templates"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de Jinja2
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)

def format_cop(value: int) -> str:
    return f"${value:,.0f}".replace(",", ".")

jinja_env.filters["cop"] = format_cop

def render_template(template_name: str, **context):
    tmpl = jinja_env.get_template(template_name)
    return tmpl.render(**context)

# Inicializar DB al importar
init_db()

# ==================== ARCHIVOS ESTÁTICOS ====================

@app.route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=str(STATIC_DIR))

# ==================== VISTAS HTML ====================

@app.route('/')
def index():
    return render_template("index.html", settings=get_settings(), stats=get_stats())

@app.route('/consultar')
def consultar_page():
    q = request.query.get("q", "").strip()
    results = []
    if q:
        results = find_purchases_by_query(q)
    return render_template("consultar.html", settings=get_settings(), query=q, results=results)

@app.route('/boleto/<order_id>')
def boleto_page(order_id):
    order = get_order_by_id(order_id)
    if not order:
        return HTTPResponse(status=404, body="Boleto no encontrado")
    return render_template("boleto.html", settings=get_settings(), order=order)

@app.route('/admin')
def admin_page():
    return render_template("admin.html", settings=get_settings(), stats=get_stats(), orders=get_all_orders())

@app.route('/terminos')
def terminos_page():
    return render_template("terminos.html", settings=get_settings())

# ==================== API PÚBLICA ====================

@app.route('/api/stats', method=['GET'])
def api_stats():
    response.content_type = 'application/json'
    return json.dumps(get_stats())

@app.route('/api/random-tickets', method=['POST'])
def api_random_tickets():
    response.content_type = 'application/json'
    payload = request.json or {}
    count = int(payload.get('count', 5))
    settings = get_settings()
    min_count = settings.get("min_tickets", 5)

    if count < min_count:
        response.status = 400
        return json.dumps({"detail": f"Debes seleccionar mínimo {min_count} boletas."})

    tickets = get_random_available_tickets(count)
    if len(tickets) < count:
        response.status = 400
        return json.dumps({"detail": f"Solo quedan {len(tickets)} boletas disponibles."})

    return json.dumps({"tickets": tickets, "count": len(tickets)})

@app.route('/api/check-ticket/<number>', method=['GET'])
def api_check_ticket(number):
    response.content_type = 'application/json'
    return json.dumps(check_ticket(number))

@app.route('/api/search-tickets', method=['GET'])
def api_search_tickets():
    response.content_type = 'application/json'
    q = request.query.get("q", "").strip()
    limit = int(request.query.get("limit", 60))
    status = request.query.get("status", "available")
    return json.dumps(search_tickets(query=q, limit=limit, status=status))

@app.route('/api/tickets-range', method=['GET'])
def api_tickets_range():
    response.content_type = 'application/json'
    start = int(request.query.get("start", 0))
    count = int(request.query.get("count", 1000))
    tickets = get_tickets_by_range(start, count)
    return json.dumps({"start": start, "count": len(tickets), "tickets": tickets})

@app.route('/api/checkout', method=['POST'])
def api_checkout():
    response.content_type = 'application/json'
    payload = request.json or {}
    try:
        order = register_order(
            full_name=payload.get("full_name", "").strip(),
            cedula=payload.get("cedula", "").strip(),
            phone=payload.get("phone", "").strip(),
            email=payload.get("email", "").strip(),
            city=payload.get("city", "Colombia").strip(),
            tickets=payload.get("tickets", []),
            payment_method=payload.get("payment_method", "nequi"),
            seller=payload.get("seller", "Web Directo"),
            notes=payload.get("notes"),
            auto_approve=False
        )
    except ValueError as e:
        response.status = 400
        return json.dumps({"detail": str(e)})

    # Enviar correo de confirmación
    send_order_confirmation(order)

    # Mensaje prellenado para WhatsApp oficial (3212358924)
    settings = get_settings()
    wa_num = settings.get("whatsapp_number", "573212358924")
    numbers_str = ", ".join(order["tickets"][:10])
    if len(order["tickets"]) > 10:
        numbers_str += f" y {len(order['tickets']) - 10} más"

    wa_message = (
        f"¡Hola! Acabo de reservar {order['ticket_count']} boletas para el sorteo del iPhone 17 Pro Max.\n\n"
        f"📝 Orden: {order['order_id']}\n"
        f"👤 Nombre: {order['full_name']}\n"
        f"🪪 Cédula: {order['cedula']}\n"
        f"🎟️ Números: {numbers_str}\n"
        f"💰 Total a pagar: ${order['total_amount']:,} COP\n"
        f"💳 Método: {order['payment_method'].upper()}\n"
        f"👤 Vendedor / Asesor: {order.get('seller', 'Web Directo')}\n\n"
        f"Adjunto mi comprobante de pago para aprobación."
    )
    wa_url = f"https://wa.me/{wa_num}?text={urllib.parse.quote(wa_message)}"

    return json.dumps({
        "success": True,
        "order": order,
        "whatsapp_url": wa_url
    })

@app.route('/api/upload-receipt/<order_id>', method=['POST'])
def api_upload_receipt(order_id):
    response.content_type = 'application/json'
    order = get_order_by_id(order_id)
    if not order:
        response.status = 404
        return json.dumps({"detail": "Orden no encontrada"})

    upload = request.files.get('file')
    if not upload:
        response.status = 400
        return json.dumps({"detail": "Archivo no enviado"})

    ext = Path(upload.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".pdf"]:
        response.status = 400
        return json.dumps({"detail": "Formato no permitido. Usa JPG, PNG o PDF."})

    filename = f"recibo_{order_id}_{int(datetime.now().timestamp())}{ext}"
    dest_path = UPLOADS_DIR / filename
    upload.save(str(dest_path))

    from app.database import get_connection
    with get_connection() as conn:
        conn.execute("UPDATE orders SET receipt_url = ? WHERE id = ?", (f"/static/uploads/{filename}", order_id))
        conn.commit()

    return json.dumps({"success": True, "receipt_url": f"/static/uploads/{filename}"})

@app.route('/api/consultar', method=['GET'])
def api_consultar():
    response.content_type = 'application/json'
    q = request.query.get("q", "").strip()
    if not q or len(q) < 3:
        return json.dumps({"orders": []})
    orders = find_purchases_by_query(q)
    return json.dumps({"orders": orders})

# ==================== API ADMINISTRACIÓN ====================

@app.route('/api/admin/login', method=['POST'])
def api_admin_login():
    response.content_type = 'application/json'
    payload = request.json or {}
    settings = get_settings()
    if str(payload.get("pin", "")).strip() == str(settings.get("admin_pin", "1722")).strip():
        return json.dumps({"authenticated": True})
    response.status = 401
    return json.dumps({"detail": "PIN de seguridad incorrecto"})

@app.route('/api/admin/orders/<order_id>/approve', method=['POST'])
def api_admin_approve_order(order_id):
    response.content_type = 'application/json'
    try:
        res = approve_order(order_id)
        order = get_order_by_id(order_id)
        if order:
            send_order_confirmation(order)
        return json.dumps(res)
    except ValueError as e:
        response.status = 400
        return json.dumps({"detail": str(e)})

@app.route('/api/admin/orders/<order_id>/reject', method=['POST'])
def api_admin_reject_order(order_id):
    response.content_type = 'application/json'
    try:
        return json.dumps(reject_order(order_id))
    except ValueError as e:
        response.status = 400
        return json.dumps({"detail": str(e)})

@app.route('/api/admin/cleanup-expired', method=['POST'])
def api_admin_cleanup_expired():
    response.content_type = 'application/json'
    settings = get_settings()
    timeout = settings.get("reservation_timeout_minutes", 30)
    freed = cleanup_expired_reservations(timeout)
    return json.dumps({"success": True, "freed_tickets": freed})

@app.route('/api/admin/manual-sale', method=['POST'])
def api_admin_manual_sale():
    response.content_type = 'application/json'
    payload = request.json or {}
    try:
        order = register_order(
            full_name=payload.get("full_name", "").strip(),
            cedula=payload.get("cedula", "").strip(),
            phone=payload.get("phone", "").strip(),
            email=payload.get("email", "").strip(),
            city=payload.get("city", "Colombia").strip(),
            tickets=payload.get("tickets", []),
            payment_method=payload.get("payment_method", "efectivo"),
            seller=payload.get("seller", "Administración"),
            notes=payload.get("notes"),
            auto_approve=True
        )
        send_order_confirmation(order)
        return json.dumps({"success": True, "order": order})
    except ValueError as e:
        response.status = 400
        return json.dumps({"detail": str(e)})

@app.route('/api/admin/check-winner', method=['POST'])
def api_admin_check_winner():
    response.content_type = 'application/json'
    payload = request.json or {}
    num_str = str(payload.get("number", "")).strip().zfill(4)
    return json.dumps(check_winning_number(num_str))

@app.route('/api/admin/update-settings', method=['POST'])
def api_admin_update_settings():
    response.content_type = 'application/json'
    payload = request.json or {}
    new_settings = save_settings(payload)
    return json.dumps({"success": True, "settings": new_settings})

@app.route('/api/admin/export-excel', method=['GET'])
def api_admin_export_excel():
    orders = get_all_orders(limit=10000)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Participantes"

    headers = [
        "ID Orden", "Cédula", "Nombre Completo", "Teléfono / WhatsApp",
        "Correo Electrónico", "Ciudad", "Vendedor / Asesor", "Cant. Boletas",
        "Total COP", "Estado", "Método de Pago", "Fecha Registro", "Números"
    ]
    ws.append(headers)

    for ord_item in orders:
        tickets_str = ", ".join(ord_item.get("tickets", []))
        ws.append([
            ord_item.get("id"),
            ord_item.get("cedula"),
            ord_item.get("full_name"),
            ord_item.get("phone"),
            ord_item.get("email"),
            ord_item.get("city"),
            ord_item.get("seller", "Web Directo"),
            ord_item.get("ticket_count"),
            ord_item.get("total_amount"),
            str(ord_item.get("status", "")).upper(),
            str(ord_item.get("payment_method", "")).upper(),
            ord_item.get("created_at"),
            tickets_str
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"reporte_sorteo_iphone17_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return output.getvalue()
