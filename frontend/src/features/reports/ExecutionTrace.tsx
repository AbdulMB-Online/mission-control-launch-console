import { useEffect, useState } from 'react';
import { fetchTraces, type TracePage, type TraceStep } from '../../api/traces';

const labels: Record<string, string> = {
  filing: 'Report filing', launch_rules: 'Launch limits', priority_provisional: 'Provisional priority',
  classification: 'Classification', priority_resolved: 'Resolved priority', injection: 'Hidden instructions',
  missing_information: 'Missing information', tone: 'Report tone', approval: 'Human approval',
};
const label = (step: TraceStep) => labels[step.step_key] ?? (/^(draft|evaluation)_[1-3]$/.test(step.step_key)
  ? `${step.step_key.startsWith('draft') ? 'Draft' : 'Evaluation'} ${step.round_number}` : step.step_key);
const dateLabel = (value: string) => `${new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'medium', timeZone: 'UTC' })} UTC`;

export function ExecutionTrace({ reportId, refreshToken, pipelineStatus, approvalId }: {
  reportId: string; refreshToken: number; pipelineStatus: string; approvalId: string | undefined;
}) {
  const [page, setPage] = useState<TracePage | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    setError(false);
    async function refresh() {
      try {
        const result = await fetchTraces(reportId, controller.signal);
        if (controller.signal.aborted) return;
        setPage(result);
        if (['queued', 'processing'].includes(pipelineStatus) || result.steps.some(step => step.status === 'running')) timer = setTimeout(() => void refresh(), 2000);
      } catch {
        if (!controller.signal.aborted) setError(true);
      }
    }
    void refresh();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [reportId, refreshToken, pipelineStatus, approvalId]);

  return <section className="execution-trace" aria-labelledby="trace-heading"><header className="trace-header"><h3 id="trace-heading">Execution trace</h3><p>Recorded processing steps</p></header>
    {error && <p className="form-message" role="alert">Execution trace could not be loaded. Refresh to retry.</p>}
    {!page && !error && <p className="trace-loading" role="status">Loading execution trace…</p>}
    {page && <>
      <div className="trace-totals"><div><span>{page.totals.cost_complete ? 'Recorded cost (USD)' : 'Known cost subtotal — incomplete'}</span><strong>${page.totals.known_cost_usd}</strong></div><dl><div><dt>Input tokens</dt><dd>{page.totals.input_tokens}</dd></div><div><dt>Cached input subset</dt><dd>{page.totals.cached_input_tokens}</dd></div><div><dt>Output tokens</dt><dd>{page.totals.output_tokens}</dd></div></dl>
        {!page.totals.usage_complete && <p>Token totals include only available usage.</p>}
        {page.totals.simulated && <p className="simulation-note">Simulated usage and cost</p>}
      </div>
      <div className="trace-steps">{groupSteps(page.steps).map(group => group[0].parallel_group
        ? <div className="parallel-traces" role="group" aria-label="Parallel advisory checks" key={group[0].parallel_group}><p>Parallel advisory checks</p>{group.map(step => <StepCard key={step.id} step={step} />)}</div>
        : <StepCard key={group[0].id} step={group[0]} />)}</div>
      {page.steps.length === 0 && <p className="trace-loading">No execution steps were recorded for this report.</p>}
    </>}
  </section>;
}

function groupSteps(steps: TraceStep[]): TraceStep[][] {
  const groups: TraceStep[][] = [];
  for (const step of steps) {
    const group = step.parallel_group ? groups.find(items => items[0].parallel_group === step.parallel_group) : undefined;
    if (group) group.push(step); else groups.push([step]);
  }
  return groups;
}

function StepCard({ step }: { step: TraceStep }) {
  const headingId = `step-${step.id}`;
  const deterministic = step.provider === 'python' || step.provider === 'human';
  return <article className={`trace-card trace-${step.status}`} aria-labelledby={headingId}>
    <header><h4 id={headingId}>{label(step)}</h4><span className="trace-status">{{ running: 'In progress', completed: 'Completed', error: 'Failed' }[step.status]}</span></header>
    <p className="trace-provider">{deterministic ? step.provider === 'human' ? 'Director action' : 'Python rules' : step.model ?? 'Model unavailable'}{step.provider === 'fake' && <span>Simulation</span>}</p>
    <dl className="trace-timing"><div><dt>Started</dt><dd><time dateTime={step.started_at}>{dateLabel(step.started_at)}</time></dd></div>{step.finished_at && <div><dt>Finished</dt><dd><time dateTime={step.finished_at}>{dateLabel(step.finished_at)}</time></dd></div>}</dl>
    {step.usage_status === 'reported' ? <dl className="trace-usage"><div><dt>Input tokens</dt><dd>{step.input_tokens}</dd></div><div><dt>Cached input subset</dt><dd>{step.cached_input_tokens}</dd></div><div><dt>Output tokens</dt><dd>{step.output_tokens}</dd></div><div><dt>Cost (USD)</dt><dd>{step.cost_usd === null ? 'Cost unknown' : `$${step.cost_usd}`}</dd></div></dl>
      : <div className="trace-unknown"><span>Usage unavailable</span><span>{step.cost_usd === null ? 'Cost unknown' : `$${step.cost_usd}`}</span></div>}
    {step.error_code && <p className="trace-error">{step.error_code}</p>}
    <details className="trace-metadata"><summary>Step metadata</summary><dl><div><dt>Version</dt><dd>{step.prompt_version}</dd></div>{step.provider_response_id && <div><dt>Response reference</dt><dd>{step.provider_response_id}</dd></div>}{step.rate_snapshot && <div><dt>Rate snapshot</dt><dd>{step.rate_snapshot.version}; per million tokens: ${step.rate_snapshot.input_per_million} input, ${step.rate_snapshot.cached_input_per_million} cached input, ${step.rate_snapshot.output_per_million} output.</dd></div>}</dl></details>
  </article>;
}
