import { appShell } from "../layout";
import { readError } from "../lib/http";
import { wireDropzone } from "../lib/files";
import { wireCopyButton, wireOutputCollapse } from "../lib/ui";
import { wireHealthButton } from "../lib/health";

function wireMdForm(scope: ParentNode): void {
  const form = scope.querySelector("#md-form");
  const out = scope.querySelector("#md-out");
  const meta = scope.querySelector("#md-meta");
  const err = scope.querySelector("#md-err");
  if (!(form instanceof HTMLFormElement) || !(out instanceof HTMLTextAreaElement)) return;
  if (!(meta instanceof HTMLElement) || !(err instanceof HTMLElement)) return;

  wireDropzone(form, { mode: "any", err });

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    err.textContent = "";
    out.value = "";
    meta.textContent = "";

    const fd = new FormData(form);
    const file = fd.get("file");
    if (!(file instanceof File) || file.size === 0) {
      err.textContent = "Wybierz lub upuść plik.";
      return;
    }

    const body = new FormData();
    body.append("file", file);

    const btn = form.querySelector('button[type="submit"]');
    if (!(btn instanceof HTMLButtonElement)) return;
    btn.disabled = true;
    try {
      const res = await fetch("/v1/to-markdown", { method: "POST", body });
      if (!res.ok) throw new Error(await readError(res));
      const data = (await res.json()) as { markdown: string; title?: string | null };
      out.value = data.markdown ?? "";
      meta.textContent =
        data.title != null && data.title !== "" ? `Tytuł: ${data.title}` : "Tytuł: (brak)";
    } catch (e) {
      err.textContent = e instanceof Error ? e.message : String(e);
    } finally {
      btn.disabled = false;
    }
  });
}

function wireMdOutputUi(scope: ParentNode): void {
  const copyBtn = scope.querySelector("#md-copy");
  const toggleBtn = scope.querySelector("#md-toggle-out");
  const block = scope.querySelector("#md-output-block");
  const ta = scope.querySelector("#md-out");
  const hint = scope.querySelector("#md-clipboard-hint");
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

export function renderToMarkdownPage(root: HTMLElement): void {
  root.innerHTML = appShell(
    "/to-markdown",
    `
      <section class="card" aria-labelledby="md-h">
        <h2 id="md-h">Plik → Markdown</h2>
        <form id="md-form">
          <div class="file-area">
            <div
              class="dropzone"
              tabindex="0"
              role="region"
              aria-label="Strefa upuszczania pliku do konwersji"
            >
              <span class="dropzone-text">Przeciągnij plik tutaj lub wybierz poniżej.</span>
              <span class="file-name" aria-live="polite"></span>
            </div>
            <label>
              Plik
              <input type="file" name="file" required />
            </label>
          </div>
          <div class="row">
            <button type="submit">Konwertuj</button>
          </div>
          <p id="md-meta" class="meta"></p>
          <div id="md-output-block" class="output-block">
            <div class="output-toolbar">
              <button type="button" class="secondary" id="md-copy">Kopiuj</button>
              <button
                type="button"
                class="secondary"
                id="md-toggle-out"
                aria-expanded="true"
                aria-controls="md-out"
              >
                Zwiń odpowiedź
              </button>
              <span id="md-clipboard-hint" class="clipboard-hint" aria-live="polite"></span>
            </div>
            <textarea id="md-out" readonly placeholder="Tu pojawi się Markdown…"></textarea>
          </div>
          <p id="md-err" class="err" role="alert"></p>
        </form>
      </section>
    `,
  );
  wireHealthButton(root);
  wireMdForm(root);
  wireMdOutputUi(root);
}
