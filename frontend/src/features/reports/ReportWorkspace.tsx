import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchReports, type Report, type ReportPage } from '../../api/reports';
import { Icon } from '../../app/Icon';
import { ReportForm } from './ReportForm';
import { ReportChecks } from './ReportChecks';
import { DirectorReview } from './DirectorReview';

export function ReportWorkspace({ refreshToken, onTotalChange, onReviewChange }: { refreshToken: number; onTotalChange: (total: number) => void; onReviewChange?: (open: boolean) => void }) {
  const [page, setPage] = useState<ReportPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [filed, setFiled] = useState(false);
  const activeLoad = useRef<AbortController | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = page?.items.find(report => report.id === selectedId);
  const updateReport = useCallback((report: Report) => {
    setPage(current => current ? { ...current, items: current.items.map(item => item.id === report.id ? report : item) } : current);
  }, []);
  function selectReport(id: string | null) { setSelectedId(id); onReviewChange?.(id !== null); }

  useEffect(() => {
    const controller = new AbortController();
    activeLoad.current = controller;
    setLoading(true);
    setLoadError(false);
    fetchReports(controller.signal)
      .then(result => { if (!controller.signal.aborted) setPage(result); })
      .catch(() => { if (!controller.signal.aborted) setLoadError(true); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [refreshToken]);

  useEffect(() => { onTotalChange(page?.total ?? 0); }, [page, onTotalChange]);

  function saved(report: Report) {
    activeLoad.current?.abort();
    setLoading(false);
    setLoadError(false);
    setPage(current => ({
      items: [report, ...(current?.items ?? []).filter(item => item.id !== report.id)].slice(0, 20),
      total: (current?.total ?? 0) + (current?.items.some(item => item.id === report.id) ? 0 : 1),
      limit: 20, offset: 0,
    }));
    setShowForm(false);
    setFiled(true);
  }

  return (
    <section className="report-desk" id="report-workspace" aria-labelledby="report-heading">
      <header className="desk-header"><div className="desk-title"><span className="section-icon"><Icon name="report" /></span><div><h2 id="report-heading">Report workspace</h2><p>Engineer anomaly reports</p></div></div><button className="file-report" disabled={showForm} onClick={() => { setShowForm(true); setFiled(false); }}><span aria-hidden="true">+</span>File report</button></header>
      {filed && <div className="report-success" role="status"><Icon name="check" />Report filed</div>}
      {showForm && <ReportForm onFiled={saved} onCancel={() => setShowForm(false)} />}
      {loadError && <div className="report-load-error" role="alert">Could not load reports. Refresh the connection to try again.</div>}
      {loading && <p className="report-loading" role="status">Loading saved reports…</p>}
      {!showForm && !loading && !loadError && !page?.items.length && <div className="desk-body"><div className="desk-grid" aria-hidden="true" /><ReportIllustration /><div className="empty-copy"><h3>No reports filed yet</h3><p>File an anomaly with the readings and context your Flight Director needs.</p></div><div className="filing-notice"><Icon name="report" /><span>Reports are saved before they appear in the queue.</span></div></div>}
      {Boolean(page?.items.length) && <div className={selected ? 'director-workspace' : ''}><div className={`report-list ${selected ? 'compact-queue' : ''}`} aria-label="Saved reports">{page!.items.map(report => <article className={`saved-report ${selectedId === report.id ? 'selected-report' : ''}`} key={report.id}>
        <div className="saved-report-heading"><span className="station-badge">{report.station}</span><time dateTime={report.created_at}>{new Date(report.created_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' })} UTC</time></div>
        <h3>{report.engineer_name}</h3>
        {!selected && <>
        <div className={`report-priority priority-${report.effective_severity}`}>
          <div className="priority-description"><strong>{{ high: 'High priority', medium: 'Medium priority', low: 'Low priority' }[report.effective_severity]}</strong>
            {report.severity_provisional && <span>Provisional — awaiting classification</span>}
          </div>
          <div className="priority-deadline"><span>Brief by</span><time aria-label="Briefing deadline" dateTime={report.brief_by_at}>{new Date(report.brief_by_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'medium', timeZone: 'UTC' })} UTC</time></div>
        </div>
        <dl className="saved-readings"><div><dt>Wind</dt><dd>{report.wind_knots}<span> knots</span></dd></div><div><dt>Temperature</dt><dd>{report.temp_c}<span> °C</span></dd></div><div><dt>Fuel</dt><dd>{report.fuel_pct}<span> %</span></dd></div></dl>
        <p className="saved-note">{report.note}</p>
        <ReportChecks report={report} />
        </>}
        <span className="report-reference">Report {report.id.slice(0, 8)}</span>
        <button className="review-report" aria-pressed={selectedId === report.id} onClick={() => selectReport(report.id)}>Review report</button>
      </article>)}</div>
        {selected && <DirectorReview key={selected.id} initialReport={selected} refreshToken={refreshToken} onReportChanged={updateReport} onClose={() => selectReport(null)} />}
      </div>}
      <footer className="desk-footer"><span><span className="quiet-dot" />{page ? `${page.total} saved ${page.total === 1 ? 'report' : 'reports'}` : 'Persistent report storage'}</span><span>{page && page.total > 20 ? 'Showing latest 20' : 'Every report stays on record'}</span></footer>
    </section>
  );
}

function ReportIllustration() {
  return (
    <svg className="report-illustration" viewBox="0 0 560 210" fill="none" aria-hidden="true">
      <path className="flight-track" d="M-15 173C84 173 81 57 189 57h156c89 0 107-48 230-48" />
      <path className="flight-track secondary" d="M-15 194c101 0 120-72 192-72h188c90 0 91-72 210-72" />
      <circle cx="113" cy="105" r="22" className="range-ring" /><circle cx="113" cy="105" r="4" className="route-point" />
      <path d="M113 74v10m0 42v10m-31-31h10m42 0h10" className="range-cross" />
      <path d="m444 32 10 5-10 5-10-5 10-5Z" className="route-marker" />
      <rect x="220" y="39" width="132" height="146" rx="8" transform="rotate(10 220 39)" className="sheet rear" />
      <rect x="208" y="23" width="133" height="152" rx="8" transform="rotate(-9 208 23)" className="sheet middle" />
      <rect x="216" y="21" width="132" height="154" rx="8" className="sheet front" />
      <path d="M232 44h7m7 0h28" className="document-caption" /><path d="M232 68h77M232 82h94M232 96h64" className="document-line" />
      <rect x="232" y="116" width="100" height="36" rx="4" className="document-inset" />
      <path d="M242 128h38m-38 12h75" className="document-detail" />
      <circle cx="348" cy="174" r="17" className="document-badge" /><path d="M348 167v14m-7-7h14" className="badge-plus" />
      <circle cx="388" cy="102" r="3" className="route-point muted" />
      <path d="M180 39h7m-3.5-3.5v7M392 173h7m-3.5-3.5v7" className="range-cross" />
    </svg>
  );
}
