/**
 * components/StudentBottomNav.tsx — HostelOps AI
 * 5-tab bottom nav for student role. Dark mode with purple active state.
 */

import { Link, useLocation } from 'react-router-dom';
import { C } from '../lib/theme';

interface NavTab {
    label: string;
    icon: string;
    to: string;
}

const TABS: NavTab[] = [
    { label: 'Home',       icon: 'home',                  to: '/student' },
    { label: 'Complaints', icon: 'chat_bubble',            to: '/student/complaints' },
    { label: 'Laundry',   icon: 'local_laundry_service',  to: '/student/laundry' },
    { label: 'Mess',      icon: 'restaurant',              to: '/student/mess' },
    { label: 'Profile',   icon: 'person',                  to: '/student/profile' },
];

export default function StudentBottomNav() {
    const { pathname } = useLocation();

    return (
        <nav style={navStyle}>
            {TABS.map((tab) => {
                const active = pathname === tab.to || pathname.startsWith(tab.to + '/');
                return (
                    <Link key={tab.to} to={tab.to} style={linkStyle}>
                        <span
                            className="material-symbols-outlined"
                            style={{
                                fontSize: 22,
                                color: active ? C.primary : C.textMuted,
                                fontVariationSettings: active
                                    ? "'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24"
                                    : "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24",
                            }}
                        >
                            {tab.icon}
                        </span>
                        <span style={{ ...labelStyle, color: active ? C.primary : C.textMuted }}>
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
    background: C.bgSurface,
    borderTop: `1px solid ${C.border}`,
    borderRadius: '20px 20px 0 0',
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
