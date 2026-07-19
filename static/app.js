const elements = {
  panel: document.querySelector("#instructor-panel"),
  toastStack: document.querySelector("#toast-stack"),
  countdownOverlay: document.querySelector("#countdown-overlay"),
  countdownOverlayNumber: document.querySelector("#countdown-overlay-number"),
  showPanel: document.querySelector("#show-panel"),
  hidePanel: document.querySelector("#hide-panel"),
  startBlackFriday: document.querySelector("#start-black-friday"),
  toggleLoad: document.querySelector("#toggle-load"),
  resetDemo: document.querySelector("#reset-demo"),
  topStatus: document.querySelector("#top-status"),
  eventPill: document.querySelector("#event-pill"),
  countdown: document.querySelector("#countdown"),
  heroTitle: document.querySelector("#hero-title"),
  heroEyebrow: document.querySelector("#hero-eyebrow"),
  heroPhoto: document.querySelector("#hero-photo"),
  heroDescription: document.querySelector("#hero-description"),
  discountTag: document.querySelector("#discount-tag"),
  cloudStatus: document.querySelector("#cloud-status"),
  productsTitle: document.querySelector("#products-title"),
  activeUsers: document.querySelector("#active-users"),
  requestsPerSecond: document.querySelector("#requests-per-second"),
  averageCpu: document.querySelector("#average-cpu"),
  cpuFill: document.querySelector("#cpu-fill"),
  activeInstances: document.querySelector("#active-instances"),
  serverBars: document.querySelector("#server-bars"),
  instanceName: document.querySelector("#instance-name"),
  instanceIp: document.querySelector("#instance-ip"),
  responseTime: document.querySelector("#response-time"),
};

let blackFridayApplied = false;
let lastInstanceId = "";
let loadTimer = null;
let loadRunning = false;

function formatBRL(value) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number(value || 0));
}

let virtualUserPoolSize = 0;
let virtualUserCursor = 0;
const MAX_BROWSER_VIRTUAL_USERS = 120;
let warnedHighCpu = false;
let lastInstanceCount = 1;
let blackFridayToastShown = false;
let lastCountdownOverlaySecond = null;

function showToast(title, message, type = "") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`.trim();
  toast.innerHTML = `<strong>${title}</strong><span>${message}</span>`;
  elements.toastStack.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(-6px)";
  }, 4200);

  setTimeout(() => toast.remove(), 4700);
}

function updateFinalCountdown(seconds) {
  const value = Number(seconds);

  if (value > 0 && value <= 3) {
    elements.countdownOverlay.classList.add("visible");

    if (lastCountdownOverlaySecond !== value) {
      elements.countdownOverlayNumber.textContent = value;
      elements.countdownOverlayNumber.style.animation = "none";
      void elements.countdownOverlayNumber.offsetWidth;
      elements.countdownOverlayNumber.style.animation = "countdownPulse .8s ease";
      lastCountdownOverlaySecond = value;
    }
  } else {
    elements.countdownOverlay.classList.remove("visible");
    lastCountdownOverlaySecond = null;
  }
}

function getClientId() {
  const key = "cloud-demo-client";
  let id = sessionStorage.getItem(key);

  if (!id) {
    id = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
    sessionStorage.setItem(key, id);
  }

  return id;
}

function formatCountdown(seconds) {
  return `00:${String(Math.max(0, Number(seconds) || 0)).padStart(2, "0")}`;
}

function animateNumber(element, value) {
  const previous = Number(element.dataset.value || 0);
  const next = Number(value || 0);
  element.dataset.value = next;

  const started = performance.now();
  const duration = 260;

  function frame(now) {
    const progress = Math.min((now - started) / duration, 1);
    const current = Math.round(previous + (next - previous) * progress);
    element.textContent = current.toLocaleString("pt-BR");

    if (progress < 1) {
      requestAnimationFrame(frame);
    }
  }

  requestAnimationFrame(frame);
}

function friendlyInstanceName(instanceId) {
  if (!instanceId) return "EC2-01";
  if (instanceId.startsWith("ip-")) return instanceId;
  const cleaned = instanceId.replace(/[^a-zA-Z0-9]/g, "").slice(-4).toUpperCase();
  return `EC2-${cleaned || "01"}`;
}

function renderServerBars(count) {
  elements.serverBars.innerHTML = "";
  const safeCount = Math.max(1, Math.min(8, Number(count) || 1));

  for (let i = 0; i < safeCount; i += 1) {
    const bar = document.createElement("span");
    bar.className = "server-bar";
    elements.serverBars.appendChild(bar);
  }
}

function applyBlackFriday() {
  if (blackFridayApplied) {
    return;
  }

  blackFridayApplied = true;
  lastCountdownOverlaySecond = null;

  elements.countdownOverlay.classList.remove("visible");

  if (!blackFridayToastShown) {
    showToast(
      "Black Friday iniciada",
      "A campanha promocional está no ar.",
      "success"
    );

    blackFridayToastShown = true;
  }

  document.body.classList.add("black-friday", "flash");

  elements.eventPill.classList.add("hidden");
  elements.countdown.classList.add("hidden");

  elements.heroEyebrow.classList.remove("hidden");
  elements.heroEyebrow.textContent =
    window.STORE_DATA.heroEyebrowBlackFriday;

  elements.heroTitle.textContent =
    "A maior virada de preços começou.";

  elements.heroDescription.textContent =
    "Ofertas relâmpago, tráfego em alta e uma infraestrutura preparada para manter o site disponível.";

  elements.discountTag.textContent =
    document.body.dataset.badgeBf;

  elements.heroPhoto.src =
    document.body.dataset.heroBf;

  elements.productsTitle.textContent =
    "Ofertas de Black Friday";

  document.querySelectorAll(".product-card").forEach((card) => {
    const price = card.querySelector(".current-price");

    if (price && card.dataset.bfPrice) {
      price.textContent = formatBRL(card.dataset.bfPrice);
    }
  });

  setTimeout(() => {
    document.body.classList.remove("flash");
  }, 900);
}

function resetVisualState() {
  blackFridayApplied = false;
  blackFridayToastShown = false;
  warnedHighCpu = false;
  lastInstanceCount = 1;
  lastCountdownOverlaySecond = null;

  elements.toastStack.innerHTML = "";
  elements.countdownOverlay.classList.remove("visible");

  document.body.classList.remove("black-friday", "flash");

  elements.eventPill.classList.add("hidden");
  elements.countdown.classList.add("hidden");

  elements.heroEyebrow.classList.remove("hidden");
  elements.heroEyebrow.textContent =
    window.STORE_DATA.heroEyebrowNormal;

  elements.heroTitle.textContent =
    "Performance que acompanha você.";

  elements.heroDescription.textContent =
    "Produtos selecionados, entrega rápida e uma experiência preparada para permanecer disponível.";

  elements.discountTag.textContent =
    document.body.dataset.badgeNormal;

  elements.heroPhoto.src =
    document.body.dataset.heroNormal;

  elements.productsTitle.textContent =
    "Tecnologia em destaque";

  document.querySelectorAll(".product-card").forEach((card) => {
    const price = card.querySelector(".current-price");

    if (price && card.dataset.normalPrice) {
      price.textContent = formatBRL(card.dataset.normalPrice);
    }
  });
}

async function postAction(path) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Falha ao executar ${path}`);
  }

  return response.json();
}

function startBrowserLoad() {
  if (loadTimer) return;

  loadRunning = true;
  virtualUserPoolSize = 4;
  virtualUserCursor = 0;
  elements.toggleLoad.classList.add("active");
  elements.toggleLoad.textContent = "⏹ Parar carga controlada";

  loadTimer = setInterval(() => {
    // Aumenta gradualmente a quantidade de usuários virtuais.
    virtualUserPoolSize = Math.min(
      MAX_BROWSER_VIRTUAL_USERS,
      virtualUserPoolSize + 4
    );

    // Mantém uma carga moderada no navegador, alternando entre os usuários
    // virtuais para que todos permaneçam ativos na janela de 30 segundos.
    const requestsPerCycle = Math.min(16, virtualUserPoolSize);

    for (let i = 0; i < requestsPerCycle; i += 1) {
      const virtualUser = virtualUserCursor % virtualUserPoolSize;
      virtualUserCursor += 1;

      fetch(`/api/load?work_ms=180&n=${Date.now()}-${i}`, {
        cache: "no-store",
        headers: {
          "X-Demo-Client": `browser-vu-${virtualUser}`,
        },
      }).catch(() => {});
    }
  }, 350);
}

function stopBrowserLoad() {
  loadRunning = false;
  virtualUserPoolSize = 0;
  virtualUserCursor = 0;
  clearInterval(loadTimer);
  loadTimer = null;
  elements.toggleLoad.classList.remove("active");
  elements.toggleLoad.textContent = "⚡ Iniciar carga controlada";
}

function updateDemoPhase(data) {
  if (data.phase === "countdown") {
    // Durante a contagem, mostramos apenas o pill e o cronômetro.
    elements.heroEyebrow.classList.add("hidden");

    elements.eventPill.classList.remove("hidden");
    elements.eventPill.textContent =
      "BLACK FRIDAY COMEÇA EM";

    elements.countdown.classList.remove("hidden");
    elements.countdown.textContent =
      formatCountdown(data.seconds_remaining);

    updateFinalCountdown(data.seconds_remaining);
    return;
  }

  if (data.phase === "black_friday") {
    updateFinalCountdown(0);
    applyBlackFriday();
    return;
  }

  // Estado normal.
  updateFinalCountdown(0);
}

async function refreshStatus() {
  try {
    const started = performance.now();
    const response = await fetch("/api/status", {
      cache: "no-store",
      headers: { "X-Demo-Client": getClientId() },
    });

    const data = await response.json();
    const browserLatency = Math.round(performance.now() - started);

    updateDemoPhase(data);

    animateNumber(elements.activeUsers, data.active_users);
    animateNumber(elements.requestsPerSecond, Math.round(data.requests_per_second || 0));
    animateNumber(elements.activeInstances, data.active_instance_count || 1);

    const cpu = Math.max(0, Math.min(100, Number(data.average_cpu || 0)));
    elements.averageCpu.textContent = `${cpu.toFixed(0)}%`;
    elements.cpuFill.style.width = `${cpu}%`;
    elements.cpuFill.style.background =
      cpu >= 80 ? "#ff5c3d" : cpu >= 55 ? "#ffc36a" : "#41d39b";

    if (cpu >= 70 && !warnedHighCpu) {
      showToast("Pico de processamento", `CPU média em ${cpu.toFixed(0)}%.`, "warning");
      warnedHighCpu = true;
    }

    if (cpu < 55) {
      warnedHighCpu = false;
    }

    if (Number(data.active_instance_count || 1) > lastInstanceCount) {
      showToast(
        "Novo servidor detectado",
        `${friendlyInstanceName(data.instance_id)} entrou em operação.`,
        "success"
      );
    }

    lastInstanceCount = Number(data.active_instance_count || 1);

    renderServerBars(data.active_instance_count || 1);

    const friendlyName = friendlyInstanceName(data.instance_id);
    elements.instanceName.textContent = friendlyName;
    elements.instanceIp.textContent = `IP: ${data.instance_ip}`;
    elements.responseTime.textContent = `${data.average_response_ms || browserLatency} ms`;
    elements.cloudStatus.textContent = data.status_label;
    elements.topStatus.textContent = data.status_label;

    if (lastInstanceId && lastInstanceId !== data.instance_id) {
      const serverCard = elements.instanceName.closest(".server-card");
      serverCard.classList.add("flash-server");
      setTimeout(() => serverCard.classList.remove("flash-server"), 800);
    }
    lastInstanceId = data.instance_id;

    if (data.load_mode && !loadRunning) {
      startBrowserLoad();
    } else if (!data.load_mode && loadRunning) {
      stopBrowserLoad();
    }
  } catch (error) {
    elements.cloudStatus.textContent = "Atualização indisponível";
  }
}

elements.startBlackFriday.addEventListener("click", async () => {
  try {
    await postAction("/api/demo/start-black-friday");

    elements.heroEyebrow.classList.add("hidden");

    elements.eventPill.classList.remove("hidden");
    elements.eventPill.textContent =
      "BLACK FRIDAY COMEÇA EM";

    elements.countdown.classList.remove("hidden");
  } catch (error) {
    console.error(error);

    showToast(
      "Não foi possível iniciar",
      "Tente novamente em alguns instantes.",
      "warning"
    );
  }
});

elements.toggleLoad.addEventListener("click", async () => {
  const result = await postAction("/api/demo/toggle-load");
  if (result.load_mode) {
    showToast("Carga controlada iniciada", "Usuários virtuais estão acessando a aplicação.", "warning");
  } else {
    showToast("Carga controlada encerrada", "O tráfego começará a diminuir.", "success");
  }
});

elements.resetDemo.addEventListener("click", async () => {
  stopBrowserLoad();
  await postAction("/api/demo/reset");
  resetVisualState();
  await refreshStatus();
});

elements.hidePanel.addEventListener("click", () => {
  elements.panel.style.display = "none";
  elements.showPanel.style.display = "block";
});

elements.showPanel.addEventListener("click", () => {
  elements.panel.style.display = "block";
  elements.showPanel.style.display = "none";
});

document.addEventListener("keydown", async (event) => {
  const key = event.key.toLowerCase();

  if (key === "b") {
    await postAction("/api/demo/start-black-friday");
  }

  if (key === "l") {
    await postAction("/api/demo/toggle-load");
  }

  if (key === "r") {
    stopBrowserLoad();
    await postAction("/api/demo/reset");
    resetVisualState();
  }

  if (key === "h") {
    const hidden = elements.panel.style.display === "none";
    elements.panel.style.display = hidden ? "block" : "none";
    elements.showPanel.style.display = hidden ? "none" : "block";
  }
});

refreshStatus();
setInterval(refreshStatus, 1000);
