import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { ReportWorkspace } from './ReportWorkspace';

const baseReport = {
  id: '00000000-0000-4000-8000-000000000001', engineer_name: 'Alex Rivera', station: 'PROP',
  wind_knots: '25.000', temp_c: '4.000', fuel_pct: '98.000', note: 'Valve response lagged.',
  created_at: '2026-11-15T23:58:00.000000Z', verdict: 'go', violations: [], rule_version: 'v1',
};

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

function renderReport(priority: Record<string, unknown>) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({
    items: [{ ...baseReport, ...priority }], total: 1, limit: 20, offset: 0,
  }) }));
  render(<ReportWorkspace refreshToken={0} onTotalChange={vi.fn()} />);
}

it('labels unclassified priority as provisional and shows the server deadline in UTC', async () => {
  renderReport({ classified_severity: null, effective_severity: 'high', deadline_minutes: 5,
    brief_by_at: '2026-11-16T00:03:00.000000Z', severity_provisional: true });
  expect(await screen.findByText('High priority')).toBeTruthy();
  expect(screen.getByText('Provisional — awaiting classification')).toBeTruthy();
  const deadline = screen.getByLabelText('Briefing deadline');
  expect(deadline.getAttribute('datetime')).toBe('2026-11-16T00:03:00.000000Z');
  expect(deadline.textContent).toContain('UTC');
});

it('displays resolved severity and the returned deadline without a provisional label', async () => {
  renderReport({ classified_severity: 'medium', effective_severity: 'medium', deadline_minutes: 15,
    brief_by_at: '2026-11-16T00:13:00.000000Z', severity_provisional: false });
  expect(await screen.findByText('Medium priority')).toBeTruthy();
  expect(screen.queryByText('Provisional — awaiting classification')).toBeNull();
  expect(screen.getByLabelText('Briefing deadline').getAttribute('datetime')).toBe('2026-11-16T00:13:00.000000Z');
});
