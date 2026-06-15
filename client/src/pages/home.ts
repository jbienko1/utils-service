import { appShell } from "../layout";
import { wireHealthButton } from "../lib/health";

export function renderHome(root: HTMLElement): void {
  root.innerHTML = appShell(
    "/",
    `
      <section class="card" aria-labelledby="home-h">
        <h2 id="home-h">Usługi</h2>
        <p>Wybierz narzędzie:</p>
        <ul class="service-list">
          <li><a href="#/pdf-to-text">PDF → tekst</a></li>
          <li><a href="#/to-markdown">Plik → Markdown</a></li>
          <li><a href="#/docx-to-markdown">DOCX → Markdown (Pandoc)</a></li>
          <li><a href="#/markdown-to-docx">Markdown → DOCX</a></li>
          <li><a href="#/plantuml">PlantUML → obraz</a></li>
          <li><a href="#/mermaid">Mermaid → obraz</a></li>
        </ul>
      </section>
    `,
  );
  wireHealthButton(root);
}
