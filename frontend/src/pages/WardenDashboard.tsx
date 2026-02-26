import { useAuth } from '../hooks/useAuth';

export default function WardenDashboard() {
    const { user, logout } = useAuth();
    return (
        <div style={{ padding: 32 }}>
            <h1>Warden Dashboard</h1>
            <p>Welcome, {user?.name} ({user?.role})</p>
            <button onClick={logout}>Logout</button>
        </div>
    );
}
