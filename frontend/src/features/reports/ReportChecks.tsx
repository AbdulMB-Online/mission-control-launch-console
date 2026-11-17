import type { AdvisoryCheck, Report } from '../../api/reports';
import { Icon } from '../../app/Icon';

const labels = { injection: 'Hidden instructions', missing_information: 'Missing information', tone: 'Report tone' };

function statusLabel(check: AdvisoryCheck): string {
  if (check.status === 'error') return 'Unavailable';
  if (check.kind === 'tone') return { calm: 'Calm', urgent: 'Urgent', panic: 'Panic' }[check.details.tone!];
  return check.flagged ? 'Flagged' : 'Clear';
}

export function ReportChecks({ report }: { report: Report }) {
  return <div className="report-analysis">
    {report.requires_review && <div className="review-notice" role="alert"><Icon name="shield" /><div><strong>Human review required</strong><p>Review flagged findings and unavailable checks before approving a briefing.</p></div></div>}
    {report.checks.length === 0 ? <p className="checks-pending">Advisory checks pending</p> : <div className="check-results">
      {report.checks.map(check => <div className="check-group" role="group" aria-label={labels[check.kind]} key={check.kind}>
        <div className="check-heading"><h4>{labels[check.kind]}</h4><span className={`check-badge ${check.flagged || check.status === 'error' ? 'attention' : ''}`}>{statusLabel(check)}</span></div>
        {check.status === 'error' ? <p>This check did not complete. Review the report directly.</p> : <>
          {(check.details.reasons ?? check.details.missing_details ?? []).length > 0 && <ul>{(check.details.reasons ?? check.details.missing_details ?? []).map((detail, index) => <li key={index}>{detail}</li>)}</ul>}
          {check.details.rationale && <p>{check.details.rationale}</p>}
        </>}
      </div>)}
    </div>}
  </div>;
}
