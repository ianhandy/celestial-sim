// Celestial Sim — all user-facing strings come from strings.json.
// Physics uses a softened inverse-square law in arbitrary units.

const G = 1.0;
const SOFT = 4.0;
const DT = 1 / 60;

let strings = {};
let bodies = [];
let running = true;
let timeScale = 1;
let showTrails = true;
let elapsedYears = 0;

const $ = (id) => document.getElementById(id);

async function loadStrings() {
  try {
    const res = await fetch("strings.json");
    if (!res.ok) throw new Error(res.statusText);
    strings = await res.json();
  } catch (err) {
    console.error(err);
    strings = { errors: { stringsLoadFailed: "Failed to load strings.json." } };
    alert(strings.errors.stringsLoadFailed);
  }
}

function lookup(path) {
  return path.split(".").reduce((o, k) => (o == null ? o : o[k]), strings) ?? "";
}

function applyStrings() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    const text = lookup(key);
    if (el.tagName === "TITLE") {
      document.title = text;
    } else {
      el.textContent = text;
    }
  });
}

function defaultBodies() {
  // Central star plus a few orbiting bodies in stable-ish circular orbits.
  const cx = 450, cy = 300;
  const star = { x: cx, y: cy, vx: 0, vy: 0, m: 20000, r: 14, color: "#ffd27a", trail: [] };
  const mk = (r, mass, color, phase = 0) => {
    const speed = Math.sqrt((G * star.m) / r);
    return {
      x: cx + r * Math.cos(phase),
      y: cy + r * Math.sin(phase),
      vx: -speed * Math.sin(phase),
      vy:  speed * Math.cos(phase),
      m: mass,
      r: Math.max(2, Math.cbrt(mass) * 0.9),
      color,
      trail: [],
    };
  };
  return [
    star,
    mk(70,   8,  "#9fd3ff", 0),
    mk(120, 20,  "#c5a0ff", 1.2),
    mk(180, 35,  "#7fe0a6", 2.4),
    mk(260, 15,  "#ff9f9f", 3.6),
  ];
}

function step(dt) {
  for (let i = 0; i < bodies.length; i++) {
    let ax = 0, ay = 0;
    const a = bodies[i];
    for (let j = 0; j < bodies.length; j++) {
      if (i === j) continue;
      const b = bodies[j];
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const r2 = dx * dx + dy * dy + SOFT * SOFT;
      const inv = 1 / Math.sqrt(r2);
      const f = (G * b.m) * inv * inv * inv;
      ax += f * dx;
      ay += f * dy;
    }
    a.vx += ax * dt;
    a.vy += ay * dt;
  }
  for (const b of bodies) {
    b.x += b.vx * dt;
    b.y += b.vy * dt;
    if (showTrails) {
      b.trail.push(b.x, b.y);
      if (b.trail.length > 400) b.trail.splice(0, b.trail.length - 400);
    } else if (b.trail.length) {
      b.trail.length = 0;
    }
  }
  elapsedYears += dt * 0.1;
}

function draw(ctx, canvas) {
  ctx.fillStyle = "rgba(3, 5, 10, 0.35)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  if (showTrails) {
    for (const b of bodies) {
      if (b.trail.length < 4) continue;
      ctx.strokeStyle = b.color + "66";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(b.trail[0], b.trail[1]);
      for (let i = 2; i < b.trail.length; i += 2) {
        ctx.lineTo(b.trail[i], b.trail[i + 1]);
      }
      ctx.stroke();
    }
  }

  for (const b of bodies) {
    ctx.fillStyle = b.color;
    ctx.beginPath();
    ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
    ctx.fill();
  }
}

function updateStats(fps) {
  $("stat-bodies").textContent = String(bodies.length);
  $("stat-elapsed").textContent = elapsedYears.toFixed(2);
  $("stat-fps").textContent = String(Math.round(fps));
}

function bindControls(canvas) {
  $("btn-play").addEventListener("click", () => { running = true; });
  $("btn-pause").addEventListener("click", () => { running = false; });
  $("btn-reset").addEventListener("click", () => {
    bodies = defaultBodies();
    elapsedYears = 0;
  });
  $("btn-clear").addEventListener("click", () => {
    bodies = [];
    elapsedYears = 0;
  });
  $("btn-add").addEventListener("click", () => {
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const r = 120 + Math.random() * 200;
    const phase = Math.random() * Math.PI * 2;
    const starMass = bodies[0]?.m ?? 20000;
    const speed = Math.sqrt((G * starMass) / r) * (0.8 + Math.random() * 0.4);
    bodies.push({
      x: cx + r * Math.cos(phase),
      y: cy + r * Math.sin(phase),
      vx: -speed * Math.sin(phase),
      vy:  speed * Math.cos(phase),
      m: 5 + Math.random() * 25,
      r: 3 + Math.random() * 3,
      color: `hsl(${Math.floor(Math.random() * 360)} 80% 70%)`,
      trail: [],
    });
  });

  $("speed").addEventListener("input", (e) => {
    timeScale = parseFloat(e.target.value);
  });
  $("trails").addEventListener("change", (e) => {
    showTrails = e.target.checked;
  });

  // Click to drop a body; drag to fling it.
  let dragStart = null;
  canvas.addEventListener("mousedown", (e) => {
    const { x, y } = canvasPoint(canvas, e);
    dragStart = { x, y };
  });
  canvas.addEventListener("mouseup", (e) => {
    if (!dragStart) return;
    const { x, y } = canvasPoint(canvas, e);
    bodies.push({
      x: dragStart.x,
      y: dragStart.y,
      vx: (x - dragStart.x) * 2,
      vy: (y - dragStart.y) * 2,
      m: 10,
      r: 4,
      color: "#ffffff",
      trail: [],
    });
    dragStart = null;
  });
}

function canvasPoint(canvas, e) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: ((e.clientX - rect.left) / rect.width) * canvas.width,
    y: ((e.clientY - rect.top) / rect.height) * canvas.height,
  };
}

async function main() {
  await loadStrings();
  applyStrings();

  const canvas = $("sky");
  const ctx = canvas.getContext("2d");

  bodies = defaultBodies();
  bindControls(canvas);

  let last = performance.now();
  let frame = 0;
  let fpsWindowStart = last;
  let fps = 0;

  function loop(now) {
    const dt = Math.min(0.05, (now - last) / 1000) * timeScale;
    last = now;
    if (running) step(dt);
    draw(ctx, canvas);

    frame++;
    if (now - fpsWindowStart >= 500) {
      fps = (frame * 1000) / (now - fpsWindowStart);
      frame = 0;
      fpsWindowStart = now;
      updateStats(fps);
    }

    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
}

main();
