import { appShell } from "../layout";
import { readError } from "../lib/http";
import { wireHealthButton } from "../lib/health";

const DEFAULT_SRC = `@startuml
Alice -> Bob: Cześć
Bob --> Alice: OK
@enduml
`;

let lastPreviewUrl: string | null = null;

function revokePreview(): void {
  if (lastPreviewUrl) {
    URL.revokeObjectURL(lastPreviewUrl);
    lastPreviewUrl = null;
  }
}

/** Wywołaj przy zmianie trasy, żeby zwolnić blob URL podglądu. */
export function cleanupPlantumlPreview(): void {
  revokePreview();
}

export function renderPlantumlPage(root: HTMLElement): void {
  revokePreview();
  root.innerHTML = appShell(
    "/plantuml",
    `
      <section class="card" aria-labelledby="puml-h">
        <h2 id="puml-h">PlantUML → obraz</h2>
        <p class="lead">
          Wymaga <strong>plantuml</strong> i <strong>Graphviz (dot)</strong> po stronie API (w Dockerze jest w obrazie).
        </p>
        <form id="puml-form">
          <label>
            Źródło PlantUML
            <textarea id="puml-src" class="textarea-puml" spellcheck="false">${DEFAULT_SRC.trim()}</textarea>
          </label>
          <div class="file-area" style="margin-top:0.5rem">
            <label>
              Opcjonalnie: wgraj plik .puml / .txt
              <input type="file" id="puml-file" accept=".puml,.plantuml,.pu,.txt,.iuml,text/plain" />
            </label>
          </div>
          <div class="row">
            <label>
              Format
              <select name="format" id="puml-format">
                <option value="svg">SVG</option>
                <option value="png">PNG</option>
              </select>
            </label>
            <button type="submit">Generuj podgląd</button>
          </div>
          <div id="puml-preview-wrap" class="puml-preview-wrap" hidden>
            <p class="meta">Podgląd:</p>
            <img id="puml-preview" class="diagram-preview" alt="Wynik PlantUML" />
          </div>
          <p id="puml-err" class="err" role="alert"></p>
        </form>
      </section>
    `,
  );
  wireHealthButton(root);

  const form = root.querySelector("#puml-form");
  const ta = root.querySelector("#puml-src");
  const fileIn = root.querySelector("#puml-file");
  const fmt = root.querySelector("#puml-format");
  const err = root.querySelector("#puml-err");
  const wrap = root.querySelector("#puml-preview-wrap");
  const img = root.querySelector("#puml-preview");

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
    const blob = new Blob([ta.value], { type: "text/plain" });
    body.append("file", blob, "diagram.puml");

    const btn = form.querySelector('button[type="submit"]');
    if (!(btn instanceof HTMLButtonElement)) return;
    btn.disabled = true;
    try {
      const q = encodeURIComponent(fmt.value);
      const res = await fetch(`/v1/plantuml-to-image?format=${q}`, { method: "POST", body });
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
