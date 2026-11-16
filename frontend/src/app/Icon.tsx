import type { ReactNode } from 'react';

type IconName = 'overview' | 'report' | 'shield' | 'refresh' | 'check' | 'guide' | 'lock';

export function Icon({ name, className = '' }: { name: IconName; className?: string }) {
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
