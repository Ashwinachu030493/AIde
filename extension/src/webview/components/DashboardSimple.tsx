import React, { useState, useEffect } from 'react';

interface DashboardData {
    timestamp: string;
    health: {
        score: number;
        breakdown: {
            code_quality: number;
            coverage: number;
            freshness: number;
        };
    };
    ingestion: {
        total_files: number;
        indexed_files: number;
        error_files: number;
        total_chunks: number;
    };
    audit: {
        last_run: string | null;
        total_issues: number;
        critical_issues: number;
        health_score: number;
        open_issues: number;
    };
    usage: {
        today: {
            tokens: number;
            cost_usd: number;
            requests: number;
        };
        total: {
            tokens: number;
            cost_usd: number;
            requests: number;
        };
    };
    activity: Array<{
        type: string;
        timestamp: string;
        description: string;
        details: string;
    }>;
    quick_actions: Array<{
        id: string;
        label: string;
        description: string;
        command: string;
    }>;
}

interface DashboardProps {
    projectId: string;
    onNavigate: (view: string) => void;
}

export const DashboardSimple: React.FC<DashboardProps> = ({ projectId, onNavigate }) => {
    const [data, setData] = useState<DashboardData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<string>('');

    const loadDashboard = async () => {
        try {
            const response = await fetch(`http://localhost:8000/dashboard/project/${projectId}/overview`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            setData(result);
            setLastUpdated(new Date().toLocaleTimeString());
            setError(null);
        } catch (err: any) {
            setError(`Failed to load: ${err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadDashboard();
        const interval = setInterval(loadDashboard, 5000);
        return () => clearInterval(interval);
    }, [projectId]);

    const getHealthColor = (score: number) => {
        if (score >= 80) return '#4caf50';
        if (score >= 60) return '#ff9800';
        return '#f44336';
    };

    if (isLoading && !data) {
        return <div style={{ padding: '20px', textAlign: 'center' }}>Loading dashboard...</div>;
    }

    if (error) {
        return (
            <div style={{ padding: '20px' }}>
                <h3>Dashboard Error</h3>
                <p>{error}</p>
                <button onClick={loadDashboard}>Retry</button>
            </div>
        );
    }

    return (
        <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2 style={{ margin: 0 }}>Project Dashboard</h2>
                <span style={{ fontSize: '0.9em', opacity: 0.7 }}>Updated: {lastUpdated}</span>
            </div>

            {/* Health Score */}
            <div style={{
                backgroundColor: 'var(--vscode-editor-background, #1e1e1e)',
                border: `2px solid ${getHealthColor(data?.health?.score || 0)}`,
                borderRadius: '8px',
                padding: '20px',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '20px'
            }}>
                <div style={{ fontSize: '48px', fontWeight: 'bold', color: getHealthColor(data?.health?.score || 0) }}>
                    {data?.health?.score || 0}
                </div>
                <div>
                    <div style={{ fontSize: '18px', fontWeight: 'bold' }}>Overall Health</div>
                    <div style={{ opacity: 0.7 }}>Quality: {data?.health?.breakdown?.code_quality || 0} | Coverage: {data?.health?.breakdown?.coverage || 0}%</div>
                </div>
            </div>

            {/* Stats Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px', marginBottom: '25px' }}>
                <div style={{ backgroundColor: 'var(--vscode-editor-inactiveSelectionBackground, #333)', padding: '15px', borderRadius: '6px' }}>
                    <h4 style={{ margin: '0 0 10px 0' }}>Files Indexed</h4>
                    <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                        {data?.ingestion?.indexed_files || 0} / {data?.ingestion?.total_files || 0}
                    </div>
                    <p style={{ margin: '5px 0 0 0', opacity: 0.7 }}>{data?.ingestion?.total_chunks || 0} chunks</p>
                </div>

                <div style={{ backgroundColor: 'var(--vscode-editor-inactiveSelectionBackground, #333)', padding: '15px', borderRadius: '6px' }}>
                    <h4 style={{ margin: '0 0 10px 0' }}>Audit Issues</h4>
                    <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{data?.audit?.open_issues || 0}</div>
                    <p style={{ margin: '5px 0 0 0', color: (data?.audit?.critical_issues || 0) > 0 ? '#f44336' : '#4caf50' }}>
                        {data?.audit?.critical_issues || 0} critical
                    </p>
                </div>

                <div style={{ backgroundColor: 'var(--vscode-editor-inactiveSelectionBackground, #333)', padding: '15px', borderRadius: '6px' }}>
                    <h4 style={{ margin: '0 0 10px 0' }}>AI Usage Today</h4>
                    <div style={{ fontSize: '24px', fontWeight: 'bold' }}>${(data?.usage?.today?.cost_usd || 0).toFixed(4)}</div>
                    <p style={{ margin: '5px 0 0 0', opacity: 0.7 }}>{(data?.usage?.today?.tokens || 0).toLocaleString()} tokens</p>
                </div>
            </div>

            {/* Quick Actions */}
            <h3>Quick Actions</h3>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '25px', flexWrap: 'wrap' }}>
                <button onClick={() => onNavigate('chat')} style={{ padding: '10px 20px', cursor: 'pointer' }}>Ask AI</button>
                <button onClick={() => onNavigate('audit')} style={{ padding: '10px 20px', cursor: 'pointer' }}>Run Audit</button>
                <button onClick={() => onNavigate('settings')} style={{ padding: '10px 20px', cursor: 'pointer' }}>Settings</button>
            </div>

            {/* Recent Activity */}
            <h3>Recent Activity</h3>
            <div style={{ backgroundColor: 'var(--vscode-editor-inactiveSelectionBackground, #333)', borderRadius: '6px' }}>
                {data?.activity && data.activity.length > 0 ? (
                    data.activity.slice(0, 5).map((item, index) => (
                        <div key={index} style={{
                            padding: '12px',
                            borderBottom: index < 4 ? '1px solid var(--vscode-panel-border, #444)' : 'none',
                            display: 'flex',
                            gap: '15px'
                        }}>
                            <span>{item.type === 'llm_usage' ? '🤖' : '🔍'}</span>
                            <div style={{ flex: 1 }}>
                                <div>{item.description}</div>
                                <div style={{ opacity: 0.7, fontSize: '0.9em' }}>{item.details}</div>
                            </div>
                            <div style={{ opacity: 0.5, fontSize: '0.8em' }}>
                                {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                        </div>
                    ))
                ) : (
                    <div style={{ padding: '20px', textAlign: 'center', opacity: 0.7 }}>No recent activity</div>
                )}
            </div>
        </div>
    );
};
