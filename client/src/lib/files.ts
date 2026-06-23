export function assignFileToInput(input: HTMLInputElement, file: File): void {
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
  input.dispatchEvent(new Event("change", { bubbles: true }));
}

export function updateFileNameLabel(form: HTMLFormElement, input: HTMLInputElement): void {
  const nameEl = form.querySelector(".file-name");
  if (!(nameEl instanceof HTMLElement)) return;
  const f = input.files?.[0];
  nameEl.textContent = f ? `Wybrany plik: ${f.name}` : "";
}

export function isPdfFile(file: File): boolean {
  const n = file.name.toLowerCase();
  return file.type === "application/pdf" || n.endsWith(".pdf");
}

export function isDocxFile(file: File): boolean {
  const n = file.name.toLowerCase();
  if (n.endsWith(".docx")) return true;
  const t = (file.type || "").toLowerCase();
  return (
    t === "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ||
    (t === "application/octet-stream" && n.endsWith(".docx"))
  );
}

export function isMarkdownSourceFile(file: File): boolean {
  const n = file.name.toLowerCase();
  if (n.endsWith(".md") || n.endsWith(".markdown") || n.endsWith(".txt")) return true;
  const t = (file.type || "").toLowerCase();
  return (
    t === "text/markdown" ||
    t === "text/x-markdown" ||
    t === "text/plain" ||
    (t === "application/octet-stream" &&
      (n.endsWith(".md") || n.endsWith(".markdown") || n.endsWith(".txt")))
  );
}

export function isPlantumlSourceFile(file: File): boolean {
  const n = file.name.toLowerCase();
  if (
    n.endsWith(".puml") ||
    n.endsWith(".plantuml") ||
    n.endsWith(".pu") ||
    n.endsWith(".txt") ||
    n.endsWith(".iuml")
  ) {
    return true;
  }
  const t = (file.type || "").toLowerCase();
  if (t === "text/plain" || t === "text/x-puml") return true;
  return (
    t === "application/octet-stream" &&
    (n.endsWith(".puml") ||
      n.endsWith(".plantuml") ||
      n.endsWith(".pu") ||
      n.endsWith(".txt") ||
      n.endsWith(".iuml"))
  );
}

export function isMermaidSourceFile(file: File): boolean {
  const n = file.name.toLowerCase();
  if (n.endsWith(".mmd") || n.endsWith(".mermaid") || n.endsWith(".md") || n.endsWith(".txt")) return true;
  const t = (file.type || "").toLowerCase();
  return (
    t === "text/plain" ||
    t === "text/markdown" ||
    (t === "application/octet-stream" &&
      (n.endsWith(".mmd") || n.endsWith(".mermaid") || n.endsWith(".md") || n.endsWith(".txt")))
  );
}

export type DropzoneMode = "pdf" | "docx" | "any" | "markdownSource" | "plantumlSource" | "mermaidSource";

export function wireDropzone(
  form: HTMLFormElement,
  options: { mode: DropzoneMode; err: HTMLElement },
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

    if (options.mode === "pdf" && !isPdfFile(file)) {
      options.err.textContent = "Upuszczony plik musi być PDF.";
      return;
    }
    if (options.mode === "docx" && !isDocxFile(file)) {
      options.err.textContent = "Upuszczony plik musi być DOCX (.docx).";
      return;
    }
    if (options.mode === "markdownSource" && !isMarkdownSourceFile(file)) {
      options.err.textContent =
        "Dozwolone: .md, .markdown, .txt (lub typ text/markdown / text/plain).";
      return;
    }
    if (options.mode === "plantumlSource" && !isPlantumlSourceFile(file)) {
      options.err.textContent =
        "Dozwolone: .puml, .plantuml, .pu, .txt, .iuml (lub typ text/plain / text/x-puml).";
      return;
    }
    if (options.mode === "mermaidSource" && !isMermaidSourceFile(file)) {
      options.err.textContent =
        "Dozwolone: .mmd, .mermaid, .md, .txt (lub typ text/plain / text/markdown).";
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

export function parseContentDispositionFilename(cd: string | null): string | null {
  if (!cd) return null;
  const star = /filename\*=UTF-8''([^;]+)/i.exec(cd);
  if (star?.[1]) {
    try {
      const n = decodeURIComponent(star[1].trim());
      if (n) return n;
    } catch {
      /* ignore */
    }
  }
  const quoted = /filename="([^"]+)"/i.exec(cd);
  if (quoted?.[1]) return quoted[1].trim();
  const plain = /filename=([^;\s]+)/i.exec(cd);
  if (plain?.[1]) return plain[1].replace(/^"|"$/g, "").trim();
  return null;
}

export function downloadBlobAsFile(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
