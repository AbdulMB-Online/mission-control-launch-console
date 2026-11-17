import { cleanup, render, screen, within } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { ReportWorkspace } from './ReportWorkspace';

const report = {
  id: '00000000-0000-4000-8000-000000000001', engineer_name: 'Alex Rivera', station: 'PROP',
  wind_knots: '25.001', temp_c: '4.000', fuel_pct: '98.000', note: 'Valve response lagged.',
  created_at: '2026-11-15T23:58:00.000000Z', verdict: 'no_go',
  violations: [{ field: 'wind_knots', observed: '25.001', operator: '<=', limit: '25', message: 'Wind must be at most 25 knots.' }], rule_version: 'v1',
  classified_severity: 'low', effective_severity: 'high', deadline_minutes: 5,
  brief_by_at: '2026-11-16T00:03:00.000000Z', severity_provisional: false,
  requires_review: true, review_reasons: ['injection_flagged'],
  subsystem: 'propulsion', classification_status: 'completed', classification_rationale: 'Valve anomaly.',
  pipeline_status: 'processing', error_code: null, briefings: [], selected_briefing_id: null,
  approval_state: 'unavailable', approval: null,
};
type CheckFixture = { kind: string; status: string; flagged: boolean | null; details: Record<string, unknown>; error_code: string | null };
const cleanChecks: CheckFixture[] = [
  { kind: 'injection', status: 'completed', flagged: false, details: { reasons: [] }, error_code: null },
  { kind: 'missing_information', status: 'completed', flagged: false, details: { missing_details: [] }, error_code: null },
  { kind: 'tone', status: 'completed', flagged: false, details: { tone: 'calm', rationale: 'Factual tone.' }, error_code: null },
];

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

function renderChecks(checks: CheckFixture[]) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({
    items: [{ ...report, checks }], total: 1, limit: 20, offset: 0,
  }) }));
  render(<ReportWorkspace refreshToken={0} onTotalChange={vi.fn()} />);
}

it('prominently shows human review and all three advisory results', async () => {
  renderChecks([
    { ...cleanChecks[0], flagged: true, details: { reasons: ['Embedded instruction.'] } },
    cleanChecks[1], { ...cleanChecks[2], flagged: true, details: { tone: 'panic', rationale: 'Panic language.' } },
  ]);
  expect(await screen.findByRole('alert')).toHaveProperty('textContent', expect.stringContaining('Human review required'));
  expect(within(screen.getByRole('group', { name: 'Hidden instructions' })).getByText('Flagged')).toBeTruthy();
  expect(within(screen.getByRole('group', { name: 'Missing information' })).getByText('Clear')).toBeTruthy();
  expect(within(screen.getByRole('group', { name: 'Report tone' })).getByText('Panic')).toBeTruthy();
  expect(screen.getByText('Embedded instruction.')).toBeTruthy();
});

it('shows an unknown check as unavailable and preserves completed siblings', async () => {
  renderChecks([
    { ...cleanChecks[0], status: 'error', flagged: null, details: {}, error_code: 'timeout' },
    cleanChecks[1], cleanChecks[2],
  ]);
  expect(await screen.findByRole('group', { name: 'Hidden instructions' })).toBeTruthy();
  expect(within(screen.getByRole('group', { name: 'Hidden instructions' })).getByText('Unavailable')).toBeTruthy();
  expect(within(screen.getByRole('group', { name: 'Missing information' })).getByText('Clear')).toBeTruthy();
  expect(screen.getByRole('alert').textContent).toContain('Human review required');
});

it('renders model HTML as text without creating executable elements', async () => {
  const attack = '<img src=x onerror="window.compromised=true">';
  renderChecks([{ ...cleanChecks[0], flagged: true, details: { reasons: [attack] } }, cleanChecks[1], cleanChecks[2]]);
  expect(await screen.findByText(attack)).toBeTruthy();
  expect(document.querySelector('img[onerror]')).toBeNull();
  expect(screen.queryByRole('button', { name: /approve/i })).toBeNull();
});
