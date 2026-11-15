export type ReportInput = {
  engineer_name: string;
  station: string;
  wind_knots: string;
  temp_c: string;
  fuel_pct: string;
  note: string;
};

export type Report = ReportInput & { id: string; created_at: string };
export type ReportPage = { items: Report[]; total: number; limit: number; offset: number };
export type FieldErrors = Partial<Record<keyof ReportInput, string>>;

const inputFields = ['engineer_name', 'station', 'wind_knots', 'temp_c', 'fuel_pct', 'note'] as const;
const reportFields = [...inputFields, 'id', 'created_at'] as const;
const isObject = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;

function readReport(value: unknown): Report {
  if (!isObject(value) || !reportFields.every(field => typeof value[field] === 'string')) {
    throw new Error('Invalid report response');
  }
  return value as Report;
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
