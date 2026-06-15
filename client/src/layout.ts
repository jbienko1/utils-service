const NAV: ReadonlyArray<{ path: string; href: string; label: string }> = [
  { path: "/", href: "#/", label: "Start" },
  { path: "/pdf-to-text", href: "#/pdf-to-text", label: "PDF → tekst" },
  { path: "/to-markdown", href: "#/to-markdown", label: "Plik → Markdown" },
  { path: "/docx-to-markdown", href: "#/docx-to-markdown", label: "DOCX → Markdown" },
  { path: "/markdown-to-docx", href: "#/markdown-to-docx", label: "Markdown → DOCX" },
  { path: "/plantuml", href: "#/plantuml", label: "PlantUML" },
  { path: "/mermaid", href: "#/mermaid", label: "Mermaid" },
];

function navHtml(activePath: string): string {
  const links = NAV.map(
    (item) =>
      `<a href="${item.href}" class="nav-link${activePath === item.path ? " nav-link-active" : ""}">${item.label}</a>`,
  ).join("");
  return `<nav class="app-nav" aria-label="Nawigacja główna">${links}</nav>`;
}

export function appShell(activePath: string, mainHtml: string): string {
  return `
    <div class="wrap">
      <header>
        <h1>utils-service — klient WWW</h1>
        <p>Prosty interfejs do usług REST (PDF, Markdown, DOCX, PlantUML, Mermaid).</p>
        <div class="status">
          <span id="health-dot" class="dot" aria-hidden="true"></span>
          <span id="health-text">Nie sprawdzono</span>
        </div>
        <div style="margin-top:0.6rem">
          <button type="button" class="secondary" id="btn-health">Sprawdź /health</button>
        </div>
      </header>
      ${navHtml(activePath)}
      <main class="app-main">
        ${mainHtml}
      </main>
      <footer>
        W trybie <code>npm run dev</code> żądania idą przez proxy Vite na backend (domyślnie
        <code>http://127.0.0.1:8000</code>). Zobacz <code>client/README.md</code>.
      </footer>
    </div>
  `;
}
