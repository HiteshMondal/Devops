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
`;

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
      <h1>Your Name</h1>
      <p>Software Engineer — building things with code</p>
    </header>
    <main>
      <section id="about">
        <h2>About</h2>
        <p class="muted">Short bio goes here. Edit this in static/app.js.</p>
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

function renderApp() {
  injectStyles();
  renderShell();
  loadProjects();
  wireContactForm();
}

document.addEventListener("DOMContentLoaded", renderApp);
