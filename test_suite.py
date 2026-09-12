import io
import json
from app.main import app
from app.database import get_stats

def call_wsgi(path, method="GET", body=None, content_type="application/json"):
    body_bytes = b""
    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif body is not None:
        body_bytes = json.dumps(body).encode("utf-8")

    env = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(body_bytes),
        "wsgi.errors": io.StringIO(),
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
        "CONTENT_TYPE": content_type if body else "",
        "CONTENT_LENGTH": str(len(body_bytes)),
    }
    
    status_box = []
    headers_box = []
    def start_response(status, headers, exc_info=None):
        status_box.append(status)
        headers_box.append(headers)
        
    result = app(env, start_response)
    response_body = b"".join(result)
    status_code = int(status_box[0].split()[0])
    return status_code, response_body

print("=== 1. Probando Estadísticas Iniciales ===")
stats = get_stats()
print("Total tickets en DB:", stats["total_tickets"])
assert stats["total_tickets"] == 10000

print("\n=== 2. Probando Páginas HTML ===")
for p in ["/", "/consultar", "/admin", "/terminos"]:
    status, body = call_wsgi(p)
    assert status == 200, f"Fallo en {p}: {status}"
    print(f"Ruta {p}: OK (200, {len(body)} bytes)")

print("\n=== 3. Probando Validación de Mínimo 5 Boletas ===")
status, body = call_wsgi("/api/random-tickets", method="POST", body={"count": 4})
assert status == 400, "Debe rechazar 4 boletas"
print("Validación de mínimo: OK (400 recibido al pedir 4 boletas)")

status, body = call_wsgi("/api/random-tickets", method="POST", body={"count": 5})
assert status == 200
data_r = json.loads(body.decode("utf-8"))
tickets = data_r["tickets"]
assert len(tickets) == 5
print("Asignación de 5 números al azar:", tickets)

print("\n=== 4. Probando Checkout / Creación de Orden ===")
order_payload = {
    "full_name": "Edwin Garavito",
    "cedula": "1032456789",
    "phone": "3105559999",
    "email": "edwin.test@gmail.com",
    "city": "Bogotá D.C.",
    "tickets": tickets,
    "payment_method": "nequi"
}
status, body = call_wsgi("/api/checkout", method="POST", body=order_payload)
assert status == 200, f"Error checkout: {body.decode('utf-8')}"
res_data = json.loads(body.decode("utf-8"))
order_id = res_data["order"]["order_id"]
print("Orden creada:", order_id)
print("Total:", res_data["order"]["total_amount"], "COP")
print("WhatsApp URL:", res_data["whatsapp_url"][:60], "...")
assert res_data["order"]["total_amount"] == 10000

print("\n=== 5. Probando Verificación de Boleto Digital ===")
status, body = call_wsgi(f"/boleto/{order_id}")
assert status == 200
print(f"Boleto digital /boleto/{order_id}: OK (200, {len(body)} bytes)")

print("\n=== 6. Probando Verificador de Ganador (Antes de Aprobar Pago) ===")
status, body = call_wsgi("/api/admin/check-winner", method="POST", body={"number": tickets[0]})
assert status == 200
win_chk = json.loads(body.decode("utf-8"))
assert win_chk["status"] == "reserved"
print(f"Número {tickets[0]} detectado como RESERVADO (aún no aprobado): OK")

print("\n=== 7. Probando Aprobación de Orden por el Administrador ===")
status, body = call_wsgi(f"/api/admin/orders/{order_id}/approve", method="POST")
assert status == 200
print("Orden aprobada por administración: OK")

print("\n=== 8. Probando Verificador de Ganador (Con Pago Aprobado) ===")
status, body = call_wsgi("/api/admin/check-winner", method="POST", body={"number": tickets[0]})
assert status == 200
win_data = json.loads(body.decode("utf-8"))
assert win_data["has_winner"] is True
assert win_data["buyer_name"] == "Edwin Garavito"
assert win_data["buyer_cedula"] == "1032456789"
print(f"¡HAY GANADOR OFICIAL! Boleta {tickets[0]} -> {win_data['buyer_name']} ({win_data['buyer_phone']})")

print("\n=== 9. Probando Exportación de Excel ===")
status, body = call_wsgi("/api/admin/export-excel")
assert status == 200
assert len(body) > 1000
print(f"Descarga de archivo Excel (.xlsx): OK ({len(body)} bytes)")

print("\n==============================================")
print("[OK] ¡TODAS LAS PRUEBAS FUNCIONARON PERFECTAMENTE!")
print("==============================================")
