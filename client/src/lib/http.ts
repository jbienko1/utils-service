export async function readError(res: Response): Promise<string> {
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
