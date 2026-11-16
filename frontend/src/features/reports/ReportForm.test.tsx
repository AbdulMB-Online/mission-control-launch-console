import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import App from '../../app/App';

const payload = {
  engineer_name: 'Alex Rivera', station: 'PROP', wind_knots: '25.000',
  temp_c: '4.000', fuel_pct: '98.000', note: 'Valve response lagged during the final check.',
};
const saved = {
  ...payload, id: '00000000-0000-4000-8000-000000000001', created_at: '2026-11-12T12:00:00Z',
  classified_severity: null, effective_severity: 'high', deadline_minutes: 5,
  brief_by_at: '2026-11-12T12:05:00.000000Z', severity_provisional: true,
  requires_review: false, review_reasons: [], checks: [],
};
const postMock = vi.fn();
const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockImplementation((url: string, init?: RequestInit) => {
    if (url === '/healthz') return Promise.resolve({ ok: true, json: async () => ({ status: 'ok', service: 'mission-control', provider: 'fake' }) });
    if (url === '/api/v1/reports' && init?.method === 'POST') return postMock(init);
    if (url.startsWith('/api/v1/reports')) return Promise.resolve({ ok: true, json: async () => ({ items: [], total: 0, limit: 20, offset: 0 }) });
    throw new Error(`Unexpected API path: ${url}`);
  });
  vi.stubGlobal('fetch', fetchMock);
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); fetchMock.mockReset(); postMock.mockReset(); });

async function fillReport(station = 'PROP') {
  await screen.findByText('System online');
  fireEvent.click(screen.getByRole('button', { name: 'File report' }));
  for (const [label, value] of [
    ['Engineer name', payload.engineer_name], ['Station', station],
    ['Wind (knots)', payload.wind_knots], ['Temperature (°C)', payload.temp_c],
    ['Fuel (%)', payload.fuel_pct], ['Anomaly note', payload.note],
  ]) fireEvent.change(screen.getByLabelText(label), { target: { value } });
}

it('files all six fields without converting exact readings into numbers', async () => {
  postMock.mockResolvedValue({ ok: true, status: 201, json: async () => saved });
  render(<App />);
  await fillReport();
  fireEvent.click(screen.getByRole('button', { name: 'Submit report' }));
  expect(await screen.findByText('Report filed')).toBeTruthy();
  expect(postMock).toHaveBeenCalledTimes(1);
  expect(JSON.parse(postMock.mock.calls[0][0].body)).toEqual(payload);
});

it('shows field errors and preserves the entered report for correction', async () => {
  postMock.mockResolvedValue({ ok: false, status: 422, json: async () => ({ error: {
    code: 'validation_error', message: 'Check the highlighted fields.', fields: [{ field: 'station', message: 'Station is required.' }],
  } }) });
  render(<App />);
  await fillReport('   ');
  fireEvent.click(screen.getByRole('button', { name: 'Submit report' }));
  expect(await screen.findByText('Station is required.')).toBeTruthy();
  expect((screen.getByLabelText('Engineer name') as HTMLInputElement).value).toBe(payload.engineer_name);
  expect((screen.getByLabelText('Anomaly note') as HTMLTextAreaElement).value).toBe(payload.note);
  expect(screen.queryByText('Report filed')).toBeNull();
});

it('keeps the report available for retry after a network failure', async () => {
  postMock.mockRejectedValueOnce(new Error('network unavailable'));
  render(<App />);
  await fillReport();
  fireEvent.click(screen.getByRole('button', { name: 'Submit report' }));
  expect(await screen.findByText('Could not file the report. Your entries are saved here; try again.')).toBeTruthy();
  expect((screen.getByLabelText('Wind (knots)') as HTMLInputElement).value).toBe('25.000');
  postMock.mockResolvedValueOnce({ ok: true, status: 201, json: async () => saved });
  fireEvent.click(screen.getByRole('button', { name: 'Submit report' }));
  expect(await screen.findByText('Report filed')).toBeTruthy();
});

it('prevents a second submission while the first request is pending', async () => {
  let finish!: (value: unknown) => void;
  postMock.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  render(<App />);
  await fillReport();
  const submit = screen.getByRole('button', { name: 'Submit report' });
  fireEvent.click(submit);
  await waitFor(() => expect(submit.hasAttribute('disabled')).toBe(true));
  fireEvent.click(submit);
  expect(postMock).toHaveBeenCalledTimes(1);
  finish({ ok: true, status: 201, json: async () => saved });
  expect(await screen.findByText('Report filed')).toBeTruthy();
});
