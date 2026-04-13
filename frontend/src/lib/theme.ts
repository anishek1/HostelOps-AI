/**
 * lib/theme.ts — HostelOps AI
 * Dark mode design system. All colors, semantic tokens, and shared styles.
 * Every page imports C (colors) from here — single source of truth.
 */

export const C = {
    // Backgrounds
    bg: '#0A0A0F',
    bgSurface: '#13121A',
    bgElevated: '#1C1B24',
    bgHover: '#232230',

    // Primary (Electric Purple)
    primary: '#7C5CFC',
    primaryMuted: '#6B4FDB',
    primaryLight: 'rgba(124,92,252,0.12)',
    primaryContainer: 'rgba(124,92,252,0.15)',

    // Accent (Mint)
    accent: '#00D4AA',
    accentLight: 'rgba(0,212,170,0.12)',

    // Semantic
    success: '#00D4AA',
    successLight: 'rgba(0,212,170,0.12)',
    danger: '#FF4D4F',
    dangerLight: 'rgba(255,77,79,0.12)',
    warning: '#FFB020',
    warningLight: 'rgba(255,176,32,0.12)',
    info: '#3B82F6',
    infoLight: 'rgba(59,130,246,0.12)',

    // Text
    textPrimary: '#F0F0F5',
    textSecondary: '#9B9BB0',
    textMuted: '#6B6B80',
    textDisabled: '#4A4A5A',

    // Input
    inputBg: '#1C1B24',

    // Amber (warning alias)
    amber: '#FFB020',
    amberLight: 'rgba(255,176,32,0.12)',

    // Borders
    border: 'rgba(255,255,255,0.06)',
    borderLight: 'rgba(255,255,255,0.10)',

    // Cards
    card: '#13121A',
    cardBorder: 'rgba(255,255,255,0.06)',
} as const;

/** Status chip styles for complaint status values */
export const STATUS_COLORS: Record<string, { bg: string; text: string; label: string }> = {
    INTAKE:            { bg: C.primaryLight,  text: C.primary,  label: 'Intake' },
    CLASSIFIED:        { bg: C.primaryLight,  text: C.primary,  label: 'Classified' },
    AWAITING_APPROVAL: { bg: C.warningLight,  text: C.warning,  label: 'Pending' },
    ASSIGNED:          { bg: C.infoLight,     text: C.info,     label: 'Assigned' },
    IN_PROGRESS:       { bg: C.infoLight,     text: C.info,     label: 'In Progress' },
    RESOLVED:          { bg: C.successLight,  text: C.success,  label: 'Resolved' },
    REOPENED:          { bg: C.warningLight,  text: C.warning,  label: 'Reopened' },
    ESCALATED:         { bg: C.dangerLight,   text: C.danger,   label: 'Escalated' },
};

/** Severity chip styles */
export const SEVERITY_COLORS: Record<string, { bg: string; text: string }> = {
    low:    { bg: C.successLight, text: C.success },
    medium: { bg: C.warningLight, text: C.warning },
    high:   { bg: C.dangerLight,  text: C.danger },
};

/** Category label styling */
export const CATEGORY_COLORS: Record<string, { bg: string; text: string }> = {
    mess:           { bg: C.warningLight,  text: C.warning },
    laundry:        { bg: C.accentLight,   text: C.accent },
    maintenance:    { bg: C.infoLight,     text: C.info },
    interpersonal:  { bg: C.dangerLight,   text: C.danger },
    critical:       { bg: C.dangerLight,   text: C.danger },
    uncategorised:  { bg: 'rgba(255,255,255,0.06)', text: C.textMuted },
};

/** Shared card style */
export const cardStyle: React.CSSProperties = {
    background: C.card,
    border: `1px solid ${C.cardBorder}`,
    borderRadius: 16,
    padding: '16px 18px',
};

/** Shared section title style */
export const sectionTitle: React.CSSProperties = {
    fontSize: 11,
    fontWeight: 700,
    color: C.textMuted,
    letterSpacing: '0.10em',
    textTransform: 'uppercase',
    margin: '0 0 12px',
};

/** Chip/badge style */
export function chipStyle(bg: string, text: string): React.CSSProperties {
    return {
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: '0.07em',
        textTransform: 'uppercase',
        color: text,
        background: bg,
        padding: '3px 8px',
        borderRadius: 999,
        whiteSpace: 'nowrap',
    };
}
