// Admin logic and state
const AdminState = {
    isLoggedIn: false
};

function checkAdminAuth() {
    const token = sessionStorage.getItem("admin_auth");
    const overlay = document.getElementById("admin-login-overlay");
    const content = document.getElementById("admin-dashboard-content");

    if (token === "authenticated") {
        AdminState.isLoggedIn = true;
        if (overlay) overlay.classList.add("hidden");
        if (content) content.classList.remove("hidden");
        lucide.createIcons();
    } else {
        AdminState.isLoggedIn = false;
        if (overlay) overlay.classList.remove("hidden");
        if (content) content.classList.add("hidden");
    }
}

async function handleAdminLogin(event) {
    event.preventDefault();
    const pin = document.getElementById("admin-pin-input").value.trim();

    try {
        const res = await fetch("/api/admin/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pin: pin })
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "PIN incorrecto");
        }

        sessionStorage.setItem("admin_auth", "authenticated");
        checkAdminAuth();
        
        Swal.fire({
            icon: 'success',
            title: 'Bienvenido Administrador',
            timer: 1500,
            showConfirmButton: false,
            background: '#0f172a',
            color: '#fff'
        });

    } catch (e) {
        Swal.fire({
            icon: 'error',
            title: 'Acceso Denegado',
            text: e.message,
            background: '#0f172a',
            color: '#fff'
        });
    }
}

function logoutAdmin() {
    sessionStorage.removeItem("admin_auth");
    checkAdminAuth();
}

// Filtro de órdenes
function filterOrders(status) {
    document.querySelectorAll(".order-filter-btn").forEach(b => b.classList.remove("border-blue-500", "bg-blue-600/20"));
    
    document.querySelectorAll(".order-row").forEach(row => {
        if (status === 'all' || row.dataset.status === status) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}

// Aprobar Orden
async function approveOrder(orderId) {
    const result = await Swal.fire({
        title: `¿Aprobar Orden ${orderId}?`,
        text: "Las boletas pasarán a estado 'Vendida' de forma definitiva y se enviará correo de confirmación al comprador.",
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Sí, Aprobar Pago',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#10B981',
        cancelButtonColor: '#64748B',
        background: '#0f172a',
        color: '#fff'
    });

    if (!result.isConfirmed) return;

    try {
        const res = await fetch(`/api/admin/orders/${orderId}/approve`, { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Error al aprobar");

        Swal.fire({
            icon: 'success',
            title: '¡Orden Aprobada!',
            text: 'Las boletas ya están vendidas y aseguradas.',
            timer: 1800,
            showConfirmButton: false,
            background: '#0f172a',
            color: '#fff'
        }).then(() => {
            window.location.reload();
        });
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error', text: err.message, background: '#0f172a', color: '#fff' });
    }
}

// Rechazar Orden
async function rejectOrder(orderId) {
    const result = await Swal.fire({
        title: `¿Rechazar Orden ${orderId}?`,
        text: "Los números reservados volverán a estar inmediatamente DISPONIBLES para otros compradores.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, Rechazar y Liberar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#EF4444',
        cancelButtonColor: '#64748B',
        background: '#0f172a',
        color: '#fff'
    });

    if (!result.isConfirmed) return;

    try {
        const res = await fetch(`/api/admin/orders/${orderId}/reject`, { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Error al rechazar");

        Swal.fire({
            icon: 'info',
            title: 'Orden Rechazada',
            text: 'Las boletas han sido liberadas.',
            timer: 1800,
            showConfirmButton: false,
            background: '#0f172a',
            color: '#fff'
        }).then(() => {
            window.location.reload();
        });
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error', text: err.message, background: '#0f172a', color: '#fff' });
    }
}

// Selector y Verificador del Ganador Oficial
async function checkWinnerNumber() {
    const input = document.getElementById("winner-number-input");
    const box = document.getElementById("winner-result-box");
    const num = input.value.trim().padStart(4, "0");

    if (num.length !== 4 || isNaN(num)) {
        Swal.fire({
            icon: 'warning',
            title: 'Número Inválido',
            text: 'Debes ingresar un número de 4 cifras (ej: 0421 o 9999).',
            background: '#0f172a',
            color: '#fff'
        });
        return;
    }

    try {
        const res = await fetch("/api/admin/check-winner", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ number: num })
        });
        const data = await res.json();

        box.classList.remove("hidden");

        if (data.has_winner) {
            box.innerHTML = `
                <div class="bg-gradient-to-r from-emerald-950/80 to-slate-900 border-2 border-emerald-500 rounded-3xl p-6 sm:p-8 shadow-2xl">
                    <div class="flex items-center space-x-3 text-emerald-400 mb-4">
                        <i data-lucide="party-popper" class="w-8 h-8"></i>
                        <span class="text-2xl font-black uppercase tracking-wider">¡HAY GANADOR DEL iPHONE 17 PRO!</span>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-300">
                        <div class="space-y-2 bg-slate-950/70 p-4 rounded-2xl border border-slate-800">
                            <div><span class="text-slate-500 text-[10px]">Número Ganador Oficial:</span> <span class="text-2xl font-mono font-black text-amber-400 block">${data.number}</span></div>
                            <div><span class="text-slate-500 text-[10px]">Código de Orden:</span> <span class="font-mono text-white font-bold block">${data.order_id}</span></div>
                            <div><span class="text-slate-500 text-[10px]">Fecha de Aprobación:</span> <span class="text-white block">${data.approved_at || 'Confirmado'}</span></div>
                        </div>
                        <div class="space-y-2 bg-slate-950/70 p-4 rounded-2xl border border-slate-800">
                            <div><span class="text-slate-500 text-[10px]">Nombre del Ganador:</span> <strong class="text-lg text-white block">${data.buyer_name}</strong></div>
                            <div><span class="text-slate-500 text-[10px]">Cédula de Identidad:</span> <strong class="text-sm font-mono text-white block">${data.buyer_cedula}</strong></div>
                            <div><span class="text-slate-500 text-[10px]">Teléfono / WhatsApp:</span> <strong class="text-sm font-mono text-emerald-400 block">${data.buyer_phone}</strong></div>
                            <div><span class="text-slate-500 text-[10px]">Correo:</span> <strong class="text-white block">${data.buyer_email}</strong></div>
                        </div>
                    </div>
                    <div class="mt-6 flex flex-wrap gap-3">
                        <a href="https://wa.me/${data.buyer_phone.replace('+', '').replace(' ', '')}?text=¡Felicitaciones%20${encodeURIComponent(data.buyer_name)}!%20Eres%20el%20feliz%20ganador%20del%20iPhone%2017%20Pro%20con%20el%20número%20${data.number}" target="_blank" class="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg shadow-emerald-900/40 flex items-center">
                            <i data-lucide="message-circle" class="w-4 h-4 mr-1.5"></i> Contactar Ganador por WhatsApp
                        </a>
                        <a href="/boleto/${data.order_id}" target="_blank" class="px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs border border-slate-700 flex items-center">
                            <i data-lucide="file-text" class="w-4 h-4 mr-1.5"></i> Ver Certificado Oficial
                        </a>
                    </div>
                </div>
            `;
        } else if (data.status === "reserved") {
            box.innerHTML = `
                <div class="bg-amber-950/40 border border-amber-500/50 rounded-2xl p-6 text-amber-200 text-xs">
                    <h4 class="text-base font-bold mb-1 flex items-center"><i data-lucide="clock" class="w-5 h-5 mr-2"></i> El número ${data.number} está RESERVADO pero su pago aún no ha sido aprobado</h4>
                    <p>Revisa la lista de órdenes pendientes para validar si el pago de esta orden (${data.order_id}) ya fue realizado.</p>
                </div>
            `;
        } else {
            box.innerHTML = `
                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-slate-400 text-xs text-center">
                    <h4 class="text-base font-bold text-white mb-1">El número ${data.number} NO FUE VENDIDO</h4>
                    <p>La boleta se encontraba disponible en el momento del sorteo. Según el reglamento, el premio puede acumularse o jugarse con el siguiente sorteo oficial.</p>
                </div>
            `;
        }
        lucide.createIcons();

    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error', text: err.message, background: '#0f172a', color: '#fff' });
    }
}

// Modal Venta Manual
function openManualSaleModal() {
    document.getElementById("manual-sale-modal").classList.remove("hidden");
}
function closeManualSaleModal() {
    document.getElementById("manual-sale-modal").classList.add("hidden");
}

async function submitManualSale(event) {
    event.preventDefault();
    const count = parseInt(document.getElementById("man-count").value) || 5;

    try {
        // Obtener números al azar disponibles
        const rRes = await fetch("/api/random-tickets", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ count: count })
        });
        const rData = await rRes.json();
        if (!rRes.ok) throw new Error(rData.detail || "No hay suficientes boletas disponibles");

        const payload = {
            full_name: document.getElementById("man-name").value.trim(),
            cedula: document.getElementById("man-cedula").value.trim(),
            phone: document.getElementById("man-phone").value.trim(),
            email: document.getElementById("man-email").value.trim(),
            city: "Colombia",
            tickets: rData.tickets,
            payment_method: "efectivo",
            notes: "Registrado manualmente en administración"
        };

        const res = await fetch("/api/admin/manual-sale", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Error registrando venta");

        closeManualSaleModal();
        Swal.fire({
            icon: 'success',
            title: '¡Venta Registrada!',
            html: `Se asignaron y vendieron ${count} boletas a <strong>${payload.full_name}</strong>.<br>Boletas: ${rData.tickets.join(", ")}`,
            background: '#0f172a',
            color: '#fff'
        }).then(() => {
            window.location.reload();
        });

    } catch (e) {
        Swal.fire({ icon: 'error', title: 'Error', text: e.message, background: '#0f172a', color: '#fff' });
    }
}

// Guardar Configuración
async function saveGlobalSettings(event) {
    event.preventDefault();
    const payload = {
        prize_name: document.getElementById("set-prize").value.trim(),
        lottery_name: document.getElementById("set-lottery").value.trim(),
        nequi_number: document.getElementById("set-nequi").value.trim(),
        daviplata_number: document.getElementById("set-daviplata").value.trim(),
        bancolombia_account: document.getElementById("set-bancolombia").value.trim(),
        whatsapp_number: document.getElementById("set-whatsapp").value.trim(),
        admin_pin: document.getElementById("set-pin").value.trim()
    };

    try {
        const res = await fetch("/api/admin/update-settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("Error al guardar ajustes");

        Swal.fire({
            icon: 'success',
            title: '¡Configuración Guardada!',
            text: 'Los cambios ya están activos en toda la plataforma.',
            timer: 1500,
            showConfirmButton: false,
            background: '#0f172a',
            color: '#fff'
        });
    } catch (e) {
        Swal.fire({ icon: 'error', title: 'Error', text: e.message, background: '#0f172a', color: '#fff' });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    checkAdminAuth();
});


// Liberar reservas vencidas de más de 30 minutos
async function cleanupExpiredReservations() {
    try {
        const res = await fetch("/api/admin/cleanup-expired", { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error("Error al limpiar");

        Swal.fire({
            icon: 'info',
            title: 'Limpieza Completada',
            text: `Se han liberado ${data.freed_tickets} boletas de reservas vencidas (> 30 min).`,
            timer: 2000,
            showConfirmButton: false,
            background: '#0f172a',
            color: '#fff'
        }).then(() => {
            window.location.reload();
        });
    } catch (e) {
        Swal.fire({ icon: 'error', title: 'Error', text: e.message, background: '#0f172a', color: '#fff' });
    }
}
