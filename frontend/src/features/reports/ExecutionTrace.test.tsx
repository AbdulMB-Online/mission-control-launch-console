import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import App from '../../app/App';

const reportId = '00000000-0000-4000-8000-000000000001';
const selectedId = '00000000-0000-4000-8000-000000000002';
const report = {
  id: reportId, engineer_name: 'Alex Rivera', station: 'PROP', wind_knots: '25', temp_c: '4', fuel_pct: '98',
  note: 'Valve response lagged.', created_at: '2026-11-17T12:00:00.000000Z', verdict: 'go', rule_version: 'v1', violations: [],
  classified_severity: 'low', effective_severity: 'low', deadline_minutes: 30,
  brief_by_at: '2026-11-17T12:30:00.000000Z', severity_provisional: false,
  subsystem: 'propulsion', classification_status: 'completed', classification_rationale: 'Valve anomaly.',
  requires_review: false, review_reasons: [], pipeline_status: 'completed', error_code: null, checks: [],
  briefings: [{ id: selectedId, round_number: 1, summary: 'Inspect the valve response.', recommended_actions: [],
    created_at: '2026-11-17T12:01:00.000000Z', evaluation_status: 'accepted', feedback: [],
    evaluated_at: '2026-11-17T12:01:02.000000Z', is_selected: true }],
  selected_briefing_id: selectedId, approval_state: 'pending', approval: null,
};
const rate = { version: 'openai-standard-2026-11-17', model: 'gpt-5.4-mini-2026-03-17', input_per_million: '0.75', cached_input_per_million: '0.075', output_per_million: '4.50' };
function step(key: string, order: number, overrides: Record<string, unknown> = {}) {
  return { id: `trace-${key}`, report_id: reportId, step_key: key, display_order: order, status: 'completed',
    started_at: '2026-11-17T12:00:01.000000Z', finished_at: '2026-11-17T12:00:02.000000Z',
    provider: 'openai', model: rate.model, prompt_version: `${key}-v1`, provider_response_id: `resp-${key}`,
    input_tokens: 1000, cached_input_tokens: 200, output_tokens: 100, usage_status: 'reported',
    error_code: null, parallel_group: null, round_number: null, cost_usd: '0.001065', rate_snapshot: rate, ...overrides };
}
const fixture = {
  report_id: reportId,
  steps: [
    step('launch_rules', 20, { provider: 'python', model: null, input_tokens: 0, cached_input_tokens: 0, output_tokens: 0, cost_usd: '0', rate_snapshot: null }),
    step('classification', 30),
    step('injection', 50, { parallel_group: 'parallel-checks' }),
    step('missing_information', 51, { parallel_group: 'parallel-checks' }),
    step('tone', 52, { parallel_group: 'parallel-checks' }),
    step('draft_1', 100, { round_number: 1 }),
    step('evaluation_1', 110, { round_number: 1 }),
  ],
  totals: { input_tokens: 6000, cached_input_tokens: 1200, output_tokens: 600, usage_complete: true,
    known_cost_usd: '0.006390', cost_complete: true, simulated: false },
};
let trace: typeof fixture;
let traceUnavailable: boolean;
const fetchMock = vi.fn();

beforeEach(() => {
  trace = structuredClone(fixture);
  traceUnavailable = false;
  fetchMock.mockImplementation((url: string) => {
    if (url === '/healthz') return Promise.resolve({ ok: true, json: async () => ({ status: 'ok', service: 'mission-control', provider: 'fake' }) });
    if (url === `/api/v1/reports/${reportId}/traces`) return Promise.resolve({ ok: !traceUnavailable, status: traceUnavailable ? 503 : 200, json: async () => trace });
    if (url === `/api/v1/reports/${reportId}`) return Promise.resolve({ ok: true, json: async () => report });
    if (url.startsWith('/api/v1/reports')) return Promise.resolve({ ok: true, json: async () => ({ items: [report], total: 1, limit: 20, offset: 0 }) });
    throw new Error(`Unexpected request: ${url}`);
  });
  vi.stubGlobal('fetch', fetchMock);
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); fetchMock.mockReset(); });

async function openTrace() {
  render(<App />);
  fireEvent.click(await screen.findByRole('button', { name: 'Review report' }));
  return screen.findByRole('region', { name: 'Execution trace' });
}

it('shows a card for each executed step, rounds, parallel grouping, timing and token subsets', async () => {
  const region = await openTrace();
  expect(await within(region).findAllByRole('article')).toHaveLength(7);
  const classification = within(region).getByRole('article', { name: 'Classification' });
  expect(within(classification).getByText(rate.model)).toBeTruthy();
  expect(within(classification).getByText('1000')).toBeTruthy();
  expect(within(classification).getByText('200')).toBeTruthy();
  expect(within(classification).getByText('100')).toBeTruthy();
  expect(within(classification).getByText('$0.001065')).toBeTruthy();
  expect(classification.querySelector('time')?.getAttribute('datetime')).toBe('2026-11-17T12:00:01.000000Z');
  expect(within(region).getByRole('group', { name: 'Parallel advisory checks' })).toBeTruthy();
  expect(within(region).getByRole('article', { name: 'Draft 1' })).toBeTruthy();
  expect(within(region).getByRole('article', { name: 'Evaluation 1' })).toBeTruthy();
  expect(within(region).getByText('$0.006390')).toBeTruthy();
});

it('uses the server cost total without browser token arithmetic or rounding away small costs', async () => {
  trace.totals.known_cost_usd = '0.000000075';
  const region = await openTrace();
  expect(await within(region).findByText('$0.000000075')).toBeTruthy();
  expect(within(region).queryByText('$0.00')).toBeNull();
});

it('keeps failed calls and visibly marks unavailable usage and incomplete cost subtotals', async () => {
  trace.steps[1] = step('classification', 30, { status: 'error', error_code: 'timeout', input_tokens: null, cached_input_tokens: null, output_tokens: null, usage_status: 'unavailable', cost_usd: null, rate_snapshot: null });
  trace.totals.cost_complete = false;
  trace.totals.usage_complete = false;
  const region = await openTrace();
  const card = await within(region).findByRole('article', { name: 'Classification' });
  expect(within(card).getByText('Usage unavailable')).toBeTruthy();
  expect(within(card).getByText('Cost unknown')).toBeTruthy();
  expect(card.textContent).toContain('timeout');
  expect(within(region).getByText('Known cost subtotal — incomplete')).toBeTruthy();
  expect(within(card).queryByText('$0')).toBeNull();
});

it('shows running calls with unknown cost and no invented completion time', async () => {
  trace.steps = [step('classification', 30, { status: 'running', finished_at: null, input_tokens: null, cached_input_tokens: null, output_tokens: null, usage_status: 'unavailable', cost_usd: null, rate_snapshot: null })];
  trace.totals.cost_complete = false;
  trace.totals.usage_complete = false;
  const region = await openTrace();
  const card = await within(region).findByRole('article', { name: 'Classification' });
  expect(within(card).getByText('In progress')).toBeTruthy();
  expect(within(card).getByText('Cost unknown')).toBeTruthy();
  expect(card.querySelectorAll('time')).toHaveLength(1);
});

it('labels fake usage and zero real cost as simulation', async () => {
  trace.steps = [step('classification', 30, { provider: 'fake', model: 'fake-v1', input_tokens: 0, cached_input_tokens: 0, output_tokens: 0, cost_usd: '0', rate_snapshot: null })];
  trace.totals = { input_tokens: 0, cached_input_tokens: 0, output_tokens: 0, usage_complete: true, known_cost_usd: '0', cost_complete: true, simulated: true };
  const region = await openTrace();
  expect(await within(region).findByText('Simulated usage and cost')).toBeTruthy();
  expect(within(region).getByRole('article', { name: 'Classification' }).textContent).toContain('fake-v1');
});

it('keeps the briefing available when trace retrieval fails', async () => {
  traceUnavailable = true;
  await openTrace();
  expect(await screen.findByText('Execution trace could not be loaded. Refresh to retry.')).toBeTruthy();
  expect(screen.getByText('Inspect the valve response.')).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Approve briefing' }).hasAttribute('disabled')).toBe(false);
});
