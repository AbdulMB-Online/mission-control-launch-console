export type ReportInput = {
  engineer_name: string;
  station: string;
  wind_knots: string;
  temp_c: string;
  fuel_pct: string;
  note: string;
};

export type Severity = 'high' | 'medium' | 'low';
export type Briefing = {
  id: string; round_number: number; summary: string; recommended_actions: string[];
  created_at: string; evaluation_status: 'pending' | 'accepted' | 'needs_revision' | 'error';
  feedback: string[]; evaluated_at: string | null; is_selected: boolean;
};
export type Approval = {
  id: string; report_id: string; briefing_id: string; approved_by: string; approved_at: string;
  review_acknowledged: boolean; review_reasons_snapshot: string[];
};
export type AdvisoryCheck = {
  kind: 'injection' | 'missing_information' | 'tone';
  status: 'completed' | 'error';
  flagged: boolean | null;
  details: { reasons?: string[]; missing_details?: string[]; tone?: 'calm' | 'urgent' | 'panic'; rationale?: string };
  error_code: string | null;
};
export type Report = ReportInput & {
  id: string;
  created_at: string;
  classified_severity: Severity | null;
  effective_severity: Severity;
  deadline_minutes: 5 | 15 | 30;
  brief_by_at: string;
  severity_provisional: boolean;
  requires_review: boolean;
  review_reasons: string[];
  checks: AdvisoryCheck[];
  verdict: 'go' | 'no_go';
  violations: { field: string; observed: string; operator: string; limit: string; message: string }[];
  subsystem: string;
  classification_status: 'not_run' | 'completed' | 'fallback';
  classification_rationale: string;
  pipeline_status: 'queued' | 'processing' | 'completed' | 'failed';
  error_code: string | null;
  briefings: Briefing[];
  selected_briefing_id: string | null;
  approval_state: 'unavailable' | 'pending' | 'approved';
  approval: Approval | null;
};
export type ReportPage = { items: Report[]; total: number; limit: number; offset: number };
export type FieldErrors = Partial<Record<keyof ReportInput, string>>;

const inputFields = ['engineer_name', 'station', 'wind_knots', 'temp_c', 'fuel_pct', 'note'] as const;
const reportFields = [...inputFields, 'id', 'created_at'] as const;
const severities: Severity[] = ['high', 'medium', 'low'];
const isObject = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;
const isStringList = (value: unknown): value is string[] => Array.isArray(value) && value.every(item => typeof item === 'string');
const isDate = (value: unknown): value is string => typeof value === 'string' && !Number.isNaN(Date.parse(value));

function readApproval(value: unknown): Approval {
  if (!isObject(value) || !['id', 'report_id', 'briefing_id', 'approved_by'].every(key => typeof value[key] === 'string')
    || !isDate(value.approved_at) || typeof value.review_acknowledged !== 'boolean'
    || !isStringList(value.review_reasons_snapshot)) throw new Error('Invalid approval response');
  return value as Approval;
}

function readBriefing(value: unknown): Briefing {
  if (!isObject(value) || typeof value.id !== 'string' || typeof value.summary !== 'string'
    || !Number.isInteger(value.round_number) || ![1, 2, 3].includes(value.round_number as number)
    || !isStringList(value.recommended_actions) || !isDate(value.created_at)
    || !['pending', 'accepted', 'needs_revision', 'error'].includes(value.evaluation_status as string)
    || !isStringList(value.feedback) || !(value.evaluated_at === null || isDate(value.evaluated_at))
    || typeof value.is_selected !== 'boolean') throw new Error('Invalid briefing response');
  return value as Briefing;
}

function readCheck(value: unknown): AdvisoryCheck {
  if (!isObject(value) || !['injection', 'missing_information', 'tone'].includes(value.kind as string)
    || !['completed', 'error'].includes(value.status as string) || !isObject(value.details)
    || !(value.error_code === null || typeof value.error_code === 'string')) throw new Error('Invalid check response');
  if (value.status === 'error') {
    if (value.flagged !== null) throw new Error('Unknown check must not be marked clear');
  } else if (typeof value.flagged !== 'boolean'
    || (value.kind === 'injection' && !isStringList(value.details.reasons))
    || (value.kind === 'missing_information' && !isStringList(value.details.missing_details))
    || (value.kind === 'tone' && (!['calm', 'urgent', 'panic'].includes(value.details.tone as string)
      || typeof value.details.rationale !== 'string'))) throw new Error('Invalid check details');
  return value as AdvisoryCheck;
}

function readReport(value: unknown): Report {
  if (!isObject(value) || !reportFields.every(field => typeof value[field] === 'string')
    || !severities.includes(value.effective_severity as Severity)
    || (value.classified_severity !== null && !severities.includes(value.classified_severity as Severity))
    || typeof value.deadline_minutes !== 'number' || ![5, 15, 30].includes(value.deadline_minutes)
    || typeof value.brief_by_at !== 'string' || Number.isNaN(Date.parse(value.brief_by_at))
    || typeof value.severity_provisional !== 'boolean' || typeof value.requires_review !== 'boolean'
    || !isStringList(value.review_reasons) || !Array.isArray(value.checks)
    || !['go', 'no_go'].includes(value.verdict as string) || !Array.isArray(value.violations)
    || !value.violations.every(item => isObject(item) && ['field', 'observed', 'operator', 'limit', 'message'].every(key => typeof item[key] === 'string'))
    || typeof value.subsystem !== 'string' || typeof value.classification_rationale !== 'string'
    || !['not_run', 'completed', 'fallback'].includes(value.classification_status as string)
    || !['queued', 'processing', 'completed', 'failed'].includes(value.pipeline_status as string)
    || !(value.error_code === null || typeof value.error_code === 'string')
    || !Array.isArray(value.briefings) || !(value.selected_briefing_id === null || typeof value.selected_briefing_id === 'string')
    || !['unavailable', 'pending', 'approved'].includes(value.approval_state as string)) {
    throw new Error('Invalid report response');
  }
  const checks = value.checks.map(readCheck);
  if (new Set(checks.map(item => item.kind)).size !== checks.length) throw new Error('Duplicate check response');
  const briefings = value.briefings.map(readBriefing);
  const approval = value.approval === null ? null : readApproval(value.approval);
  return { ...value, checks, briefings, approval } as Report;
}

export class ReportApiError extends Error {
  constructor(message: string, public fields: FieldErrors) { super(message); }
}

export async function fileReport(submission: ReportInput): Promise<Report> {
  const response = await fetch('/api/v1/reports', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(submission),
  });
  const data: unknown = await response.json();
  if (!response.ok) {
    const error = isObject(data) && isObject(data.error) ? data.error : {};
    const fields: FieldErrors = {};
    if (Array.isArray(error.fields)) {
      for (const item of error.fields) {
        if (isObject(item) && inputFields.includes(item.field as keyof ReportInput) && typeof item.message === 'string') {
          fields[item.field as keyof ReportInput] = item.message;
        }
      }
    }
    throw new ReportApiError(typeof error.message === 'string' ? error.message : 'The report could not be saved. Try again.', fields);
  }
  return readReport(data);
}

export async function fetchReports(signal: AbortSignal): Promise<ReportPage> {
  const response = await fetch('/api/v1/reports', { signal });
  if (!response.ok) throw new Error('Could not load reports');
  const data: unknown = await response.json();
  if (!isObject(data) || !Array.isArray(data.items) || typeof data.total !== 'number'
    || typeof data.limit !== 'number' || typeof data.offset !== 'number') throw new Error('Invalid report list');
  return { items: data.items.map(readReport), total: data.total, limit: data.limit, offset: data.offset };
}

export async function fetchReport(id: string, signal: AbortSignal): Promise<Report> {
  const response = await fetch(`/api/v1/reports/${encodeURIComponent(id)}`, { signal });
  if (!response.ok) throw new Error('Could not refresh this report. Close and reopen it to retry.');
  return readReport(await response.json());
}

export async function approveBriefing(reportId: string, briefingId: string, acknowledgeReview: boolean, username: string, password: string): Promise<Approval> {
  const encoded = btoa(Array.from(new TextEncoder().encode(`${username}:${password}`), byte => String.fromCharCode(byte)).join(''));
  const response = await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Basic ${encoded}` },
    body: JSON.stringify({ briefing_id: briefingId, acknowledge_review: acknowledgeReview }),
  });
  const data: unknown = await response.json();
  if (!response.ok) {
    const error = isObject(data) && isObject(data.error) ? data.error : {};
    throw new Error(typeof error.message === 'string' ? error.message : 'Approval was not confirmed. Close and reopen this report before trying again.');
  }
  const approval = readApproval(data);
  if (approval.report_id !== reportId || approval.briefing_id !== briefingId) throw new Error('Approval response did not match this briefing. Reopen the report to check its status.');
  return approval;
}
