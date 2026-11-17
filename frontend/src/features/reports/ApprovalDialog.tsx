import { useEffect, useRef, useState, type FormEvent } from 'react';
import { approveBriefing, type Approval, type Report } from '../../api/reports';

export function ApprovalDialog({ report, briefingId, onApproved, onClose }: {
  report: Report; briefingId: string; onApproved: (approval: Approval) => void; onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const usernameInput = useRef<HTMLInputElement>(null);
  const inFlight = useRef(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [acknowledged, setAcknowledged] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const needsReview = report.requires_review || report.review_reasons.length > 0;

  useEffect(() => {
    const previouslyFocused = document.activeElement;
    const element = dialog.current!;
    if (typeof element.showModal === 'function') element.showModal();
    else element.setAttribute('open', '');
    usernameInput.current?.focus();
    return () => { if (previouslyFocused instanceof HTMLElement) previouslyFocused.focus(); };
  }, []);

  async function confirm(event: FormEvent) {
    event.preventDefault();
    if (inFlight.current || !username || !password || (needsReview && !acknowledged)) return;
    inFlight.current = true;
    setPending(true);
    setError('');
    try {
      const approval = await approveBriefing(report.id, briefingId, acknowledged, username, password);
      onApproved(approval);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Approval was not confirmed. Reopen the report to check its status.');
    } finally {
      setUsername('');
      setPassword('');
      setPending(false);
      inFlight.current = false;
    }
  }

  return <dialog className="approval-dialog" ref={dialog} aria-labelledby="approval-title" aria-describedby="approval-boundary" onCancel={event => { event.preventDefault(); if (!inFlight.current) onClose(); }}>
    <form onSubmit={event => void confirm(event)}>
      <h2 id="approval-title">Approve briefing</h2><p id="approval-boundary" className="approval-boundary">Approving this briefing does not authorize launch.</p>
      <p className="approval-context">Confirm your review of the selected briefing for {report.station}, filed by {report.engineer_name}.</p>
      {needsReview && <label className="review-acknowledgment"><input type="checkbox" checked={acknowledged} disabled={pending} onChange={event => setAcknowledged(event.target.checked)} /><span>I have reviewed the flagged findings</span></label>}
      <div className="approval-credentials"><div className="report-field"><label htmlFor="director-username">Director username</label><input id="director-username" ref={usernameInput} autoComplete="off" required value={username} disabled={pending} onChange={event => setUsername(event.target.value)} /></div><div className="report-field"><label htmlFor="director-password">Director password</label><input id="director-password" type="password" autoComplete="off" required value={password} disabled={pending} onChange={event => setPassword(event.target.value)} /></div></div>
      {error && <p className="form-message" role="alert">{error}</p>}
      <div className="form-actions"><button className="cancel-report" type="button" disabled={pending} onClick={onClose}>Cancel</button><button className="submit-report" type="submit" disabled={pending || !username || !password || (needsReview && !acknowledged)}>{pending ? 'Confirming approval…' : 'Confirm briefing approval'}</button></div>
    </form>
  </dialog>;
}
