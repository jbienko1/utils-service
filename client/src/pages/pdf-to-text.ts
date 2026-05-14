import { appShell } from "../layout";
import { readError } from "../lib/http";
import { isPdfFile, wireDropzone } from "../lib/files";
import { wireCopyButton, wireOutputCollapse } from "../lib/ui";
import { wireHealthButton } from "../lib/health";

function wirePdfForm(scope: ParentNode): void {
  const form = scope.querySelector("#pdf-form");
  const out = scope.querySelector("#pdf-out");
  const meta = scope.querySelector("#pdf-meta");
  const err = scope.querySelector("#pdf-err");
  if (!(form instanceof HTMLFormElement) || !(out instanceof HTMLTextAreaElement)) return;
  if (!(meta instanceof HTMLElement) || !(err instanceof HTMLElement)) return;

  wireDropzone(form, { mode: "pdf", err });

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    err.textContent = "";
    out.value = "";
    meta.textContent = "";

    const fd = new FormData(form);
    const file = fd.get("file");
    if (!(file instanceof File) || file.size === 0) {
      err.textContent = "Wybierz lub upuść plik PDF.";
      return;
    }
    if (!isPdfFile(file)) {
      err.textContent = "Wymagany plik PDF.";
      return;
    }

    const ocr = (fd.get("ocr") as string) || "off";
    const body = new FormData();
    body.append("file", file);

    const btn = form.querySelector('button[type="submit"]');
    if (!(btn instanceof HTMLButtonElement)) return;
    btn.disabled = true;
    try {
      const res = await fetch(`/v1/pdf-to-text?ocr=${encodeURIComponent(ocr)}`, {
        method: "POST",
        body,
      });
      if (!res.ok) throw new Error(await readError(res));
      const data = (await res.json()) as {
        text: string;
        page_count: number;
        used_ocr: boolean;
      };
      out.value = data.text ?? "";
      meta.textContent = `Stron: ${data.page_count ?? "?"} · OCR: ${data.used_ocr ? "tak" : "nie"}`;
    } catch (e) {
      err.textContent = e instanceof Error ? e.message : String(e);
    } finally {
      btn.disabled = false;
    }
  });
}

function wirePdfOutputUi(scope: ParentNode): void {
  const copyBtn = scope.querySelector("#pdf-copy");
  const toggleBtn = scope.querySelector("#pdf-toggle-out");
  const block = scope.querySelector("#pdf-output-block");
  const ta = scope.querySelector("#pdf-out");
  const hint = scope.querySelector("#pdf-clipboard-hint");
  if (
    copyBtn instanceof HTMLButtonElement &&
    toggleBtn instanceof HTMLButtonElement &&
    block instanceof HTMLElement &&
    ta instanceof HTMLTextAreaElement &&
    hint instanceof HTMLElement
  ) {
    wireCopyButton(copyBtn, ta, hint);
    wireOutputCollapse(block, toggleBtn);
  }
}

export function renderPdfPage(root: HTMLElement): void {
  root.innerHTML = appShell(
    "/pdf-to-text",
    `
      <section class="card" aria-labelledby="pdf-h">
        <h2 id="pdf-h">PDF → tekst</h2>
        <form id="pdf-form">
          <div class="file-area">
            <div
              class="dropzone"
              tabindex="0"
              role="region"
              aria-label="Strefa upuszczania pliku PDF"
            >
              <span class="dropzone-text">Przeciągnij plik PDF tutaj lub wybierz poniżej.</span>
              <span class="file-name" aria-live="polite"></span>
            </div>
            <label>
              Plik PDF
              <input type="file" name="file" accept="application/pdf,.pdf" required />
            </label>
          </div>
          <div class="row">
            <label>
              OCR
              <select name="ocr">
                <option value="off">wyłączone</option>
                <option value="auto">auto</option>
                <option value="on">włączone</option>
              </select>
            </label>
            <button type="submit">Wyślij</button>
          </div>
          <p id="pdf-meta" class="meta"></p>
          <div id="pdf-output-block" class="output-block">
            <div class="output-toolbar">
              <button type="button" class="secondary" id="pdf-copy">Kopiuj</button>
              <button
                type="button"
                class="secondary"
                id="pdf-toggle-out"
                aria-expanded="true"
                aria-controls="pdf-out"
              >
                Zwiń odpowiedź
              </button>
              <span id="pdf-clipboard-hint" class="clipboard-hint" aria-live="polite"></span>
            </div>
            <textarea id="pdf-out" readonly placeholder="Tu pojawi się wynik…"></textarea>
          </div>
          <p id="pdf-err" class="err" role="alert"></p>
        </form>
      </section>
    `,
  );
  wireHealthButton(root);
  wirePdfForm(root);
  wirePdfOutputUi(root);
}
