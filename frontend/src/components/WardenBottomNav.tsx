/**
 * components/WardenBottomNav.tsx — HostelOps AI
 * 5-tab bottom nav for warden roles (assistant_warden, warden, chief_warden).
 */

import { Link, useLocation } from 'react-router-dom';

interface NavTab {
    label: string;
    icon: string;
    to: string;
    matchPrefix?: string;
}

const TABS: NavTab[] = [
    { label: 'Dashboard', icon: 'bar_chart',     to: '/warden',                    matchPrefix: '/warden' },
    { label: 'Approvals', icon: 'check_circle',  to: '/warden/approval-queue' },
    { label: 'Students',  icon: 'people',         to: '/warden/registrations' },
    { label: 'Settings',  icon: 'settings',       to: '/warden/settings' },
    { label: 'Profile',   icon: 'person',          to: '/student/profile' },
];

export default function WardenBottomNav() {
    const { pathname } = useLocation();

    function isActive(tab: NavTab): boolean {
        if (tab.to === '/warden') {
            // Only exact match for dashboard to avoid matching /warden/approval-queue etc.
            return pathname === '/warden';
        }
        return pathname === tab.to || pathname.startsWith(tab.to + '/');
    }

    return (
        <nav style={navStyle}>
            {TABS.map((tab) => {
                const active = isActive(tab);
                return (
                    <Link key={tab.to} to={tab.to} style={linkStyle}>
                        <span
                            className="material-symbols-outlined"
                            style={{
                                fontSize: 22,
                                color: active ? '#4647D3' : '#C4C4D4',
                                fontVariationSettings: active
                                    ? "'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24"
                                    : "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24",
                            }}
                        >
                            {tab.icon}
                        </span>
                        <span style={{ ...labelStyle, color: active ? '#4647D3' : '#C4C4D4' }}>
                            {tab.label}
                        </span>
                    </Link>
                );
            })}
        </nav>
    );
}

const navStyle: React.CSSProperties = {
    position: 'fixed',
    bottom: 0,
    left: '50%',
    transform: 'translateX(-50%)',
    width: '100%',
    maxWidth: 430,
    height: 64,
    display: 'flex',
    alignItems: 'stretch',
    background: 'rgba(255,245,238,0.80)',
    backdropFilter: 'blur(12px)',
    WebkitBackdropFilter: 'blur(12px)',
    borderTop: '1px solid rgba(0,0,0,0.06)',
    zIndex: 50,
};

const linkStyle: React.CSSProperties = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
    textDecoration: 'none',
    padding: '6px 0',
};

const labelStyle: React.CSSProperties = {
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: '0.02em',
    lineHeight: 1,
};
