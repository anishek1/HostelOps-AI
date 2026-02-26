import { useAuth } from '../hooks/useAuth';

export default function StudentDashboard() {
    const { user, logout } = useAuth();
    return (
        <div style={{ padding: 32 }}>
            <h1>Student Dashboard</h1>
            <p>Welcome, {user?.name} (Room {user?.room_number})</p>
            <button onClick={logout}>Logout</button>
        </div>
    );
}
