import { appShell } from "../layout";
import { readError } from "../lib/http";
import { downloadBlobAsFile, wireDropzone } from "../lib/files";
import { wireCopyButton, wireOutputCollapse } from "../lib/ui";
import { wireHealthButton } from "../lib/health";

type DocxMdResponse = {
  markdown: string;
  title?: string | null;
  media_count?: number;
  media_zip_base64?: string | null;
};

function wireDocxMdForm(scope: ParentNode): void {
  const form = scope.querySelector("#docx-md-form");
  const out = scope.querySelector("#docx-md-out");
  const meta = scope.querySelector("#docx-md-meta");
  const err = scope.querySelector("#docx-md-err");
  const zipBtn = scope.querySelector("#docx-md-zip");
  const mdBtn = scope.querySelector("#docx-md-download");
  if (!(form instanceof HTMLFormElement) || !(out instanceof HTMLTextAreaElement)) return;
  if (!(meta instanceof HTMLElement) || !(err instanceof HTMLElement)) return;
  if (!(zipBtn instanceof HTMLButtonElement) || !(mdBtn instanceof HTMLButtonElement)) return;

  wireDropzone(form, { mode: "docx", err });

  let lastZipBase64: string | null = null;
  let lastMdFilename = "document.md";

  const resetDownloads = (): void => {
    lastZipBase64 = null;
    zipBtn.hidden = true;
    mdBtn.hidden = true;
  };

  zipBtn.addEventListener("click", () => {
    if (!lastZipBase64) return;
    const binary = atob(lastZipBase64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    downloadBlobAsFile(new Blob([bytes], { type: "application/zip" }), "media.zip");
  });

  mdBtn.addEventListener("click", () => {
    downloadBlobAsFile(new Blob([out.value], { type: "text/markdown;charset=utf-8" }), lastMdFilename);
  });

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    err.textContent = "";
    out.value = "";
    meta.textContent = "";
    resetDownloads();

    const fd = new FormData(form);
    const file = fd.get("file");
    if (!(file instanceof File) || file.size === 0) {
      err.textContent = "Wybierz lub upuść plik DOCX.";
      return;
    }

    const comments = fd.get("comments") === "on";
    const extractMedia = fd.get("extract_media") === "on";
    const stem = file.name.replace(/\.docx$/i, "") || "document";
    lastMdFilename = `${stem}.md`;

    const body = new FormData();
    body.append("file", file);

    const params = new URLSearchParams({
      comments: String(comments),
      extract_media: String(extractMedia),
    });

    const btn = form.querySelector('button[type="submit"]');
    if (!(btn instanceof HTMLButtonElement)) return;
    btn.disabled = true;
    try {
      const res = await fetch(`/v1/docx-to-markdown?${params.toString()}`, { method: "POST", body });
      if (!res.ok) throw new Error(await readError(res));
      const data = (await res.json()) as DocxMdResponse;
      out.value = data.markdown ?? "";
      const titlePart =
        data.title != null && data.title !== "" ? `Tytuł: ${data.title}` : "Tytuł: (brak)";
      const mediaPart = `Obrazów: ${data.media_count ?? 0}`;
      meta.textContent = `${titlePart} · ${mediaPart}`;
      if (data.media_zip_base64) {
        lastZipBase64 = data.media_zip_base64;
        zipBtn.hidden = false;
      }
      if (out.value) mdBtn.hidden = false;
    } catch (e) {
      err.textContent = e instanceof Error ? e.message : String(e);
    } finally {
      btn.disabled = false;
    }
  });
}

function wireDocxMdOutputUi(scope: ParentNode): void {
  const copyBtn = scope.querySelector("#docx-md-copy");
  const toggleBtn = scope.querySelector("#docx-md-toggle-out");
  const block = scope.querySelector("#docx-md-output-block");
  const ta = scope.querySelector("#docx-md-out");
  const hint = scope.querySelector("#docx-md-clipboard-hint");
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

export function renderDocxToMarkdownPage(root: HTMLElement): void {
  root.innerHTML = appShell(
    "/docx-to-markdown",
    `
      <section class="card" aria-labelledby="docx-md-h">
        <h2 id="docx-md-h">DOCX → Markdown</h2>
        <p class="lead">Konwersja przez <strong>Pandoc</strong> (komentarze, track changes, opcjonalnie obrazy).</p>
        <form id="docx-md-form">
          <div class="file-area">
            <div
              class="dropzone"
              tabindex="0"
              role="region"
              aria-label="Strefa upuszczania pliku DOCX"
            >
              <span class="dropzone-text">Przeciągnij plik .docx lub wybierz poniżej.</span>
              <span class="file-name" aria-live="polite"></span>
            </div>
            <label>
              Plik DOCX
              <input
                type="file"
                name="file"
                accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                required
              />
            </label>
          </div>
          <div class="row">
            <label class="checkbox">
              <input type="checkbox" name="comments" checked />
              Komentarze i redakcja (usunięcia jako <code>~~</code>)
            </label>
            <label class="checkbox">
              <input type="checkbox" name="extract_media" />
              Wyciągnij obrazy (ZIP <code>media/</code>)
            </label>
          </div>
          <div class="row">
            <button type="submit">Konwertuj</button>
            <button type="button" class="secondary" id="docx-md-download" hidden>Pobierz .md</button>
            <button type="button" class="secondary" id="docx-md-zip" hidden>Pobierz media (ZIP)</button>
          </div>
          <p id="docx-md-meta" class="meta" aria-live="polite"></p>
          <div id="docx-md-output-block" class="output-block">
            <div class="output-toolbar">
              <button type="button" class="secondary" id="docx-md-copy">Kopiuj</button>
              <button
                type="button"
                class="secondary"
                id="docx-md-toggle-out"
                aria-expanded="true"
                aria-controls="docx-md-out"
              >
                Zwiń odpowiedź
              </button>
              <span id="docx-md-clipboard-hint" class="clipboard-hint" aria-live="polite"></span>
            </div>
            <textarea id="docx-md-out" readonly placeholder="Tu pojawi się Markdown…"></textarea>
          </div>
          <p id="docx-md-err" class="err" role="alert"></p>
        </form>
      </section>
    `,
  );
  wireHealthButton(root);
  wireDocxMdForm(root);
  wireDocxMdOutputUi(root);
}
