/**
 * components/SkeletonCard.tsx — HostelOps AI
 * Warm shimmer loading placeholder. Always use this — never spinners.
 */

interface SkeletonCardProps {
    lines?: number;
    className?: string;
}

function SkeletonLine({ width = '100%', height = 14 }: { width?: string; height?: number }) {
    return (
        <div
            className="skeleton-shimmer"
            style={{
                width,
                height,
                borderRadius: 8,
                background: '#F5F3EF',
                flexShrink: 0,
            }}
        />
    );
}

export default function SkeletonCard({ lines = 3, className = '' }: SkeletonCardProps) {
    return (
        <>
            <style>{`
                @keyframes skeleton-sweep {
                    0%   { background-position: -400px 0; }
                    100% { background-position: 400px 0; }
                }
                .skeleton-shimmer {
                    background: linear-gradient(
                        90deg,
                        #F5F3EF 25%,
                        #EDE9E4 50%,
                        #F5F3EF 75%
                    ) no-repeat;
                    background-size: 800px 100%;
                    animation: skeleton-sweep 1.4s ease-in-out infinite;
                }
            `}</style>
            <div
                className={className}
                style={{
                    background: '#FFFFFF',
                    borderRadius: 16,
                    padding: '16px 20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 10,
                }}
            >
                <SkeletonLine width="60%" height={16} />
                {Array.from({ length: lines - 1 }).map((_, i) => (
                    <SkeletonLine
                        key={i}
                        width={i === lines - 2 ? '40%' : '100%'}
                        height={12}
                    />
                ))}
            </div>
        </>
    );
}
