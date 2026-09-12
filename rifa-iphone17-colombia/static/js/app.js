
function triggerConfetti() {
    if (typeof confetti === "function") {
        confetti({
            particleCount: 70,
            spread: 60,
            origin: { y: 0.6 }
        });
    }
}

// Estado global de la aplicación
const AppState = {
    selectedTickets: new Set(),
    unitPrice: 2000,
    minTickets: 5,
    currentRandomCount: 5
};

// 1. Contador Regresivo al 22 de Diciembre
function initCountdown() {
    // Sorteo: 22 de Diciembre 2026, 22:30:00 hora Colombia (UTC-5)
    const targetDate = new Date("2026-12-22T22:30:00-05:00").getTime();

    function update() {
        const now = new Date().getTime();
        const diff = targetDate - now;

        if (diff <= 0) {
            document.getElementById("cd-days").textContent = "00";
            document.getElementById("cd-hours").textContent = "00";
            document.getElementById("cd-minutes").textContent = "00";
            document.getElementById("cd-seconds").textContent = "00";
            return;
        }

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);

        const elDays = document.getElementById("cd-days");
        const elHours = document.getElementById("cd-hours");
        const elMinutes = document.getElementById("cd-minutes");
        const elSeconds = document.getElementById("cd-seconds");

        if (elDays) elDays.textContent = String(days).padStart(2, "0");
        if (elHours) elHours.textContent = String(hours).padStart(2, "0");
        if (elMinutes) elMinutes.textContent = String(minutes).padStart(2, "0");
        if (elSeconds) elSeconds.textContent = String(seconds).padStart(2, "0");
    }

    update();
    setInterval(update, 1000);
}

// 2. Selección de Packs
function selectPack(count) {
    AppState.currentRandomCount = count;
    switchMode('random');
    setRandomCount(count);
    generateRandomTickets();

    const selector = document.getElementById("selector");
    if (selector) {
        selector.scrollIntoView({ behavior: 'smooth' });
    }
}

function selectCustomPack() {
    const input = document.getElementById("custom-pack-input");
    const count = parseInt(input.value) || 5;
    if (count < 5) {
        Swal.fire({
            icon: 'warning',
            title: 'Mínimo 5 boletas',
            text: 'Debes seleccionar al menos 5 boletas para participar.',
            background: '#0f172a',
            color: '#fff'
        });
        return;
    }
    AppState.currentRandomCount = count;
    switchMode('random');
    generateRandomTicketsWithCount(count);
    
    const selector = document.getElementById("selector");
    if (selector) {
        selector.scrollIntoView({ behavior: 'smooth' });
    }
}

// 3. Cambio de pestaña (Azar vs Manual)
function switchMode(mode) {
    const btnRandom = document.getElementById("tab-btn-random");
    const btnManual = document.getElementById("tab-btn-manual");
    const panelRandom = document.getElementById("panel-random");
    const panelManual = document.getElementById("panel-manual");

    if (mode === 'random') {
        btnRandom.classList.add("bg-blue-600", "text-white", "shadow");
        btnRandom.classList.remove("text-slate-400");
        btnManual.classList.remove("bg-blue-600", "text-white", "shadow");
        btnManual.classList.add("text-slate-400");

        panelRandom.classList.remove("hidden");
        panelManual.classList.add("hidden");
    } else {
        btnManual.classList.add("bg-blue-600", "text-white", "shadow");
        btnManual.classList.remove("text-slate-400");
        btnRandom.classList.remove("bg-blue-600", "text-white", "shadow");
        btnRandom.classList.add("text-slate-400");

        panelManual.classList.remove("hidden");
        panelRandom.classList.add("hidden");
        loadSuggestedTickets();
    }
}

function setRandomCount(count) {
    AppState.currentRandomCount = count;
    document.querySelectorAll(".count-btn").forEach(btn => {
        if (parseInt(btn.dataset.count) === count) {
            btn.classList.add("border-blue-500", "bg-blue-600/20", "text-blue-400");
            btn.classList.remove("border-slate-700", "bg-slate-800", "text-white");
        } else {
            btn.classList.remove("border-blue-500", "bg-blue-600/20", "text-blue-400");
            btn.classList.add("border-slate-700", "bg-slate-800", "text-white");
        }
    });
}
// 4. Generación Aleatoria de Boletas
async function generateRandomTickets() {
    await generateRandomTicketsWithCount(AppState.currentRandomCount || 5);
}

async function generateRandomTicketsWithCount(count) {
    const btn = document.getElementById("btn-generate-random");
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader" class="w-5 h-5 animate-spin"></i><span>Asignando ${count} boletas...</span>`;
    lucide.createIcons();

    try {
        const response = await fetch("/api/random-tickets", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ count: count })
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Error al obtener números");
        }

        AppState.selectedTickets.clear();
        triggerConfetti();
        data.tickets.forEach(num => AppState.selectedTickets.add(num));
        renderCart();

        Swal.fire({
            icon: 'success',
            title: `¡${data.tickets.length} Boletas Asignadas!`,
            text: 'Revisa tus números en el carrito de abajo y continúa al pago.',
            timer: 2000,
            showConfirmButton: false,
            background: '#0f172a',
            color: '#fff'
        });

        // Scroll suave al carrito
        document.getElementById("cart-section").scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: err.message,
            background: '#0f172a',
            color: '#fff'
        });
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        lucide.createIcons();
    }
}

// 5. Elección Manual y Búsqueda
async function checkAndAddManualTicket() {
    const input = document.getElementById("manual-input");
    const feedback = document.getElementById("manual-check-feedback");
    const num = input.value.trim().padStart(4, "0");

    if (num.length !== 4 || isNaN(num)) {
        feedback.innerHTML = `<span class="text-red-400">Digita exactamente 4 cifras (ej: 0421).</span>`;
        return;
    }

    if (AppState.selectedTickets.has(num)) {
        feedback.innerHTML = `<span class="text-amber-400">El número ${num} ya está en tu lista.</span>`;
        return;
    }

    try {
        const res = await fetch(`/api/check-ticket/${num}`);
        const data = await res.json();

        if (data.status === "available") {
            AppState.selectedTickets.add(num);
            renderCart();
            feedback.innerHTML = `<span class="text-emerald-400">¡Número ${num} agregado a tu selección!</span>`;
            input.value = "";
        } else if (data.status === "reserved") {
            feedback.innerHTML = `<span class="text-amber-400">El número ${num} está actualmente apartado por otro comprador.</span>`;
        } else {
            feedback.innerHTML = `<span class="text-red-400">El número ${num} ya fue vendido. Elige otro.</span>`;
        }
    } catch (e) {
        feedback.innerHTML = `<span class="text-red-400">Error verificando el número.</span>`;
    }
}

async function loadSuggestedTickets() {
    const grid = document.getElementById("suggested-tickets-grid");
    grid.innerHTML = `<div class="col-span-full text-center text-slate-500 py-3">Cargando números...</div>`;

    try {
        const res = await fetch("/api/search-tickets?limit=24&status=available");
        const tickets = await res.json();

        grid.innerHTML = "";
        tickets.forEach(item => {
            const btn = document.createElement("button");
            btn.className = "p-2 rounded-xl bg-titanium-950 border border-slate-800 text-white font-mono text-sm font-bold hover:border-blue-500 hover:bg-blue-600/20 transition";
            btn.textContent = item.number;
            btn.onclick = () => {
                AppState.selectedTickets.add(item.number);
                renderCart();
            };
            grid.appendChild(btn);
        });
    } catch (e) {
        grid.innerHTML = `<div class="col-span-full text-center text-slate-500">No se pudieron cargar sugerencias.</div>`;
    }
}

// 6. Manejo del Carrito
function renderCart() {
    const container = document.getElementById("selected-tickets-container");
    const countBadge = document.getElementById("selected-count-badge");
    const totalEl = document.getElementById("cart-total-cop");
    const checkoutBtn = document.getElementById("btn-open-checkout");
    const count = AppState.selectedTickets.size;

    countBadge.textContent = `${count} boletas`;

    if (count === 0) {
        container.innerHTML = `
            <div class="text-xs text-slate-500 italic py-4 text-center w-full">
                Aún no has seleccionado números. Elige un pack arriba o haz clic en "Generar Números al Azar".
            </div>
        `;
        totalEl.textContent = "$0 COP";
        checkoutBtn.disabled = true;
        checkoutBtn.className = "w-full md:w-auto px-8 py-4 rounded-xl bg-slate-800 text-slate-500 font-bold text-sm sm:text-base cursor-not-allowed transition flex items-center justify-center space-x-2";
        return;
    }

    container.innerHTML = "";
    const sorted = Array.from(AppState.selectedTickets).sort();

    sorted.forEach(num => {
        const chip = document.createElement("div");
        chip.className = "ticket-chip inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-blue-500/40 text-blue-200 font-mono font-bold text-sm shadow-sm";
        chip.innerHTML = `
            <span>${num}</span>
            <button onclick="removeTicket('${num}')" class="text-slate-400 hover:text-red-400 transition ml-1" title="Quitar">
                ×
            </button>
        `;
        container.appendChild(chip);
    });

    const total = count * AppState.unitPrice;
    totalEl.textContent = `$${total.toLocaleString("es-CO")} COP`;

    // Actualizar barra flotante móvil
    const mobileBar = document.getElementById("mobile-sticky-bar");
    const mobileCount = document.getElementById("mobile-bar-count");
    const mobileTotal = document.getElementById("mobile-bar-total");
    if (mobileBar && mobileCount && mobileTotal) {
        if (count >= AppState.minTickets) {
            mobileCount.textContent = `${count} boletas seleccionadas`;
            mobileTotal.textContent = `$${total.toLocaleString("es-CO")} COP`;
            mobileBar.classList.remove("translate-y-full");
        } else {
            mobileBar.classList.add("translate-y-full");
        }
    }


    if (count >= AppState.minTickets) {
        checkoutBtn.disabled = false;
        checkoutBtn.className = "w-full md:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-black text-sm sm:text-base shadow-xl shadow-blue-600/30 transition transform hover:-translate-y-0.5 cursor-pointer flex items-center justify-center space-x-2";
    } else {
        checkoutBtn.disabled = true;
        checkoutBtn.className = "w-full md:w-auto px-8 py-4 rounded-xl bg-slate-800 text-amber-400 font-bold text-sm sm:text-base cursor-not-allowed transition flex items-center justify-center space-x-2";
    }
}

function removeTicket(num) {
    AppState.selectedTickets.delete(num);
    renderCart();
}

function clearSelectedTickets() {
    AppState.selectedTickets.clear();
        triggerConfetti();
    renderCart();
}

// 7. Modal de Checkout
function openCheckoutModal() {
    const count = AppState.selectedTickets.size;
    if (count < AppState.minTickets) {
        Swal.fire({
            icon: 'warning',
            title: 'Mínimo 5 boletas',
            text: `Debes tener al menos 5 boletas para continuar (actualmente tienes ${count}).`,
            background: '#0f172a',
            color: '#fff'
        });
        return;
    }

    const total = count * AppState.unitPrice;
    document.getElementById("modal-ticket-count").textContent = `${count} boletas`;
    document.getElementById("modal-total-amount").textContent = `$${total.toLocaleString("es-CO")} COP`;
    document.getElementById("checkout-modal").classList.remove("hidden");
}

function closeCheckoutModal() {
    document.getElementById("checkout-modal").classList.add("hidden");
}

// 8. Envío de la Orden
async function submitCheckout(event) {
    event.preventDefault();
    const btn = document.getElementById("btn-submit-order");
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader" class="w-5 h-5 animate-spin"></i><span>Procesando reserva...</span>`;
    lucide.createIcons();

    const ticketsArray = Array.from(AppState.selectedTickets);
    const paymentMethod = document.querySelector("input[name='payment_method']:checked").value;

    const payload = {
        full_name: document.getElementById("cust-name").value.trim(),
        cedula: document.getElementById("cust-cedula").value.trim(),
        phone: document.getElementById("cust-phone").value.trim(),
        email: document.getElementById("cust-email").value.trim(),
        city: document.getElementById("cust-city").value.trim(),
        tickets: ticketsArray,
        payment_method: paymentMethod,
        seller: (document.getElementById("cust-seller") ? document.getElementById("cust-seller").value.trim() : "Web Directo")
    };

    try {
        const res = await fetch("/api/checkout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Error al procesar la reserva");
        }

        const order = data.order;

        // Subir comprobante si se adjuntó archivo
        const receiptInput = document.getElementById("cust-receipt");
        if (receiptInput.files.length > 0) {
            const formData = new FormData();
            formData.append("file", receiptInput.files[0]);
            try {
                await fetch(`/api/upload-receipt/${order.order_id}`, {
                    method: "POST",
                    body: formData
                });
            } catch (uploadErr) {
                console.warn("No se pudo subir imagen directamente:", uploadErr);
            }
        }

        closeCheckoutModal();
        AppState.selectedTickets.clear();
        triggerConfetti();
        renderCart();

        // Alerta de éxito con botón a WhatsApp
        Swal.fire({
            icon: 'success',
            title: '¡Reserva Exitosa!',
            html: `
                <p style="font-size: 14px; margin-bottom: 12px; color: #cbd5e1;">
                    Tu orden <strong>${order.order_id}</strong> ha sido reservada con ${order.ticket_count} boletas.
                </p>
                <p style="font-size: 13px; color: #94a3b8; margin-bottom: 16px;">
                    Te enviamos un correo a <strong>${order.email}</strong>. Para validar el pago de tus boletas, haz clic abajo para enviar el comprobante por WhatsApp:
                </p>
                <a href="${data.whatsapp_url}" target="_blank" style="display:inline-block;background:#10B981;color:#fff;font-weight:bold;padding:12px 20px;border-radius:12px;text-decoration:none;font-size:14px;box-shadow:0 4px 12px rgba(16,185,129,0.3);">
                    📲 Enviar Comprobante por WhatsApp
                </a>
                <div style="margin-top: 16px;">
                    <a href="/boleto/${order.order_id}" style="color:#38bdf8;font-size:12px;text-decoration:underline;">
                        Ver mi Boleto Digital
                    </a>
                </div>
            `,
            showConfirmButton: false,
            showCloseButton: true,
            background: '#0f172a',
            color: '#fff'
        });

    } catch (err) {
        Swal.fire({
            icon: 'error',
            title: 'No se pudo completar',
            text: err.message,
            background: '#0f172a',
            color: '#fff'
        });
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="check-circle" class="w-5 h-5"></i><span>CONFIRMAR Y ENVIAR POR WHATSAPP</span>`;
        lucide.createIcons();
    }
}

// Inicialización en carga del DOM
document.addEventListener("DOMContentLoaded", () => {
    initCountdown();
    renderCart();
    initSocialProof();
    loadRange(0);
});


// 9. Notificaciones de Prueba Social (Compradores en vivo)
const colombianBuyers = [
    { name: "Andrés M.", city: "Medellín", pack: "10 boletas", time: "hace 3 minutos" },
    { name: "Valentina R.", city: "Bogotá", pack: "5 boletas", time: "hace 5 minutos" },
    { name: "Camilo T.", city: "Cali", pack: "20 boletas", time: "hace 1 minuto" },
    { name: "Daniela G.", city: "Barranquilla", pack: "10 boletas", time: "hace 7 minutos" },
    { name: "Felipe S.", city: "Bucaramanga", pack: "5 boletas", time: "hace 2 minutos" },
    { name: "Mateo C.", city: "Pereira", pack: "15 boletas", time: "hace 9 minutos" },
    { name: "Laura P.", city: "Cartagena", pack: "10 boletas", time: "hace 4 minutos" },
    { name: "Sebastián O.", city: "Manizales", pack: "20 boletas", time: "hace 6 minutos" }
];

function initSocialProof() {
    const toast = document.getElementById("social-proof-toast");
    const title = document.getElementById("toast-title");
    const desc = document.getElementById("toast-desc");
    const timeEl = document.getElementById("toast-time");
    if (!toast) return;

    let index = 0;
    function showNext() {
        const item = colombianBuyers[index % colombianBuyers.length];
        index++;

        title.textContent = `🎉 ${item.name} (${item.city})`;
        desc.textContent = `Acaba de adquirir el Pack de ${item.pack}`;
        timeEl.textContent = item.time;

        toast.classList.remove("translate-y-24", "opacity-0", "pointer-events-none");

        setTimeout(() => {
            toast.classList.add("translate-y-24", "opacity-0", "pointer-events-none");
        }, 5000);
    }

    // Primera aparición a los 4 segundos, luego cada 22 segundos
    setTimeout(() => {
        showNext();
        setInterval(showNext, 22000);
    }, 4000);
}


// 10. Explorador de 10.000 Boletas por Rangos
let currentActiveRange = 0;

async function loadRange(start) {
    currentActiveRange = start;
    const grid = document.getElementById("tickets-matrix-grid");
    const indicator = document.getElementById("current-range-indicator");
    if (!grid) return;

    // Actualizar botones de pestaña
    document.querySelectorAll(".range-tab-btn").forEach(btn => {
        if (parseInt(btn.dataset.start) === start) {
            btn.className = "range-tab-btn px-3.5 py-2 rounded-xl text-xs font-mono font-bold bg-orange-600 text-white shadow";
        } else {
            btn.className = "range-tab-btn px-3.5 py-2 rounded-xl text-xs font-mono font-bold bg-slate-800 text-slate-300 hover:text-white border border-slate-700";
        }
    });

    const endFormatted = String(start + 999).padStart(4, "0");
    const startFormatted = String(start).padStart(4, "0");
    if (indicator) {
        indicator.textContent = `Mostrando serie: ${startFormatted} - ${endFormatted} (1.000 boletas)`;
    }

    grid.innerHTML = `<div class="col-span-full py-8 text-center text-slate-400 text-xs flex items-center justify-center space-x-2"><i data-lucide="loader" class="w-4 h-4 animate-spin"></i><span>Cargando números de la serie ${startFormatted}...</span></div>`;
    lucide.createIcons();

    try {
        const res = await fetch(`/api/tickets-range?start=${start}&count=1000`);
        const data = await res.json();
        
        grid.innerHTML = "";
        data.tickets.forEach(item => {
            const btn = document.createElement("button");
            const isSelected = AppState.selectedTickets.has(item.n);

            if (item.s === "sold") {
                btn.className = "p-1.5 rounded-lg font-mono text-xs font-bold bg-red-950/40 border border-red-500/30 text-red-400 cursor-not-allowed opacity-50";
                btn.title = `Número ${item.n} - Ya Vendido`;
                btn.disabled = true;
            } else if (item.s === "reserved") {
                btn.className = "p-1.5 rounded-lg font-mono text-xs font-bold bg-amber-950/40 border border-amber-500/30 text-amber-400 cursor-not-allowed opacity-60";
                btn.title = `Número ${item.n} - Reservado temporalmente`;
                btn.disabled = true;
            } else if (isSelected) {
                btn.className = "p-1.5 rounded-lg font-mono text-xs font-bold bg-orange-600 border border-orange-400 text-white shadow-md shadow-orange-600/30";
                btn.title = `Número ${item.n} - En tu carrito`;
                btn.onclick = () => {
                    AppState.selectedTickets.delete(item.n);
                    renderCart();
                    loadRange(currentActiveRange);
                };
            } else {
                btn.className = "p-1.5 rounded-lg font-mono text-xs font-bold bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-600 hover:text-white transition";
                btn.title = `Número ${item.n} - Disponible (Clic para agregar)`;
                btn.onclick = () => {
                    AppState.selectedTickets.add(item.n);
                    renderCart();
                    loadRange(currentActiveRange);
                };
            }
            btn.textContent = item.n;
            grid.appendChild(btn);
        });

    } catch (e) {
        grid.innerHTML = `<div class="col-span-full py-4 text-center text-red-400 text-xs">Error cargando boletas.</div>`;
    }
}
