import { appShell } from "../layout";
import { readError } from "../lib/http";
import {
  downloadBlobAsFile,
  isMarkdownSourceFile,
  parseContentDispositionFilename,
  wireDropzone,
} from "../lib/files";
import { wireHealthButton } from "../lib/health";

function wireDocxForm(scope: ParentNode): void {
  const form = scope.querySelector("#docx-form");
  const err = scope.querySelector("#docx-err");
  const meta = scope.querySelector("#docx-meta");
  if (!(form instanceof HTMLFormElement) || !(err instanceof HTMLElement)) return;
  if (!(meta instanceof HTMLElement)) return;

  wireDropzone(form, { mode: "markdownSource", err });

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    err.textContent = "";
    meta.textContent = "";

    const fd = new FormData(form);
    const file = fd.get("file");
    if (!(file instanceof File) || file.size === 0) {
      err.textContent = "Wybierz lub upuść plik źródłowy.";
      return;
    }
    if (!isMarkdownSourceFile(file)) {
      err.textContent =
        "Dozwolone: .md, .markdown, .txt (lub typ text/markdown / text/plain).";
      return;
    }

    const body = new FormData();
    body.append("file", file);

    const btn = form.querySelector('button[type="submit"]');
    if (!(btn instanceof HTMLButtonElement)) return;
    btn.disabled = true;
    try {
      const res = await fetch("/v1/markdown-to-docx", { method: "POST", body });
      if (!res.ok) throw new Error(await readError(res));
      const blob = await res.blob();
      const fromHeader =
        parseContentDispositionFilename(res.headers.get("Content-Disposition")) ??
        `${file.name.replace(/\.[^.]+$/, "") || "document"}.docx`;
      downloadBlobAsFile(blob, fromHeader);
      meta.textContent = `Pobrano: ${fromHeader}`;
    } catch (e) {
      err.textContent = e instanceof Error ? e.message : String(e);
    } finally {
      btn.disabled = false;
    }
  });
}

export function renderMarkdownToDocxPage(root: HTMLElement): void {
  root.innerHTML = appShell(
    "/markdown-to-docx",
    `
      <section class="card" aria-labelledby="docx-h">
        <h2 id="docx-h">Markdown → DOCX</h2>
        <p class="lead">Wymaga <strong>Pandoc</strong> po stronie API (lokalnie w PATH lub w obrazie Docker).</p>
        <form id="docx-form">
          <div class="file-area">
            <div
              class="dropzone"
              tabindex="0"
              role="region"
              aria-label="Strefa upuszczania pliku Markdown lub tekstu"
            >
              <span class="dropzone-text">Przeciągnij plik .md / .txt lub wybierz poniżej.</span>
              <span class="file-name" aria-live="polite"></span>
            </div>
            <label>
              Plik Markdown lub tekst
              <input
                type="file"
                name="file"
                accept=".md,.markdown,.txt,text/markdown,text/plain"
                required
              />
            </label>
          </div>
          <div class="row">
            <button type="submit">Konwertuj i pobierz DOCX</button>
          </div>
          <p id="docx-meta" class="meta" aria-live="polite"></p>
          <p id="docx-err" class="err" role="alert"></p>
        </form>
      </section>
    `,
  );
  wireHealthButton(root);
  wireDocxForm(root);
}
