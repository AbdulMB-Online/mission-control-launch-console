export type ReportInput = {
  engineer_name: string;
  station: string;
  wind_knots: string;
  temp_c: string;
  fuel_pct: string;
  note: string;
};

export type Severity = 'high' | 'medium' | 'low';
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
};
export type ReportPage = { items: Report[]; total: number; limit: number; offset: number };
export type FieldErrors = Partial<Record<keyof ReportInput, string>>;

const inputFields = ['engineer_name', 'station', 'wind_knots', 'temp_c', 'fuel_pct', 'note'] as const;
const reportFields = [...inputFields, 'id', 'created_at'] as const;
const severities: Severity[] = ['high', 'medium', 'low'];
const isObject = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;
const isStringList = (value: unknown): value is string[] => Array.isArray(value) && value.every(item => typeof item === 'string');

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
    || !isStringList(value.review_reasons) || !Array.isArray(value.checks)) {
    throw new Error('Invalid report response');
  }
  const checks = value.checks.map(readCheck);
  if (new Set(checks.map(item => item.kind)).size !== checks.length) throw new Error('Duplicate check response');
  return { ...value, checks } as Report;
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
