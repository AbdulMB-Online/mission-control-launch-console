import { useEffect, useState, type ReactNode } from 'react';

type Connection = { status: 'loading' | 'online' | 'error'; provider?: 'fake' | 'openai' };
type IconName = 'overview' | 'report' | 'shield' | 'refresh' | 'check' | 'guide' | 'lock';

function Icon({ name, className = '' }: { name: IconName; className?: string }) {
  const shapes: Record<IconName, ReactNode> = {
    overview: <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>,
    report: <><path d="M5 3h9l4 4v14H5V3Z" /><path d="M14 3v5h4M8 12h7M8 16h5" /></>,
    shield: <><path d="m12 3 8 3v6c0 4-4 7-8 9-4-2-8-5-8-9V6l8-3Z" /><path d="M9 12h6" /></>,
    refresh: <><path d="M20 7v5h-5M4 17v-5h5" /><path d="M6.1 6.1A8 8 0 0 1 19 9M5 15a8 8 0 0 0 12.9 2.9" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    guide: <><path d="M3 5h7l2 2 2-2h7v15h-7l-2 1-2-1H3V5ZM12 7v14" /><path d="M6 10h3M6 14h3M15 10h3M15 14h3" /></>,
    lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3" /></>,
  };
  return <svg className={`icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{shapes[name]}</svg>;
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

export default function App() {
  const [connection, setConnection] = useState<Connection>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setConnection({ status: 'loading' });
    async function check() {
      try {
        const response = await fetch('/healthz', { signal: controller.signal });
        if (!response.ok) throw new Error('Backend unavailable');
        const health = await response.json();
        if (health.status !== 'ok' || health.service !== 'mission-control' || !['fake', 'openai'].includes(health.provider)) {
          throw new Error('Invalid readiness response');
        }
        if (!controller.signal.aborted) setConnection({ status: 'online', provider: health.provider });
      } catch {
        if (!controller.signal.aborted) setConnection({ status: 'error' });
      }
    }
    void check();
    return () => controller.abort();
  }, [attempt]);

  const online = connection.status === 'online';
  const failed = connection.status === 'error';
  const refresh = () => setAttempt(value => value + 1);
  const statusText = online ? 'System online' : failed ? 'Connection unavailable' : 'Checking connection';

  return (
    <div className="mission-shell">
      <a className="skip-link" href="#mission-overview">Skip to workspace</a>
      <aside className="command-rail" aria-label="Console navigation">
        <a className="brand" href="#mission-overview" aria-label="Meridian launch services home">
          <svg viewBox="0 0 38 38" fill="none" aria-hidden="true"><path d="M5 29V12l10 12 9-12v17M31 8v21" stroke="currentColor" strokeWidth="2.6" /><path d="m24 6 7-3 3 7" stroke="#8daaff" strokeWidth="2.6" /></svg>
          <span>meridian<span className="brand-description">Launch services</span></span>
        </a>
        <div className="workspace-identity"><span className="workspace-symbol">M</span><span>Launch operations<small>Mission workspace</small></span></div>
        <nav aria-label="Workspace sections">
          <a className="rail-link selected" href="#mission-overview" aria-current="page"><Icon name="overview" />Overview<span className="selected-mark" /></a>
          <a className="rail-link" href="#report-workspace"><Icon name="report" />Report workspace</a>
          <a className="rail-link" href="#launch-status"><Icon name="shield" />Launch assessment</a>
          <a className="rail-link" href="#workflow-guide"><Icon name="guide" />Workflow guide</a>
        </nav>
        <div className="rail-principle"><div className="principle-orbit" aria-hidden="true"><span /></div><p>Precision before<br />permission.</p><span>Every briefing needs a human decision.</span></div>
        <div className="rail-workspace"><span className="local-dot" /><span>Local workspace</span><Icon name="lock" /></div>
      </aside>

      <div className="mission-main">
        <header className="workspace-bar">
          <div className="breadcrumb"><Icon name="overview" /><span>Launch operations</span><span className="breadcrumb-divider">/</span><strong>Overview</strong></div>
          <div className={`environment-badge ${connection.provider === 'fake' ? 'simulation' : ''}`}><span />{connection.provider === 'fake' ? 'Simulated mode' : connection.provider === 'openai' ? 'OpenAI configured' : 'Checking mode'}</div>
        </header>

        <main id="mission-overview" className="mission-content">
          <div className="page-title-row">
            <div><div className="page-context"><span className="context-line" />Preflight workspace</div><h1>Mission Control</h1><p className="page-description">Reports, briefings, and the evidence behind every decision.</p></div>
            <button className="refresh-button" aria-label="Refresh connection" onClick={refresh}><Icon name="refresh" /><span>Refresh</span></button>
          </div>
          <div className="operational-note"><Icon name="shield" /><p>Launch limits are fixed. Briefings always need the Flight Director’s approval.</p><span className="note-end">Human authority</span></div>

          <div className="workspace-grid">
            <section className="report-desk" id="report-workspace" aria-labelledby="report-heading">
              <header className="desk-header"><div className="desk-title"><span className="section-icon"><Icon name="report" /></span><div><h2 id="report-heading">Report workspace</h2><p>Engineer reports and drafted briefings</p></div></div><span className="pending-label"><span />Filing pending</span></header>
              <div className="desk-body">
                <div className="desk-grid" aria-hidden="true" /><ReportIllustration />
                <div className="empty-copy"><h3>Engineer reports will appear here</h3><p>Readings and anomaly notes come together in a focused review queue, ready for the Flight Director.</p></div>
                <div className="filing-notice"><Icon name="report" /><span>Report filing is the next milestone.</span></div>
              </div>
              <footer className="desk-footer"><span><span className="quiet-dot" />Waiting for report filing</span><span>Every report stays on record</span></footer>
            </section>

            <aside className="readiness-column" aria-label="Operational readiness">
              <section className="assessment-panel" id="launch-status" aria-labelledby="assessment-heading">
                <header><h2 id="assessment-heading">Launch assessment</h2><Icon name="shield" /></header>
                <div className="assessment-status"><span />Awaiting readings</div>
                <p className="verdict-placeholder">Not assessed</p>
                <p className="assessment-explanation">A launch verdict requires wind, temperature, and fuel readings.</p>
                <div className="assessment-boundary"><Icon name="lock" /><span>Briefing approval does not authorize launch.</span></div>
              </section>
              <section className={`connection-panel ${failed ? 'connection-error' : ''}`} aria-labelledby="connection-heading">
                <div className="connection-title"><span className={`connection-indicator ${connection.status}`} /><h2 id="connection-heading" aria-live="polite">{statusText}</h2></div>
                <p className="connection-description">{online ? 'The console and persistent storage are ready.' : failed ? 'Check the running services, then retry the connection.' : 'Checking the console and persistent storage.'}</p>
                <dl className="connection-facts">
                  <div><dt>API connection</dt><dd className={online ? 'fact-ready' : ''}>{online && <Icon name="check" />}{online ? 'Connected' : failed ? 'Unavailable' : 'Checking'}</dd></div>
                  <div><dt>Storage</dt><dd className={online ? 'fact-ready' : ''}>{online && <Icon name="check" />}{online ? 'Ready' : failed ? 'Unknown' : 'Checking'}</dd></div>
                  <div><dt>Analysis mode</dt><dd>{connection.provider === 'fake' ? 'Simulated' : connection.provider === 'openai' ? 'Configured' : 'Unknown'}</dd></div>
                </dl>
                {failed && <button className="retry-button" onClick={refresh}><Icon name="refresh" />Retry connection</button>}
              </section>
            </aside>
          </div>

          <section className="workflow-guide" id="workflow-guide" aria-labelledby="workflow-heading">
            <div className="workflow-intro"><span className="guide-symbol"><Icon name="guide" /></span><h2 id="workflow-heading">One report.<br /><span>A considered decision.</span></h2><p>How the console works</p></div>
            <ol className="workflow-steps">
              <li><div className="step-heading"><span className="step-index">1</span><h3>File the anomaly</h3></div><p>The engineer adds three readings and the context behind them.</p></li>
              <li><div className="step-heading"><span className="step-index">2</span><h3>Review the briefing</h3></div><p>Fixed launch limits and advisory analysis inform a concise draft.</p></li>
              <li><div className="step-heading"><span className="step-index">3</span><h3>Make the call</h3></div><p>The Flight Director reviews the evidence and approves the briefing.</p></li>
            </ol>
          </section>
          <footer className="workspace-footer"><span>Meridian Launch Services</span><span><Icon name="lock" />Human approval. Every briefing.</span></footer>
        </main>
      </div>
    </div>
  );
}
