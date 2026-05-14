import "./style.css";

async function readError(res: Response): Promise<string> {
  let msg = `${res.status} ${res.statusText}`;
  try {
    const j: unknown = await res.json();
    if (j && typeof j === "object" && "detail" in j) {
      const d = (j as { detail: unknown }).detail;
      if (typeof d === "string") return d;
      return JSON.stringify(d);
    }
  } catch {
    /* ignore */
  }
  return msg;
}

function assignFileToInput(input: HTMLInputElement, file: File): void {
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
  input.dispatchEvent(new Event("change", { bubbles: true }));
}

function updateFileNameLabel(form: HTMLFormElement, input: HTMLInputElement): void {
  const nameEl = form.querySelector(".file-name");
  if (!(nameEl instanceof HTMLElement)) return;
  const f = input.files?.[0];
  nameEl.textContent = f ? `Wybrany plik: ${f.name}` : "";
}

function isPdfFile(file: File): boolean {
  const n = file.name.toLowerCase();
  return file.type === "application/pdf" || n.endsWith(".pdf");
}

function wireDropzone(
  form: HTMLFormElement,
  options: { pdfOnly: boolean; err: HTMLElement },
): void {
  const zone = form.querySelector(".file-area");
  const input = form.querySelector<HTMLInputElement>('input[type="file"][name="file"]');
  if (!(zone instanceof HTMLElement) || !input) return;

  const onDragEnter = (ev: DragEvent) => {
    ev.preventDefault();
    zone.classList.add("drag-active");
  };

  const onDragOver = (ev: DragEvent) => {
    ev.preventDefault();
    if (ev.dataTransfer) ev.dataTransfer.dropEffect = "copy";
  };

  const onDragLeave = (ev: DragEvent) => {
    ev.preventDefault();
    const rel = ev.relatedTarget;
    if (rel instanceof Node && zone.contains(rel)) return;
    zone.classList.remove("drag-active");
  };

  const onDrop = (ev: DragEvent) => {
    ev.preventDefault();
    zone.classList.remove("drag-active");
    const file = ev.dataTransfer?.files?.[0];
    if (!(file instanceof File)) return;

    if (options.pdfOnly && !isPdfFile(file)) {
      options.err.textContent = "Upuszczony plik musi być PDF.";
      return;
    }
    options.err.textContent = "";
    assignFileToInput(input, file);
    updateFileNameLabel(form, input);
  };

  zone.addEventListener("dragenter", onDragEnter);
  zone.addEventListener("dragover", onDragOver);
  zone.addEventListener("dragleave", onDragLeave);
  zone.addEventListener("drop", onDrop);

  input.addEventListener("change", () => {
    options.err.textContent = "";
    updateFileNameLabel(form, input);
  });
}

function wireCopyButton(
  button: HTMLButtonElement,
  textarea: HTMLTextAreaElement,
  hint: HTMLElement,
): void {
  const defaultLabel = button.textContent ?? "Kopiuj";

  button.addEventListener("click", async () => {
    hint.textContent = "";
    if (!textarea.value) {
      hint.textContent = "Brak treści do skopiowania.";
      return;
    }
    try {
      await navigator.clipboard.writeText(textarea.value);
      button.textContent = "Skopiowano";
      window.setTimeout(() => {
        button.textContent = defaultLabel;
      }, 1500);
    } catch {
      hint.textContent =
        "Schowek niedostępny (wymagany bezpieczny kontekst lub uprawnienia). Zaznacz tekst w polu i użyj Ctrl+C.";
    }
  });
}

function wireOutputCollapse(block: HTMLElement, toggle: HTMLButtonElement): void {
  const expandedLabel = "Zwiń odpowiedź";
  const collapsedLabel = "Pokaż odpowiedź";

  const sync = () => {
    const collapsed = block.classList.contains("is-collapsed");
    toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
    toggle.textContent = collapsed ? collapsedLabel : expandedLabel;
  };

  toggle.addEventListener("click", () => {
    block.classList.toggle("is-collapsed");
    sync();
  });

  sync();
}

async function checkHealth(): Promise<boolean> {
  const elDot = document.getElementById("health-dot");
  const elText = document.getElementById("health-text");
  if (!elDot || !elText) return false;
  elDot.classList.remove("ok", "err");
  elText.textContent = "Sprawdzanie…";
  try {
    const res = await fetch("/health");
    if (!res.ok) throw new Error(await readError(res));
    const data: unknown = await res.json();
    const ok =
      data &&
      typeof data === "object" &&
      "status" in data &&
      (data as { status: unknown }).status === "ok";
    if (!ok) throw new Error("Nieoczekiwana odpowiedź /health");
    elDot.classList.add("ok");
    elText.textContent = "API osiągalne (/health OK)";
    return true;
  } catch (e) {
    elDot.classList.add("err");
    elText.textContent =
      e instanceof Error ? e.message : "Błąd połączenia z API";
    return false;
  }
}

function wirePdfForm(): void {
  const form = document.getElementById("pdf-form") as HTMLFormElement | null;
  const out = document.getElementById("pdf-out") as HTMLTextAreaElement | null;
  const meta = document.getElementById("pdf-meta") as HTMLElement | null;
  const err = document.getElementById("pdf-err") as HTMLElement | null;
  if (!form || !out || !meta || !err) return;

  wireDropzone(form, { pdfOnly: true, err });

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

    const btn = form.querySelector('button[type="submit"]') as HTMLButtonElement;
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

function wireMdForm(): void {
  const form = document.getElementById("md-form") as HTMLFormElement | null;
  const out = document.getElementById("md-out") as HTMLTextAreaElement | null;
  const meta = document.getElementById("md-meta") as HTMLElement | null;
  const err = document.getElementById("md-err") as HTMLElement | null;
  if (!form || !out || !meta || !err) return;

  wireDropzone(form, { pdfOnly: false, err });

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

    const btn = form.querySelector('button[type="submit"]') as HTMLButtonElement;
    btn.disabled = true;
    try {
      const res = await fetch("/v1/to-markdown", { method: "POST", body });
      if (!res.ok) throw new Error(await readError(res));
      const data = (await res.json()) as { markdown: string; title?: string | null };
      out.value = data.markdown ?? "";
      meta.textContent =
        data.title != null && data.title !== ""
          ? `Tytuł: ${data.title}`
          : "Tytuł: (brak)";
    } catch (e) {
      err.textContent = e instanceof Error ? e.message : String(e);
    } finally {
      btn.disabled = false;
    }
  });
}

function wireOutputUi(): void {
  const pairs: Array<{ copy: string; toggle: string; block: string; ta: string; hint: string }> = [
    {
      copy: "pdf-copy",
      toggle: "pdf-toggle-out",
      block: "pdf-output-block",
      ta: "pdf-out",
      hint: "pdf-clipboard-hint",
    },
    {
      copy: "md-copy",
      toggle: "md-toggle-out",
      block: "md-output-block",
      ta: "md-out",
      hint: "md-clipboard-hint",
    },
  ];

  for (const p of pairs) {
    const copyBtn = document.getElementById(p.copy);
    const toggleBtn = document.getElementById(p.toggle);
    const block = document.getElementById(p.block);
    const ta = document.getElementById(p.ta);
    const hint = document.getElementById(p.hint);
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
}

function render(): void {
  const root = document.getElementById("app");
  if (!root) return;
  root.innerHTML = `
    <div class="wrap">
      <header>
        <h1>utils-service — klient WWW</h1>
        <p>Prosty interfejs do usług PDF → tekst oraz plik → Markdown.</p>
        <div class="status">
          <span id="health-dot" class="dot" aria-hidden="true"></span>
          <span id="health-text">Nie sprawdzono</span>
        </div>
        <div style="margin-top:0.6rem">
          <button type="button" class="secondary" id="btn-health">Sprawdź /health</button>
        </div>
      </header>

      <section class="card" aria-labelledby="pdf-h">
        <h2 id="pdf-h">PDF → tekst</h2>
        <form id="pdf-form">
          <div class="file-area">
            <div
              id="pdf-dropzone"
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

      <section class="card" aria-labelledby="md-h">
        <h2 id="md-h">Plik → Markdown</h2>
        <form id="md-form">
          <div class="file-area">
            <div
              id="md-dropzone"
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

      <footer>
        W trybie <code>npm run dev</code> żądania idą przez proxy Vite na backend (domyślnie
        <code>http://127.0.0.1:8000</code>). Zobacz <code>client/README.md</code>.
      </footer>
    </div>
  `;

  document.getElementById("btn-health")?.addEventListener("click", () => {
    void checkHealth();
  });
  wirePdfForm();
  wireMdForm();
  wireOutputUi();
}

render();
void checkHealth();
