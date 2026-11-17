export type TraceStep = {
  id: string; report_id: string; step_key: string; display_order: number;
  status: 'running' | 'completed' | 'error'; started_at: string; finished_at: string | null;
  provider: string; model: string | null; prompt_version: string; provider_response_id: string | null;
  input_tokens: number | null; cached_input_tokens: number | null; output_tokens: number | null;
  usage_status: 'reported' | 'unavailable'; error_code: string | null; parallel_group: string | null;
  round_number: number | null; cost_usd: string | null; rate_snapshot: Record<string, string> | null;
};
export type TracePage = {
  report_id: string; steps: TraceStep[];
  totals: { input_tokens: number; cached_input_tokens: number; output_tokens: number;
    usage_complete: boolean; known_cost_usd: string; cost_complete: boolean; simulated: boolean };
};

const object = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;
const count = (value: unknown): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
const date = (value: unknown) => typeof value === 'string' && !Number.isNaN(Date.parse(value));
const nullableString = (value: unknown) => value === null || typeof value === 'string';
const dollars = (value: unknown) => typeof value === 'string' && /^(?:0|[1-9]\d*)(?:\.\d+)?$/.test(value);

function validStep(value: unknown): value is TraceStep {
  if (!object(value) || !['id', 'report_id', 'step_key', 'provider', 'prompt_version'].every(key => typeof value[key] === 'string')
    || !Number.isInteger(value.display_order) || !['running', 'completed', 'error'].includes(value.status as string)
    || !date(value.started_at) || !(value.finished_at === null || date(value.finished_at))
    || !['model', 'provider_response_id', 'error_code', 'parallel_group'].every(key => nullableString(value[key]))
    || !(value.round_number === null || [1, 2, 3].includes(value.round_number as number))
    || !(value.cost_usd === null || dollars(value.cost_usd))
    || !(value.rate_snapshot === null || (object(value.rate_snapshot) && Object.values(value.rate_snapshot).every(item => typeof item === 'string')))) return false;
  if (value.usage_status === 'reported') return count(value.input_tokens) && count(value.cached_input_tokens)
    && count(value.output_tokens) && value.cached_input_tokens <= value.input_tokens;
  return value.usage_status === 'unavailable' && value.input_tokens === null && value.cached_input_tokens === null && value.output_tokens === null;
}

export async function fetchTraces(reportId: string, signal: AbortSignal): Promise<TracePage> {
  const response = await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/traces`, { signal });
  if (!response.ok) throw new Error('Trace unavailable');
  const data: unknown = await response.json();
  if (!object(data) || data.report_id !== reportId || !Array.isArray(data.steps) || !data.steps.every(validStep)
    || !object(data.totals)) throw new Error('Invalid trace response');
  const totals = data.totals;
  if (!['input_tokens', 'cached_input_tokens', 'output_tokens'].every(key => count(totals[key]))
    || !['usage_complete', 'cost_complete', 'simulated'].every(key => typeof totals[key] === 'boolean')
    || !dollars(totals.known_cost_usd)) throw new Error('Invalid trace totals');
  const steps = data.steps as TraceStep[];
  if (steps.some(step => step.report_id !== reportId) || new Set(steps.map(step => step.id)).size !== steps.length) throw new Error('Invalid trace identity');
  return data as TracePage;
}
