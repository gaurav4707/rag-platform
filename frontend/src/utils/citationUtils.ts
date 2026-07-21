import type { Source } from "../types";

export interface CitationViewModel {
  filename: string;
  page: number | null;
  score: number | null;
  documentId: string;
}

export function deduplicateSources(sources: Source[]): Source[] {
  const seen = new Set<string>();
  return sources.filter((s) => {
    const key = `${s.document_id}:${s.page ?? "none"}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function mapToCitationViewModel(source: Source): CitationViewModel {
  return {
    filename: source.document,
    page: source.page,
    score: source.score,
    documentId: source.document_id,
  };
}

export function formatCitationText(vm: CitationViewModel): string {
  const base = `Source: ${vm.filename}`;
  if (vm.page != null) return `${base} (p. ${vm.page})`;
  return base;
}

export function formatPageRef(page: number | null): string | null {
  if (page == null) return null;
  return `Page ${page}`;
}

export function formatScore(score: number | null): string | null {
  if (score == null) return null;
  return `${(score * 100).toFixed(1)}%`;
}

export async function copyCitation(vm: CitationViewModel): Promise<string> {
  const text = formatCitationText(vm);
  await navigator.clipboard.writeText(text);
  return text;
}

export async function copyDocument(vm: CitationViewModel): Promise<string> {
  await navigator.clipboard.writeText(vm.filename);
  return vm.filename;
}

export async function copyPage(vm: CitationViewModel): Promise<string> {
  const text = `Page ${vm.page}`;
  await navigator.clipboard.writeText(text);
  return text;
}
