import React, { useState, useEffect } from 'react';
import { vsCodeButton, provideVSCodeDesignSystem } from "@vscode/webview-ui-toolkit";

// Register components
provideVSCodeDesignSystem().register(vsCodeButton());

interface Violation {
    rule_id: string;
    rule_name: string;
    severity: string;
    file_path: string;
    line_number: number;
    description: string;
}

interface AuditRun {
    id: number;
    status: string;
    health_score: number;
    total_issues: number;
    critical_issues: number;
    high_issues: number;
    started_at: string;
}

interface AuditSummary {
    total_files: number;
    files_with_issues: number;
    total_violations: number;
    critical_count: number;
    warning_count: number;
    info_count: number;
}

export const AuditPanel: React.FC = () => {
    const [path, setPath] = useState('f:/AIde');
    const [projectId, setProjectId] = useState('aide_local');
    const [isLoading, setIsLoading] = useState(false);
    const [runs, setRuns] = useState<AuditRun[]>([]);

    // Auto-load history on mount
    useEffect(() => {
        if (projectId) {
            fetchHistory();
        }
    }, [projectId]);

    const fetchHistory = async () => {
        try {
            const res = await fetch(`http://localhost:8000/auditor/project/${projectId}/runs`);
            if (res.ok) {
                const data = await res.json();
                setRuns(data.runs || []);
            }
        } catch (e) {
            console.error("Failed to fetch history:", e);
        }
    };

    const scanProject = async () => {
        setIsLoading(true);
        try {
            // Start persistent audit
            const res = await fetch(`http://localhost:8000/auditor/project/${projectId}/persistent?project_path=${encodeURIComponent(path)}`, {
                method: 'POST'
            });

            if (res.ok) {
                // Poll for updates or just refresh history after a delay
                // simple polling for demo
                setTimeout(fetchHistory, 2000);
                setTimeout(fetchHistory, 5000);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ padding: '20px' }}>
            <h2>Code Auditor (Persistent)</h2>

            <div style={{ marginBottom: '20px', borderBottom: '1px solid #ccc', paddingBottom: '10px' }}>
                <h3>Project Config</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '10px' }}>
                    <input
                        type="text"
                        value={path}
                        onChange={(e) => setPath(e.target.value)}
                        style={{ padding: '5px' }}
                        placeholder="Project Path"
                    />
                    <input
                        type="text"
                        value={projectId}
                        onChange={(e) => setProjectId(e.target.value)}
                        style={{ padding: '5px' }}
                        placeholder="Project ID (e.g. my-app)"
                    />
                    {/* @ts-ignore */}
                    <vscode-button onClick={scanProject}>Start Audit Run</vscode-button>
                </div>

                {isLoading && <div>🚀 Audit started in background...</div>}
            </div>

            <div>
                <h3>Audit History</h3>
                {runs.length === 0 ? (
                    <p>No audit runs found for this project ID.</p>
                ) : (
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ textAlign: 'left', borderBottom: '2px solid #333' }}>
                                <th>Date</th>
                                <th>Status</th>
                                <th>Health</th>
                                <th>Critical</th>
                                <th>Issues</th>
                            </tr>
                        </thead>
                        <tbody>
                            {runs.map((run) => (
                                <tr key={run.id} style={{ borderBottom: '1px solid #eee' }}>
                                    <td style={{ padding: '8px 0' }}>{new Date(run.started_at).toLocaleTimeString()}</td>
                                    <td>{run.status}</td>
                                    <td style={{
                                        color: run.health_score > 80 ? 'green' : run.health_score > 50 ? 'orange' : 'red',
                                        fontWeight: 'bold'
                                    }}>{run.health_score}%</td>
                                    <td style={{ color: run.critical_issues > 0 ? 'red' : 'inherit' }}>{run.critical_issues}</td>
                                    <td>{run.total_issues}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};
