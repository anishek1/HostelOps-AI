/**
 * components/StudentBottomNav.tsx — HostelOps AI
 * 5-tab bottom nav for student role.
 * Design: frosted glass, indigo active, #C4C4D4 inactive. Icons from Material Symbols.
 */

import { Link, useLocation } from 'react-router-dom';

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
    left: 0,
    right: 0,
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
