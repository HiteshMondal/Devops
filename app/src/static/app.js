const API = "/api/v1";
const columns = ["backlog", "in_progress", "done"];

const board = {
  backlog: document.getElementById("col-backlog"),
  in_progress: document.getElementById("col-in_progress"),
  done: document.getElementById("col-done"),
};
const counts = {
  backlog: document.getElementById("count-backlog"),
  in_progress: document.getElementById("count-in_progress"),
  done: document.getElementById("count-done"),
};
const statEls = {
  backlog: document.getElementById("stat-backlog"),
  in_progress: document.getElementById("stat-progress"),
  done: document.getElementById("stat-done"),
  total: document.getElementById("stat-total"),
};
const logEl = document.getElementById("log");
const form = document.getElementById("task-form");

function log(message) {
  const line = document.createElement("div");
  line.className = "log-line";
  const ts = new Date().toLocaleTimeString([], { hour12: false });
  line.innerHTML = `<span class="ts">${ts}</span>${escapeHtml(message)}`;
  logEl.prepend(line);
  while (logEl.childElementCount > 50) {
    logEl.removeChild(logEl.lastChild);
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  if (res.status === 204) return null;
  return res.json();
}

function makeCard(task) {
  const card = document.createElement("div");
  card.className = "card";
  card.draggable = true;
  card.dataset.id = task.id;
  card.dataset.priority = task.priority;

  card.innerHTML = `
    <p class="card-title"></p>
    <p class="card-desc"></p>
    <div class="card-meta">
      <span>#${task.id} · ${task.priority}</span>
      <span class="card-actions"><button title="Delete">✕</button></span>
    </div>
  `;
  card.querySelector(".card-title").textContent = task.title;
  card.querySelector(".card-desc").textContent = task.description || "";
  if (!task.description) card.querySelector(".card-desc").style.display = "none";

  card.querySelector(".card-actions button").addEventListener("click", async (e) => {
    e.stopPropagation();
    try {
      await api(`/tasks/${task.id}`, { method: "DELETE" });
      log(`removed task #${task.id} "${task.title}"`);
      await refresh();
    } catch (err) {
      log(`error: ${err.message}`);
    }
  });

  card.addEventListener("dragstart", (e) => {
    e.dataTransfer.setData("text/plain", task.id);
    card.style.opacity = "0.5";
  });
  card.addEventListener("dragend", () => {
    card.style.opacity = "1";
  });

  return card;
}

function wireDropzones() {
  columns.forEach((status) => {
    const zone = board[status];
    zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      zone.classList.add("drag-over");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
    zone.addEventListener("drop", async (e) => {
      e.preventDefault();
      zone.classList.remove("drag-over");
      const id = e.dataTransfer.getData("text/plain");
      try {
        await api(`/tasks/${id}`, {
          method: "PATCH",
          body: JSON.stringify({ status }),
        });
        log(`moved task #${id} → ${status}`);
        await refresh();
      } catch (err) {
        log(`error: ${err.message}`);
      }
    });
  });
}

async function refresh() {
  const [tasks, stats] = await Promise.all([api("/tasks"), api("/stats")]);

  columns.forEach((status) => (board[status].innerHTML = ""));
  const tally = { backlog: 0, in_progress: 0, done: 0 };

  tasks.forEach((task) => {
    board[task.status].appendChild(makeCard(task));
    tally[task.status] += 1;
  });

  columns.forEach((status) => (counts[status].textContent = tally[status]));
  statEls.backlog.textContent = stats.backlog;
  statEls.in_progress.textContent = stats.in_progress;
  statEls.done.textContent = stats.done;
  statEls.total.textContent = stats.total;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = document.getElementById("title").value.trim();
  const description = document.getElementById("description").value.trim();
  const priority = document.getElementById("priority").value;
  if (!title) return;

  try {
    const task = await api("/tasks", {
      method: "POST",
      body: JSON.stringify({ title, description, priority }),
    });
    log(`added task #${task.id} "${task.title}" (${priority})`);
    form.reset();
    document.getElementById("priority").value = "medium";
    await refresh();
  } catch (err) {
    log(`error: ${err.message}`);
  }
});

wireDropzones();
log("board initialized");
refresh().catch((err) => log(`error: ${err.message}`));