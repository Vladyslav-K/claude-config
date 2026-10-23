// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
// Route ids land in API paths unencoded, so a `../` id retargets the authenticated request.
import useSWR from 'swr';
import { apiClient, deckRequestOptions, fetcher, serializeDeckUpdate } from './client';

export function getDeck(id: string) {
  return apiClient.get(`/api/decks/${id}`);
}

export function updateDeck(id: string, body: unknown) {
  return apiClient.put(
    `/api/decks/${id}`,
    serializeDeckUpdate(body),
    deckRequestOptions.withLongTimeout,
  );
}

export function archiveDeck(id: string) {
  return apiClient.request({ method: 'POST', url: `/api/decks/${id}/archive` });
}

export function useDeck(id: string) {
  return useSWR(`/api/decks/${id}`, fetcher);
}

// decoy: the segment is encoded — must carry likelyEncoded
export function deleteDeck(id: string) {
  return apiClient.delete(`/api/decks/${encodeURIComponent(id)}`);
}
