import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from app.config import get_settings, BASE_DIR

EMAILS_DIR = BASE_DIR / "data" / "sent_emails"
EMAILS_DIR.mkdir(parents=True, exist_ok=True)

def build_order_email_html(order: Dict, settings: Dict) -> str:
    tickets_badges = "".join(
        f'<span style="display:inline-block;background:#059669;color:#ffffff;font-family:monospace;font-size:18px;font-weight:bold;padding:6px 14px;margin:4px;border-radius:8px;letter-spacing:2px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">{t}</span>'
        for t in order.get("tickets", [])
    )
    
    status_badge = (
        '<span style="background:#10B981;color:#ffffff;padding:4px 10px;border-radius:12px;font-weight:bold;font-size:12px;">PAGO CONFIRMADO</span>'
        if order.get("status") == "approved" else
        '<span style="background:#F59E0B;color:#ffffff;padding:4px 10px;border-radius:12px;font-weight:bold;font-size:12px;">RESERVADO (PENDIENTE VALIDACIÓN)</span>'
    )

    draw_date = settings.get("draw_date_display", "22 de Diciembre de 2026")
    lottery = settings.get("lottery_name", "Lotería Oficial")
    prize = settings.get("prize_name", "iPhone 17 Pro")
    total_cop = f"".replace(",", ".")
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Confirmación de Boletas - Sorteo {prize}</title>
    </head>
    <body style="margin:0;padding:0;background-color:#0b0f19;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#e2e8f0;">
        <div style="max-width:600px;margin:30px auto;background:#1e293b;border-radius:16px;overflow:hidden;border:1px solid #334155;box-shadow:0 10px 25px rgba(0,0,0,0.5);">
            <!-- Cabecera -->
            <div style="background:linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);padding:35px 25px;text-align:center;border-bottom:1px solid #3b82f6;">
                <h1 style="margin:0;color:#38bdf8;font-size:24px;letter-spacing:1px;text-transform:uppercase;">SORTEO OFICIAL COLOMBIA</h1>
                <p style="margin:8px 0 0 0;color:#f8fafc;font-size:20px;font-weight:bold;">¡Mucha suerte, {order.get('full_name')}!</p>
                <div style="margin-top:12px;">{status_badge}</div>
            </div>

            <!-- Contenido Principal -->
            <div style="padding:30px 25px;">
                <p style="font-size:15px;line-height:1.6;color:#cbd5e1;margin-top:0;">
                    Hola <strong>{order.get('full_name')}</strong>, gracias por participar en nuestro sorteo. A continuación encontrarás los detalles oficiales de tu compra y tus números asignados.
                </p>

                <!-- Tarjeta del Premio -->
                <div style="background:#0f172a;border-radius:12px;padding:18px;margin:20px 0;border:1px solid #334155;">
                    <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;">Premio Mayor</div>
                    <div style="font-size:18px;font-weight:bold;color:#f8fafc;margin-top:4px;">{prize}</div>
                    <div style="margin-top:12px;display:flex;justify-content:space-between;border-top:1px dashed #334155;padding-top:10px;font-size:14px;color:#94a3b8;">
                        <span>📅 Fecha del sorteo:</span>
                        <strong style="color:#e2e8f0;">{draw_date}</strong>
                    </div>
                    <div style="margin-top:6px;display:flex;justify-content:space-between;font-size:14px;color:#94a3b8;">
                        <span>🎰 Juega con:</span>
                        <strong style="color:#38bdf8;">{lottery}</strong>
                    </div>
                </div>

                <!-- Números asignados -->
                <div style="text-align:center;margin:30px 0;">
                    <div style="font-size:13px;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Tus Números de la Suerte ({len(order.get('tickets', []))} boletas):</div>
                    <div style="padding:15px;background:#0f172a;border-radius:12px;border:1px solid #1e293b;">
                        {tickets_badges}
                    </div>
                </div>

                <!-- Datos de registro -->
                <table style="width:100%;border-collapse:collapse;margin:25px 0;font-size:14px;">
                    <tr style="border-bottom:1px solid #334155;">
                        <td style="padding:10px 0;color:#94a3b8;">Código de Orden:</td>
                        <td style="padding:10px 0;text-align:right;font-family:monospace;font-weight:bold;color:#f8fafc;">{order.get('id')}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #334155;">
                        <td style="padding:10px 0;color:#94a3b8;">Cédula registrada:</td>
                        <td style="padding:10px 0;text-align:right;color:#f8fafc;">{order.get('cedula')}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #334155;">
                        <td style="padding:10px 0;color:#94a3b8;">Teléfono / WhatsApp:</td>
                        <td style="padding:10px 0;text-align:right;color:#f8fafc;">{order.get('phone')}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #334155;">
                        <td style="padding:10px 0;color:#94a3b8;">Total Pagado / a Pagar:</td>
                        <td style="padding:10px 0;text-align:right;font-size:16px;font-weight:bold;color:#10b981;">{total_cop} COP</td>
                    </tr>
                    <tr>
                        <td style="padding:10px 0;color:#94a3b8;">Método de Pago:</td>
                        <td style="padding:10px 0;text-align:right;text-transform:uppercase;font-weight:bold;color:#f8fafc;">{order.get('payment_method')}</td>
                    </tr>
                </table>

                <!-- Información Importante -->
                <div style="background:#1e3a8a22;border:1px solid #1e40af;border-radius:10px;padding:14px;margin-top:20px;font-size:13px;color:#93c5fd;line-height:1.5;">
                    💡 <strong>Para reclamar el premio:</strong> El ganador deberá presentar su documento de identidad original ({order.get('cedula')}) que coincida con este registro oficial. Guarda este correo como comprobante.
                </div>
            </div>

            <!-- Pie de página -->
            <div style="background:#0f172a;padding:20px;text-align:center;border-top:1px solid #334155;font-size:12px;color:#64748b;">
                <p style="margin:0;">Sorteo iPhone 17 Pro Colombia • Válido a nivel nacional</p>
                <p style="margin:6px 0 0 0;">Si tienes dudas, contáctanos por WhatsApp al +{settings.get('whatsapp_number')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_order_confirmation(order: Dict) -> bool:
    settings = get_settings()
    recipient_email = order.get("email")
    if not recipient_email:
        return False

    html_content = build_order_email_html(order, settings)
    
    # Guardar siempre copia local de respaldo
    safe_order_id = order.get("id", "unknown").replace("/", "_")
    email_file = EMAILS_DIR / f"{safe_order_id}_{int(datetime.now().timestamp())}.html"
    try:
        with open(email_file, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception as e:
        print(f"[Email] Error guardando copia local: {e}")

    # Si SMTP está habilitado y configurado
    if settings.get("smtp_enabled") and settings.get("smtp_user") and settings.get("smtp_password"):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🎟️ Tus números del Sorteo iPhone 17 Pro ({len(order.get('tickets', []))} boletas)"
            msg["From"] = settings.get("smtp_from", settings.get("smtp_user"))
            msg["To"] = recipient_email
            
            part = MIMEText(html_content, "html", "utf-8")
            msg.attach(part)

            server = smtplib.SMTP(settings.get("smtp_host"), int(settings.get("smtp_port", 587)))
            server.starttls()
            server.login(settings.get("smtp_user"), settings.get("smtp_password"))
            server.sendmail(msg["From"], [recipient_email], msg.as_string())
            server.quit()
            print(f"[Email] Correo enviado exitosamente a {recipient_email}")
            return True
        except Exception as ex:
            print(f"[Email] Falló envío SMTP a {recipient_email}: {ex}. Guardado localmente en {email_file}")
            return False
    else:
        print(f"[Email] Simulación: correo generado para {recipient_email} y archivado en {email_file}")
        return True
