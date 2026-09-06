// Portfolio frontend — boilerplate, single file on purpose.
// All markup and styles are generated here; index.html only loads this file.
// Extend by adding more sections to renderApp() and more routes in main.py.

const STYLES = `
  :root {
    --bg: #0f1115; --surface: #171a21; --text: #e8e9ec; --muted: #9aa0ab;
    --accent: #5b8cff; --border: #262a33; font-family: system-ui, sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); line-height: 1.6; }
  header { padding: 3rem 1.5rem; text-align: center; border-bottom: 1px solid var(--border); }
  header h1 { font-size: 2.2rem; }
  header p { color: var(--muted); margin-top: .5rem; }
  main { max-width: 800px; margin: 0 auto; padding: 2rem 1.5rem; }
  section { margin-bottom: 3rem; }
  section h2 { margin-bottom: 1rem; font-size: 1.4rem; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
          padding: 1.25rem; margin-bottom: 1rem; }
  .card a { color: var(--accent); text-decoration: none; }
  form { display: flex; flex-direction: column; gap: .75rem; }
  input, textarea { background: var(--surface); border: 1px solid var(--border); color: var(--text);
                     padding: .7rem; border-radius: 8px; font: inherit; }
  button { background: var(--accent); color: #fff; border: none; padding: .7rem;
           border-radius: 8px; cursor: pointer; font: inherit; }
  button:disabled { opacity: .6; cursor: default; }
  .muted { color: var(--muted); font-size: .9rem; }
  footer { text-align: center; color: var(--muted); padding: 2rem; font-size: .85rem; }

  .auth-box { display: flex; flex-direction: column; gap: .75rem; max-width: 320px; }
  .auth-toggle { display: flex; gap: 1rem; margin-bottom: .5rem; }
  .auth-toggle button { background: none; border: none; color: var(--muted); cursor: pointer;
                         padding: 0; font: inherit; border-bottom: 2px solid transparent;
                         border-radius: 0; }
  .auth-toggle button.active { color: var(--text); border-color: var(--accent); }
  .auth-user-badge { display: flex; align-items: center; gap: .75rem; color: var(--muted); }
  .auth-user-badge button { width: auto; padding: .4rem .8rem; font-size: .85rem; }
  .auth-error { color: #ff6b6b; font-size: .85rem; min-height: 1.2em; }
`;

const TOKEN_KEY = "access_token";
const getToken = () => localStorage.getItem(TOKEN_KEY);
const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
const clearToken = () => localStorage.removeItem(TOKEN_KEY);

function injectStyles() {
  const style = document.createElement("style");
  style.textContent = STYLES;
  document.head.appendChild(style);
}

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

function renderShell() {
  document.body.innerHTML = `
    <header>
      <h1>Hitesh Mondal</h1>
      <p>Software Engineer — building things with code</p>
    </header>
    <main>
      <section id="about">
        <h2>About</h2>
        <p class="muted"> DevOps/SRE/SDE</p>
      </section>
      <section id="auth">
        <h2>Account</h2>
        <div id="auth-container" class="muted">Loading…</div>
      </section>
      <section id="projects">
        <h2>Projects</h2>
        <div id="projects-list" class="muted">Loading projects…</div>
      </section>
      <section id="contact">
        <h2>Contact</h2>
        <form id="contact-form">
          <input name="name" placeholder="Your name" required />
          <input name="email" type="email" placeholder="Your email" required />
          <textarea name="message" placeholder="Message" rows="4" required></textarea>
          <button type="submit">Send</button>
        </form>
        <p id="contact-status" class="muted"></p>
      </section>
    </main>
    <footer>Deployed via the platform &middot; ${new Date().getFullYear()}</footer>
  `;
}

async function loadProjects() {
  const listEl = document.getElementById("projects-list");
  try {
    const projects = await fetchJSON("/api/v1/projects");
    if (!projects.length) {
      listEl.textContent = "No projects added yet.";
      return;
    }
    listEl.innerHTML = projects.map(p => `
      <div class="card">
        <strong>${p.title}</strong>
        <p class="muted">${p.description || ""}</p>
        ${p.link ? `<a href="${p.link}" target="_blank" rel="noopener">${p.link}</a>` : ""}
      </div>
    `).join("");
  } catch (err) {
    listEl.textContent = "Could not load projects.";
    console.error(err);
  }
}

function wireContactForm() {
  const form = document.getElementById("contact-form");
  const status = document.getElementById("contact-status");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const button = form.querySelector("button");
    button.disabled = true;
    status.textContent = "Sending…";

    const data = Object.fromEntries(new FormData(form).entries());

    try {
      await fetchJSON("/api/v1/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      status.textContent = "Message sent — thanks!";
      form.reset();
    } catch (err) {
      status.textContent = "Something went wrong. Try again later.";
      console.error(err);
    } finally {
      button.disabled = false;
    }
  });
}

async function fetchMe() {
  const token = getToken();
  if (!token) return null;
  try {
    const res = await fetch("/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      clearToken();
      return null;
    }
    return res.json();
  } catch {
    return null;
  }
}

function renderAuthSection(container, user) {
  if (user) {
    container.innerHTML = `
      <div class="auth-user-badge">
        <span>Signed in as <strong>${user.email}</strong></span>
        <button id="logout-btn">Log out</button>
      </div>
    `;
    document.getElementById("logout-btn").addEventListener("click", () => {
      clearToken();
      renderAuthSection(container, null);
    });
    return;
  }

  let mode = "login"; // or "signup"

  function draw() {
    container.innerHTML = `
      <div class="auth-toggle">
        <button data-mode="login" class="${mode === "login" ? "active" : ""}">Log in</button>
        <button data-mode="signup" class="${mode === "signup" ? "active" : ""}">Sign up</button>
      </div>
      <form id="auth-form" class="auth-box">
        <input name="email" type="email" placeholder="Email" required />
        <input name="password" type="password" placeholder="Password" required minlength="8" />
        <button type="submit">${mode === "login" ? "Log in" : "Sign up"}</button>
        <p id="auth-error" class="auth-error"></p>
      </form>
    `;

    container.querySelectorAll(".auth-toggle button").forEach((btn) => {
      btn.addEventListener("click", () => {
        mode = btn.dataset.mode;
        draw();
      });
    });

    const form = document.getElementById("auth-form");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorEl = document.getElementById("auth-error");
      errorEl.textContent = "";

      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;

      const data = Object.fromEntries(new FormData(form).entries());
      const endpoint = mode === "login" ? "/api/v1/auth/login" : "/api/v1/auth/signup";

      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        const body = await res.json();

        if (!res.ok) {
          errorEl.textContent = body.detail || "Something went wrong.";
          submitBtn.disabled = false;
          return;
        }

        setToken(body.access_token);
        const user = await fetchMe();
        renderAuthSection(container, user);
      } catch (err) {
        errorEl.textContent = "Network error — try again.";
        submitBtn.disabled = false;
        console.error(err);
      }
    });
  }

  draw();
}

function renderApp() {
  injectStyles();
  renderShell();
  loadProjects();
  wireContactForm();

  const authContainer = document.getElementById("auth-container");
  fetchMe().then(user => renderAuthSection(authContainer, user));
}

document.addEventListener("DOMContentLoaded", renderApp);