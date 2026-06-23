import { readError } from "./http";

export async function checkHealth(): Promise<boolean> {
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
    elText.textContent = e instanceof Error ? e.message : "Błąd połączenia z API";
    return false;
  }
}

export function wireHealthButton(scope: ParentNode = document): void {
  scope.querySelector("#btn-health")?.addEventListener("click", () => {
    void checkHealth();
  });
}
