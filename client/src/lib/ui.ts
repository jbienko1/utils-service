export function wireCopyButton(
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

export function wireOutputCollapse(block: HTMLElement, toggle: HTMLButtonElement): void {
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
