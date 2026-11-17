import { useEffect, useState } from 'react';
import { fetchReport, type Approval, type Briefing, type Report } from '../../api/reports';
import { ReportChecks } from './ReportChecks';
import { ApprovalDialog } from './ApprovalDialog';
import { ExecutionTrace } from './ExecutionTrace';

const dateLabel = (value: string) => `${new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'medium', timeZone: 'UTC' })} UTC`;
const evaluationLabels = { pending: 'Evaluation pending', accepted: 'Evaluator accepted', needs_revision: 'Revision requested', error: 'Evaluation unavailable' };

export function DirectorReview({ initialReport, refreshToken, onReportChanged, onClose }: {
  initialReport: Report; refreshToken: number; onReportChanged: (report: Report) => void; onClose: () => void;
}) {
  const [report, setReport] = useState(initialReport);
  const [loadError, setLoadError] = useState(false);
  const [showApproval, setShowApproval] = useState(false);
  const reportId = initialReport.id;

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    setLoadError(false);
    async function refresh() {
      try {
        const latest = await fetchReport(reportId, controller.signal);
        if (controller.signal.aborted) return;
        setReport(latest);
        onReportChanged(latest);
        if (latest.pipeline_status === 'queued' || latest.pipeline_status === 'processing') timer = setTimeout(() => void refresh(), 2000);
      } catch {
        if (!controller.signal.aborted) setLoadError(true);
      }
    }
    void refresh();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [reportId, refreshToken, onReportChanged]);

  const selected = report.briefings.find(item => item.id === report.selected_briefing_id && item.is_selected);
  const canApprove = !loadError && report.pipeline_status === 'completed' && Boolean(selected) && report.approval_state === 'pending';
  function approved(approval: Approval) {
    const updated: Report = { ...report, approval_state: 'approved', approval };
    setReport(updated);
    onReportChanged(updated);
    setShowApproval(false);
  }

  return <section className="director-review" aria-labelledby="review-heading">
    <header className="review-header"><div><h2 id="review-heading">Briefing review</h2><p>Report {report.id.slice(0, 8)} / {report.station}</p></div><button className="cancel-report" onClick={onClose}>Close review</button></header>
    {loadError && <p className="form-message" role="alert">Could not refresh this report. Close and reopen it to retry.</p>}
    <div className={`canonical-assessment verdict-${report.verdict}`} id="launch-status">
      <div><span>Launch verdict</span><strong>{report.verdict === 'no_go' ? 'NO_GO' : 'GO'}</strong><p>Based on submitted readings</p></div>
      <div className="assessment-findings">{report.violations.length ? <ul>{report.violations.map((violation, index) => <li key={index}>{violation.message}</li>)}</ul> : <p>All three launch readings meet the limits.</p>}<span>Briefing approval does not authorize launch.</span></div>
    </div>
    <div className={`report-priority priority-${report.effective_severity}`}>
      <div className="priority-description"><strong>{{ high: 'High priority', medium: 'Medium priority', low: 'Low priority' }[report.effective_severity]}</strong><span>{report.severity_provisional ? 'Provisional — awaiting classification' : `Subsystem: ${report.subsystem}`}</span></div>
      <div className="priority-deadline"><span>Brief by</span><time aria-label="Briefing deadline" dateTime={report.brief_by_at}>{dateLabel(report.brief_by_at)}</time></div>
    </div>
    <section className="original-report" aria-labelledby="original-heading"><h3 id="original-heading">Submitted report</h3><p className="report-author">{report.engineer_name} / {report.station}<time dateTime={report.created_at}>{dateLabel(report.created_at)}</time></p>
      <dl className="saved-readings"><div><dt>Wind</dt><dd>{report.wind_knots}<span> knots</span></dd></div><div><dt>Temperature</dt><dd>{report.temp_c}<span> °C</span></dd></div><div><dt>Fuel</dt><dd>{report.fuel_pct}<span> %</span></dd></div></dl>
      <p className="saved-note">{report.note}</p>
    </section>
    <section className="briefing-section" aria-labelledby="briefing-heading"><h3 id="briefing-heading">Flight Director briefing</h3>
      {selected ? <BriefingContent briefing={selected} /> : <p className="briefing-empty" role="status">{report.pipeline_status === 'failed' ? 'Processing did not finish. File a new report to retry; any saved drafts remain below.' : report.pipeline_status === 'completed' ? 'No briefing is available for approval.' : 'Analysis is in progress. The briefing will appear here when ready.'}</p>}
    </section>
    {report.briefings.some(item => item.id !== selected?.id) && <section className="briefing-history" aria-labelledby="history-heading"><h3 id="history-heading">Earlier drafts</h3>{report.briefings.filter(item => item.id !== selected?.id).map(item => <details key={item.id} open><summary>Draft {item.round_number}</summary><BriefingContent briefing={item} /></details>)}</section>}
    <section className="review-checks" aria-labelledby="checks-heading"><h3 id="checks-heading">Advisory findings</h3><ReportChecks report={report} /></section>
    <ExecutionTrace reportId={report.id} refreshToken={refreshToken} pipelineStatus={report.pipeline_status} approvalId={report.approval?.id} />
    <footer className="approval-bar"><div role="status">{report.approval ? <><strong>Approved by {report.approval.approved_by}</strong><time dateTime={report.approval.approved_at}>{dateLabel(report.approval.approved_at)}</time></> : <><strong>{report.approval_state === 'pending' ? 'Pending human approval' : 'Approval unavailable'}</strong><span>Evaluator status is advisory.</span></>}</div><button className="submit-report" disabled={!canApprove} onClick={() => setShowApproval(true)}>Approve briefing</button></footer>
    {showApproval && selected && <ApprovalDialog report={report} briefingId={selected.id} onApproved={approved} onClose={() => setShowApproval(false)} />}
  </section>;
}

function BriefingContent({ briefing }: { briefing: Briefing }) {
  return <div className="briefing-content"><div className="evaluation-heading"><span>Draft {briefing.round_number}</span><span className={`evaluation-status evaluation-${briefing.evaluation_status}`}>{evaluationLabels[briefing.evaluation_status]}</span></div><p className="briefing-summary">{briefing.summary}</p>
    {briefing.recommended_actions.length > 0 && <><h4>Recommended actions</h4><ul>{briefing.recommended_actions.map((action, index) => <li key={index}>{action}</li>)}</ul></>}
    {briefing.feedback.length > 0 && <div className="evaluation-feedback"><h4>Evaluator feedback</h4><ul>{briefing.feedback.map((feedback, index) => <li key={index}>{feedback}</li>)}</ul></div>}
  </div>;
}
