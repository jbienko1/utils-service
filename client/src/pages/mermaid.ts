import { appShell } from "../layout";
import { readError } from "../lib/http";
import { wireDropzone } from "../lib/files";
import { wireHealthButton } from "../lib/health";

const DEFAULT_SRC = `graph TD
  A[Klient] --> B[API]
  B --> C[Mermaid]
`;

let lastPreviewUrl: string | null = null;

function revokePreview(): void {
  if (lastPreviewUrl) {
    URL.revokeObjectURL(lastPreviewUrl);
    lastPreviewUrl = null;
  }
}

export function cleanupMermaidPreview(): void {
  revokePreview();
}

export function renderMermaidPage(root: HTMLElement): void {
  revokePreview();
  root.innerHTML = appShell(
    "/mermaid",
    `
      <section class="card" aria-labelledby="mer-h">
        <h2 id="mer-h">Mermaid → obraz</h2>
        <p class="lead">
          Wymaga <strong>Node</strong> oraz <code>mmdc</code> (katalog <code>mermaid-cli/</code> w repo lub globalny).
          Przeglądarkę podaje serwer: <code>UTILS_PUPPETEER_EXECUTABLE_PATH</code> (Chrome/Chromium).
          Możesz wkleić źródło w polu poniżej albo przeciągnąć plik .mmd / .md / .txt na strefę.
        </p>
        <form id="mer-form">
          <label>
            Źródło Mermaid
            <textarea id="mer-src" class="textarea-puml" spellcheck="false">${DEFAULT_SRC.trim()}</textarea>
          </label>
          <div class="file-area" style="margin-top:0.5rem">
            <div
              class="dropzone"
              tabindex="0"
              role="region"
              aria-label="Strefa upuszczania pliku Mermaid lub tekstu"
            >
              <span class="dropzone-text">Przeciągnij plik .mmd / .md / .txt lub wybierz poniżej.</span>
              <span class="file-name" aria-live="polite"></span>
            </div>
            <label>
              Opcjonalnie: plik źródłowy
              <input
                type="file"
                name="file"
                accept=".mmd,.mermaid,.md,.txt,text/plain,text/markdown"
              />
            </label>
          </div>
          <div class="row">
            <label>
              Format
              <select name="format" id="mer-format">
                <option value="svg">SVG</option>
                <option value="png">PNG</option>
              </select>
            </label>
            <button type="submit">Generuj podgląd</button>
          </div>
          <div id="mer-preview-wrap" class="puml-preview-wrap" hidden>
            <p class="meta">Podgląd:</p>
            <img id="mer-preview" class="diagram-preview" alt="Wynik Mermaid" />
          </div>
          <p id="mer-err" class="err" role="alert"></p>
        </form>
      </section>
    `,
  );
  wireHealthButton(root);

  const form = root.querySelector("#mer-form");
  const ta = root.querySelector("#mer-src");
  const fileIn = root.querySelector<HTMLInputElement>('#mer-form input[type="file"][name="file"]');
  const fmt = root.querySelector("#mer-format");
  const err = root.querySelector("#mer-err");
  const wrap = root.querySelector("#mer-preview-wrap");
  const img = root.querySelector("#mer-preview");

  if (
    !(form instanceof HTMLFormElement) ||
    !(ta instanceof HTMLTextAreaElement) ||
    !(fileIn instanceof HTMLInputElement) ||
    !(fmt instanceof HTMLSelectElement) ||
    !(err instanceof HTMLElement) ||
    !(wrap instanceof HTMLElement) ||
    !(img instanceof HTMLImageElement)
  ) {
    return;
  }

  wireDropzone(form, { mode: "mermaidSource", err });

  fileIn.addEventListener("change", () => {
    const f = fileIn.files?.[0];
    if (!f) return;
    void f.text().then((text) => {
      ta.value = text;
    });
  });

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    err.textContent = "";
    wrap.hidden = true;
    revokePreview();
    img.removeAttribute("src");

    const body = new FormData();
    const chosen = fileIn.files?.[0];
    if (chosen && chosen.size > 0) {
      body.append("file", chosen);
    } else {
      const blob = new Blob([ta.value], { type: "text/plain" });
      body.append("file", blob, "diagram.mmd");
    }

    const btn = form.querySelector('button[type="submit"]');
    if (!(btn instanceof HTMLButtonElement)) return;
    btn.disabled = true;
    try {
      const q = encodeURIComponent(fmt.value);
      const res = await fetch(`/v1/mermaid-to-image?format=${q}`, { method: "POST", body });
      if (!res.ok) throw new Error(await readError(res));
      const outBlob = await res.blob();
      lastPreviewUrl = URL.createObjectURL(outBlob);
      img.src = lastPreviewUrl;
      wrap.hidden = false;
    } catch (e) {
      err.textContent = e instanceof Error ? e.message : String(e);
    } finally {
      btn.disabled = false;
    }
  });
}
