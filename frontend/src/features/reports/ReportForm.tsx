import { useRef, useState, type FormEvent } from 'react';
import { fileReport, ReportApiError, type FieldErrors, type Report, type ReportInput } from '../../api/reports';

const emptyReport: ReportInput = { engineer_name: '', station: '', wind_knots: '', temp_c: '', fuel_pct: '', note: '' };
const fields = [
  { name: 'engineer_name', label: 'Engineer name', maxLength: 100, placeholder: 'Your full name' },
  { name: 'station', label: 'Station', maxLength: 50, placeholder: 'For example, PROP' },
  { name: 'wind_knots', label: 'Wind (knots)', placeholder: '25.000', decimal: true },
  { name: 'temp_c', label: 'Temperature (°C)', placeholder: '4.000', decimal: true },
  { name: 'fuel_pct', label: 'Fuel (%)', placeholder: '98.000', decimal: true },
] as const;

export function ReportForm({ onFiled, onCancel }: { onFiled: (report: Report) => void; onCancel: () => void }) {
  const [values, setValues] = useState<ReportInput>({ ...emptyReport });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [message, setMessage] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const submitting = useRef(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true;
    setPending(true);
    setErrors({});
    setMessage(null);
    try {
      const report = await fileReport(values);
      onFiled(report);
    } catch (error) {
      if (error instanceof ReportApiError) {
        setErrors(error.fields);
        setMessage(error.message);
      } else {
        setMessage('Could not file the report. Your entries are saved here; try again.');
      }
    } finally {
      submitting.current = false;
      setPending(false);
    }
  }

  return (
    <form className="report-form" aria-label="File anomaly report" onSubmit={submit} noValidate>
      <div className="form-intro"><h3>File an anomaly report</h3><p>Include the readings and what you observed. Every field is required.</p></div>
      {message && <div className="form-message" role="alert">{message}</div>}
      <div className="report-fields">
        {fields.map(field => (
          <div className={`report-field ${'decimal' in field ? 'reading-field' : 'identity-field'}`} key={field.name}>
            <label htmlFor={`report-${field.name}`}>{field.label}</label>
            <input
              id={`report-${field.name}`} name={field.name} type="text" required
              autoFocus={field.name === 'engineer_name'}
              autoComplete={field.name === 'engineer_name' ? 'name' : 'off'}
              maxLength={'maxLength' in field ? field.maxLength : 11}
              inputMode={'decimal' in field ? 'decimal' : 'text'}
              placeholder={field.placeholder} value={values[field.name]} readOnly={pending}
              aria-invalid={Boolean(errors[field.name])}
              aria-describedby={errors[field.name] ? `error-${field.name}` : 'decimal' in field ? 'decimal-guidance' : undefined}
              onChange={event => setValues(current => ({ ...current, [field.name]: event.target.value }))}
            />
            {errors[field.name] && <p className="field-error" id={`error-${field.name}`}>{errors[field.name]}</p>}
          </div>
        ))}
        <p className="reading-guidance" id="decimal-guidance">Use up to three decimal places. Readings outside launch limits can still be filed.</p>
        <div className="report-field note-field"><label htmlFor="report-note">Anomaly note</label><textarea
          id="report-note" name="note" required maxLength={4000} rows={4} value={values.note} readOnly={pending}
          placeholder="What happened, when did it happen, and what have you checked?"
          aria-invalid={Boolean(errors.note)} aria-describedby={errors.note ? 'error-note' : undefined}
          onChange={event => setValues(current => ({ ...current, note: event.target.value }))}
        />{errors.note && <p className="field-error" id="error-note">{errors.note}</p>}</div>
      </div>
      <div className="form-actions"><button className="cancel-report" type="button" disabled={pending} onClick={onCancel}>Cancel</button><button className="submit-report" type="submit" disabled={pending}>{pending ? 'Filing report…' : 'Submit report'}</button></div>
    </form>
  );
}
