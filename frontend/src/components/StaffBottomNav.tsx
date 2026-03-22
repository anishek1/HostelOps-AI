/**
 * components/StaffBottomNav.tsx — HostelOps AI
 * 3-tab bottom nav for staff roles. Tabs differ by role:
 *   laundry_man:                 Slots | Profile
 *   mess_secretary / mess_manager: Mess | Profile
 */

import { Link, useLocation } from 'react-router-dom';
import type { UserRole } from '../types/user';

interface NavTab {
    label: string;
    icon: string;
    to: string;
}

function getTabs(role: UserRole): NavTab[] {
    if (role === 'laundry_man') {
        return [
            { label: 'Slots',   icon: 'local_laundry_service', to: '/staff/laundry' },
            { label: 'Profile', icon: 'person',                  to: '/student/profile' },
        ];
    }
    // mess_secretary | mess_manager
    return [
        { label: 'Mess',    icon: 'restaurant_menu', to: '/staff/mess' },
        { label: 'Profile', icon: 'person',            to: '/student/profile' },
    ];
}

interface Props {
    role: UserRole;
}

export default function StaffBottomNav({ role }: Props) {
    const { pathname } = useLocation();
    const tabs = getTabs(role);

    return (
        <nav style={navStyle}>
            {tabs.map((tab) => {
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
