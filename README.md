# 🎟️ Portal Web Sorteo iPhone 17 Pro Max • Colombia

Plataforma web completa desarrollada con **FastAPI**, **SQLite**, **Tailwind CSS** y **JavaScript** para la gestión y venta del sorteo de un **iPhone 17 Pro Max (256GB)** en Colombia con 10.000 números (del 0000 al 9999) y compra mínima en packs desde 5 boletas ($10.000 COP).

---

## 📱 Características Principales

1. **Emisión de 10.000 Boletas**:
   - Formato exacto de 4 cifras: `0000` al `9999`, ideal para el Premio Mayor de cualquier lotería colombiana.
   - Base de datos SQLite optimizada con transacciones ACID y modo WAL.
2. **Packs y Compra Mínima (Desde $2.000 COP por boleta)**:
   - **Pack 1**: 5 Boletas ($10.000 COP) - Opción mínima requerida.
   - **Pack 2**: 10 Boletas ($20.000 COP) - Más popular.
   - **Pack 3**: 20 Boletas ($40.000 COP) - Mayor probabilidad.
   - **Pack Personalizado**: Campo libre para compras mayores (ej. 30, 50, 100 boletas).
3. **Doble Modalidad de Selección**:
   - **Máquina de la Suerte (Automático)**: Genera números disponibles al azar al instante.
   - **Buscador Manual**: Permite buscar cualquier número favorito de 4 cifras y comprobar su disponibilidad en tiempo real.
4. **Checkout y Pagos en Colombia**:
   - Información de cuentas para **Nequi**, **Daviplata** y **Bancolombia**.
   - Botón directo para adjuntar comprobante y enviar mensaje prellenado a **WhatsApp** al organizador.
   - Generación de boleta digital oficial con enlace directo.
5. **Notificaciones por Correo Electrónico**:
   - Envío automático de confirmación en HTML con los números asignados, código de orden y datos de reclamo.
   - Modo simulación integrado (guarda copias en `data/sent_emails/`) o envío real con SMTP (Gmail, Outlook, etc.).
6. **Módulo Público de Consulta (`/consultar`)**:
   - Los compradores pueden ingresar su cédula o teléfono en cualquier momento para ver sus números comprados y el estado de su pago.
7. **Panel de Administración Completo (`/admin`)**:
   - **PIN de Acceso**: `1722` (configurable desde el panel).
   - Métricas en tiempo real: Total recaudado ($ COP), boletas vendidas, boletas reservadas y boletas disponibles.
   - Gestión y aprobación de pedidos (marcar como vendida y confirmar por correo).
   - **Selector de Ganador**: Ingresa las 4 cifras del sorteo del 22 de diciembre y el sistema detecta de inmediato al ganador con su nombre, cédula, teléfono y correo, con botón directo para felicitarlo por WhatsApp.
   - **Venta Manual**: Registrar ventas directas en efectivo.
   - **Exportación a Excel**: Descarga de toda la base de datos de compradores y sus boletas en `.xlsx`.
   - Editor de cuentas bancarias y nombre de lotería.

---

## 🚀 Cómo Iniciar el Portal

### 1. Activar / Instalar Dependencias
```powershell
pip install -r requirements.txt
```

### 2. Ejecutar el Servidor
```powershell
python run.py
```

El portal estará disponible en:
- **Página Principal**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Consultar Boletas**: [http://127.0.0.1:8000/consultar](http://127.0.0.1:8000/consultar)
- **Panel Administrativo**: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) (PIN: `1722`)
- **Documentación de la API**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔒 Seguridad y Configuración

Los datos de configuración se almacenan en `data/settings.json`. Puedes modificar:
- Nombre de la lotería oficial que juega el 22 de Diciembre.
- Cuentas de Nequi, Daviplata y Bancolombia.
- Teléfono de WhatsApp para atención y comprobantes.
- PIN de acceso al panel administrativo.
- Configuración de correo SMTP.
