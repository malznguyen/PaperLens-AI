export function parsePaperIds(value: string): string[] {
  const seen = new Set<string>();
  const paperIds: string[] = [];

  for (const rawPart of value.split(",")) {
    const normalized = rawPart.trim();
    if (!normalized || seen.has(normalized)) {
      continue;
    }

    seen.add(normalized);
    paperIds.push(normalized);
  }

  return paperIds;
}
