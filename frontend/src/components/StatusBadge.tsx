/**
 * components/StatusBadge.tsx — HostelOps AI
 * Pill badge for complaint statuses. Colors per DESIGN.md status badge table.
 */

interface StatusBadgeProps {
    status: string;
    className?: string;
}

type BadgeStyle = { background: string; color: string };

const STATUS_STYLES: Record<string, BadgeStyle> = {
    INTAKE:             { background: '#F0F0ED',                      color: '#6B6B80' },
    CLASSIFIED:         { background: 'rgba(70,71,211,0.08)',          color: '#3C3489' },
    AWAITING_APPROVAL:  { background: 'rgba(255,184,0,0.10)',          color: '#9E7600' },
    ASSIGNED:           { background: 'rgba(70,71,211,0.08)',          color: '#3C3489' },
    IN_PROGRESS:        { background: 'rgba(70,71,211,0.08)',          color: '#3C3489' },
    RESOLVED:           { background: 'rgba(22,160,133,0.08)',         color: '#0F6E56' },
    REOPENED:           { background: 'rgba(255,184,0,0.10)',          color: '#9E7600' },
    ESCALATED:          { background: 'rgba(232,59,42,0.08)',          color: '#C12E20' },
};

const FALLBACK: BadgeStyle = { background: '#F0F0ED', color: '#6B6B80' };

export default function StatusBadge({ status, className = '' }: StatusBadgeProps) {
    const style = STATUS_STYLES[status.toUpperCase()] ?? FALLBACK;

    return (
        <span
            className={className}
            style={{
                display: 'inline-block',
                padding: '3px 10px',
                borderRadius: 999,
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                background: style.background,
                color: style.color,
                whiteSpace: 'nowrap',
            }}
        >
            {status.replace(/_/g, ' ')}
        </span>
    );
}
