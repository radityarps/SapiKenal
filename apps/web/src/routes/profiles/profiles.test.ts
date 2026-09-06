import { beforeEach, expect, it, vi } from 'vitest';

vi.mock('$lib/server/backend', () => ({
  backendJson: vi.fn().mockResolvedValue({ status: 'success' }),
  bearerHeaders: () => ({}),
  BackendRequestError: class extends Error {},
}));
vi.mock('$lib/server/admin', () => ({ adminLogout: vi.fn() }));

import { backendJson } from '$lib/server/backend';
import { actions } from './+page.server';

beforeEach(() => vi.clearAllMocks());

function event(fields: Record<string, string>) {
  return {
    request: new Request('http://localhost/profiles', {
      method: 'POST', body: new URLSearchParams(fields),
    }),
    locals: { sessionToken: 'test-only' },
    fetch: vi.fn(),
  } as unknown as Parameters<NonNullable<typeof actions.review>>[0];
}

it('requires explicit review confirmation before contacting the backend', async () => {
  const result = await actions.review!(event({ id: 'profile-1' }));
  expect(result).toMatchObject({ status: 422 });
  expect(backendJson).not.toHaveBeenCalled();
});

it('reviews saved content without resubmitting fields that reset review', async () => {
  await actions.review!(event({ id: 'profile-1', content_reviewed: 'true' }));
  expect(backendJson).toHaveBeenCalledWith('/api/admin/profiles/profile-1',
    expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ content_reviewed: true }) }),
    expect.any(Function));
});
