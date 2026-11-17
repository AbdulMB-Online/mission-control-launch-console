import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import App from '../../app/App';

const reportId = '00000000-0000-4000-8000-000000000001';
const selectedId = '00000000-0000-4000-8000-000000000003';
const briefing = {
  id: selectedId, round_number: 2, summary: 'Inspect the valve response before continuing.',
  recommended_actions: ['Confirm the response time.'], created_at: '2026-11-16T12:01:00.000000Z',
  evaluation_status: 'accepted', feedback: [], evaluated_at: '2026-11-16T12:01:02.000000Z', is_selected: true,
};
const baseReport = {
  id: reportId, engineer_name: 'Alex Rivera', station: 'PROP', wind_knots: '25.001', temp_c: '4.000',
  fuel_pct: '98.000', note: 'Valve response lagged.', created_at: '2026-11-16T12:00:00.000000Z',
  verdict: 'no_go', rule_version: 'v1', violations: [{ field: 'wind_knots', observed: '25.001', operator: '<=', limit: '25', message: 'Wind must be at most 25 knots.' }],
  classified_severity: 'low', effective_severity: 'high', deadline_minutes: 5,
  brief_by_at: '2026-11-16T12:05:00.000000Z', severity_provisional: false,
  subsystem: 'propulsion', classification_status: 'completed', classification_rationale: 'Valve anomaly.',
  requires_review: true, review_reasons: ['injection_flagged'], pipeline_status: 'completed', error_code: null,
  checks: [
    { kind: 'injection', status: 'completed', flagged: true, details: { reasons: ['Instruction-like text.'] }, error_code: null },
    { kind: 'missing_information', status: 'completed', flagged: false, details: { missing_details: [] }, error_code: null },
    { kind: 'tone', status: 'completed', flagged: false, details: { tone: 'calm', rationale: 'Factual tone.' }, error_code: null },
  ],
  briefings: [
    { ...briefing, id: '00000000-0000-4000-8000-000000000002', round_number: 1, summary: 'Earlier briefing.', evaluation_status: 'needs_revision', feedback: ['Specify the valve timing.'], is_selected: false },
    briefing,
  ],
  selected_briefing_id: selectedId, approval_state: 'pending', approval: null,
};
const approval = {
  id: '00000000-0000-4000-8000-000000000004', report_id: reportId, briefing_id: selectedId,
  approved_by: 'test-director', approved_at: '2026-11-16T12:02:00.000000Z',
  review_acknowledged: true, review_reasons_snapshot: ['injection_flagged'],
};
let currentReport: Record<string, unknown>;
const fetchMock = vi.fn();
const postMock = vi.fn();

beforeEach(() => {
  currentReport = structuredClone(baseReport);
  fetchMock.mockImplementation((url: string, init?: RequestInit) => {
    if (url === '/healthz') return Promise.resolve({ ok: true, json: async () => ({ status: 'ok', service: 'mission-control', provider: 'fake' }) });
    if (url === `/api/v1/reports/${reportId}/approve`) return postMock(init);
    if (url === `/api/v1/reports/${reportId}`) return Promise.resolve({ ok: true, json: async () => currentReport });
    if (url.startsWith('/api/v1/reports')) return Promise.resolve({ ok: true, json: async () => ({ items: [currentReport], total: 1, limit: 20, offset: 0 }) });
    throw new Error(`Unexpected request: ${url}`);
  });
  vi.stubGlobal('fetch', fetchMock);
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); vi.restoreAllMocks(); fetchMock.mockReset(); postMock.mockReset(); });

async function openReport() {
  render(<App />);
  fireEvent.click(await screen.findByRole('button', { name: 'Review report' }));
  return screen.findByRole('region', { name: 'Briefing review' });
}

function fillApproval(dialog: HTMLElement) {
  fireEvent.change(within(dialog).getByLabelText('Director username'), { target: { value: 'test-director' } });
  fireEvent.change(within(dialog).getByLabelText('Director password'), { target: { value: 'test-director-pass' } });
}

it('shows canonical NO_GO, selected and earlier drafts, evaluation feedback and pending human approval', async () => {
  const review = await openReport();
  expect(review.textContent).toContain('Alex Rivera');
  expect(review.textContent).toContain('PROP');
  expect(review.textContent).toContain('Valve response lagged.');
  expect(within(review).getByText('NO_GO')).toBeTruthy();
  expect(within(review).getByText('Wind must be at most 25 knots.')).toBeTruthy();
  expect(within(review).getByText('Inspect the valve response before continuing.')).toBeTruthy();
  expect(within(review).getByText('Earlier briefing.')).toBeTruthy();
  expect(within(review).getByText('Specify the valve timing.')).toBeTruthy();
  expect(within(review).getByText('Pending human approval')).toBeTruthy();
  expect(within(review).getByRole('group', { name: 'Hidden instructions' })).toBeTruthy();
  expect(within(review).getByLabelText('Briefing deadline').getAttribute('datetime')).toBe('2026-11-16T12:05:00.000000Z');
  expect(postMock).not.toHaveBeenCalled();
});

it('requires credentials, review acknowledgment and explicit confirmation before posting approval', async () => {
  const localWrite = vi.spyOn(Storage.prototype, 'setItem');
  postMock.mockImplementation(async () => {
    currentReport = { ...currentReport, approval_state: 'approved', approval };
    return { ok: true, status: 201, json: async () => approval };
  });
  const review = await openReport();
  fireEvent.click(within(review).getByRole('button', { name: 'Approve briefing' }));
  const dialog = await screen.findByRole('dialog', { name: 'Approve briefing' });
  expect(within(dialog).getByText('Approving this briefing does not authorize launch.')).toBeTruthy();
  const confirm = within(dialog).getByRole('button', { name: 'Confirm briefing approval' });
  expect(confirm.hasAttribute('disabled')).toBe(true);
  fillApproval(dialog);
  expect(confirm.hasAttribute('disabled')).toBe(true);
  fireEvent.click(within(dialog).getByRole('checkbox', { name: 'I have reviewed the flagged findings' }));
  fireEvent.click(confirm);
  expect(await screen.findByText('Approved by test-director')).toBeTruthy();
  expect(postMock).toHaveBeenCalledTimes(1);
  const init = postMock.mock.calls[0][0];
  expect(init.method).toBe('POST');
  expect(init.headers.Authorization).toBe(`Basic ${btoa('test-director:test-director-pass')}`);
  expect(JSON.parse(init.body)).toEqual({ briefing_id: selectedId, acknowledge_review: true });
  expect(localWrite).not.toHaveBeenCalled();
  expect(screen.queryByLabelText('Director password')).toBeNull();
  expect(within(screen.getByRole('region', { name: 'Briefing review' })).getByText('NO_GO')).toBeTruthy();
});

it('shows rejected credentials without marking approval and clears the password after the request', async () => {
  postMock.mockResolvedValue({ ok: false, status: 401, json: async () => ({ error: { code: 'unauthorized', message: 'Director credentials are invalid.' } }) });
  const review = await openReport();
  fireEvent.click(within(review).getByRole('button', { name: 'Approve briefing' }));
  const dialog = await screen.findByRole('dialog', { name: 'Approve briefing' });
  fillApproval(dialog);
  fireEvent.click(within(dialog).getByRole('checkbox', { name: 'I have reviewed the flagged findings' }));
  fireEvent.click(within(dialog).getByRole('button', { name: 'Confirm briefing approval' }));
  expect(await within(dialog).findByText('Director credentials are invalid.')).toBeTruthy();
  expect((within(dialog).getByLabelText('Director password') as HTMLInputElement).value).toBe('');
  expect(screen.queryByText('Approved by test-director')).toBeNull();
});

it.each(['queued', 'processing', 'failed'])('disables approval for an unavailable %s briefing', async state => {
  currentReport = { ...currentReport, pipeline_status: state, approval_state: 'unavailable', selected_briefing_id: null, briefings: [] };
  const review = await openReport();
  expect(within(review).getByRole('button', { name: 'Approve briefing' }).hasAttribute('disabled')).toBe(true);
  expect(postMock).not.toHaveBeenCalled();
});

it('renders model briefing and feedback markup as text without granting authority', async () => {
  const markup = '<img src=x onerror="window.compromised=true">';
  currentReport = { ...currentReport, briefings: [{ ...briefing, summary: markup }] };
  const review = await openReport();
  expect(within(review).getByText(markup)).toBeTruthy();
  expect(document.querySelector('img[onerror]')).toBeNull();
  expect(postMock).not.toHaveBeenCalled();
});

it('polls an active selected report and displays the completed briefing', async () => {
  vi.useFakeTimers();
  currentReport = { ...currentReport, pipeline_status: 'processing', approval_state: 'unavailable', selected_briefing_id: null, briefings: [] };
  await act(async () => { render(<App />); });
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Review report' })); });
  currentReport = structuredClone(baseReport);
  await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
  const review = screen.getByRole('region', { name: 'Briefing review' });
  expect(within(review).getByText('Inspect the valve response before continuing.')).toBeTruthy();
  expect(postMock).not.toHaveBeenCalled();
});

it('stops selected-report polling when the workspace unmounts', async () => {
  vi.useFakeTimers();
  currentReport = { ...currentReport, pipeline_status: 'processing', approval_state: 'unavailable', selected_briefing_id: null, briefings: [] };
  let view!: ReturnType<typeof render>;
  await act(async () => { view = render(<App />); });
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Review report' })); });
  view.unmount();
  const before = fetchMock.mock.calls.length;
  await act(async () => { await vi.advanceTimersByTimeAsync(4000); });
  expect(fetchMock.mock.calls).toHaveLength(before);
});
