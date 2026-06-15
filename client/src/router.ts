import { renderDocxToMarkdownPage } from "./pages/docx-to-markdown";
import { renderHome } from "./pages/home";
import { renderMarkdownToDocxPage } from "./pages/markdown-to-docx";
import { cleanupMermaidPreview, renderMermaidPage } from "./pages/mermaid";
import { cleanupPlantumlPreview, renderPlantumlPage } from "./pages/plantuml";
import { renderPdfPage } from "./pages/pdf-to-text";
import { renderToMarkdownPage } from "./pages/to-markdown";
import { checkHealth } from "./lib/health";

const TITLES: Readonly<Record<string, string>> = {
  "/": "utils-service — klient WWW",
  "/pdf-to-text": "PDF → tekst — utils-service",
  "/to-markdown": "Plik → Markdown — utils-service",
  "/docx-to-markdown": "DOCX → Markdown — utils-service",
  "/markdown-to-docx": "Markdown → DOCX — utils-service",
  "/plantuml": "PlantUML — utils-service",
  "/mermaid": "Mermaid — utils-service",
};

function currentPath(): string {
  let h = window.location.hash.replace(/^#/, "").trim();
  if (h === "" || h === "/") return "/";
  if (!h.startsWith("/")) h = `/${h}`;
  return h;
}

function renderRoute(): void {
  const root = document.getElementById("app");
  if (!root) return;
  cleanupPlantumlPreview();
  cleanupMermaidPreview();
  const path = currentPath();
  document.title = TITLES[path] ?? TITLES["/"]!;

  switch (path) {
    case "/pdf-to-text":
      renderPdfPage(root);
      break;
    case "/to-markdown":
      renderToMarkdownPage(root);
      break;
    case "/docx-to-markdown":
      renderDocxToMarkdownPage(root);
      break;
    case "/markdown-to-docx":
      renderMarkdownToDocxPage(root);
      break;
    case "/plantuml":
      renderPlantumlPage(root);
      break;
    case "/mermaid":
      renderMermaidPage(root);
      break;
    case "/":
      renderHome(root);
      break;
    default:
      window.location.hash = "#/";
      return;
  }
  void checkHealth();
}

export function startRouter(): void {
  window.addEventListener("hashchange", () => renderRoute());
  if (!window.location.hash) {
    window.location.hash = "#/";
  }
  renderRoute();
}
