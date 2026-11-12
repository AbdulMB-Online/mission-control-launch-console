import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import App from './App';

const fetchMock = vi.fn();
beforeEach(() => vi.stubGlobal('fetch', fetchMock));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); fetchMock.mockReset(); });

it('shows the console identity, backend readiness and honest simulated mode', async () => {
  fetchMock.mockResolvedValue({ ok: true, json: async () => ({ status: 'ok', service: 'mission-control', provider: 'fake' }) });
  render(<App />);
  expect(screen.getByRole('heading', { name: 'Mission Control' })).toBeTruthy();
  expect(await screen.findByText('System online')).toBeTruthy();
  expect(screen.getByText('Simulated mode')).toBeTruthy();
  expect(screen.getByText('Report filing is the next milestone.')).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledWith('/healthz', expect.objectContaining({ signal: expect.any(AbortSignal) }));
});

it('makes a failed connection visible and lets the user retry', async () => {
  fetchMock.mockRejectedValueOnce(new Error('unavailable'));
  render(<App />);
  expect(await screen.findByText('Connection unavailable')).toBeTruthy();
  fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'ok', service: 'mission-control', provider: 'fake' }) });
  fireEvent.click(screen.getByRole('button', { name: 'Retry connection' }));
  expect(await screen.findByText('System online')).toBeTruthy();
});

it('does not report an unhealthy backend as online', async () => {
  fetchMock.mockResolvedValue({ ok: false, json: async () => ({ status: 'unavailable' }) });
  render(<App />);
  expect(await screen.findByText('Connection unavailable')).toBeTruthy();
  expect(screen.queryByText('System online')).toBeNull();
});

it('lets the operator refresh a healthy connection without losing the reporting workspace', async () => {
  fetchMock.mockResolvedValue({ ok: true, json: async () => ({ status: 'ok', service: 'mission-control', provider: 'fake' }) });
  render(<App />);
  expect(await screen.findByText('System online')).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'Refresh connection' }));
  expect(await screen.findByText('System online')).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(screen.getByRole('region', { name: 'Report workspace' })).toBeTruthy();
  expect(screen.getByText('Not assessed')).toBeTruthy();
});

it('never presents a launch clearance or invented readings when the connection fails', async () => {
  fetchMock.mockRejectedValue(new Error('unavailable'));
  render(<App />);
  expect(await screen.findByText('Connection unavailable')).toBeTruthy();
  expect(screen.getByText('Not assessed')).toBeTruthy();
  expect(screen.getByText('Awaiting readings')).toBeTruthy();
  expect(screen.queryByText('GO')).toBeNull();
});
