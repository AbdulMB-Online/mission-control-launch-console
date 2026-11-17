import { useEffect, useState } from 'react';
import { Icon } from './Icon';
import { ReportWorkspace } from '../features/reports/ReportWorkspace';

type Connection = { status: 'loading' | 'online' | 'error'; provider?: 'fake' | 'openai' };
export default function App() {
  const [connection, setConnection] = useState<Connection>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const [reportCount, setReportCount] = useState(0);
  const [reviewOpen, setReviewOpen] = useState(false);

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

          <div className={`workspace-grid ${reviewOpen ? 'review-layout' : ''}`}>
            <ReportWorkspace refreshToken={attempt} onTotalChange={setReportCount} onReviewChange={setReviewOpen} />

            {!reviewOpen && <aside className="readiness-column" aria-label="Operational readiness">
              <section className="assessment-panel" id="launch-status" aria-labelledby="assessment-heading">
                <header><h2 id="assessment-heading">Launch assessment</h2><Icon name="shield" /></header>
                <div className="assessment-status"><span />{reportCount ? 'Select a report' : 'Awaiting readings'}</div>
                <p className="verdict-placeholder">Not assessed</p>
                <p className="assessment-explanation">{reportCount ? 'Open a report to inspect its launch verdict and briefing.' : 'A launch verdict requires wind, temperature, and fuel readings.'}</p>
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
            </aside>}
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
