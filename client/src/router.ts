import { renderHome } from "./pages/home";
import { renderMarkdownToDocxPage } from "./pages/markdown-to-docx";
import { renderPdfPage } from "./pages/pdf-to-text";
import { renderToMarkdownPage } from "./pages/to-markdown";
import { checkHealth } from "./lib/health";

const TITLES: Readonly<Record<string, string>> = {
  "/": "utils-service — klient WWW",
  "/pdf-to-text": "PDF → tekst — utils-service",
  "/to-markdown": "Plik → Markdown — utils-service",
  "/markdown-to-docx": "Markdown → DOCX — utils-service",
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
  const path = currentPath();
  document.title = TITLES[path] ?? TITLES["/"]!;

  switch (path) {
    case "/pdf-to-text":
      renderPdfPage(root);
      break;
    case "/to-markdown":
      renderToMarkdownPage(root);
      break;
    case "/markdown-to-docx":
      renderMarkdownToDocxPage(root);
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
