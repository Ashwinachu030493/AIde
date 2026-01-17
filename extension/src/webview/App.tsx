import React, { useState } from 'react';
import { ChatWindow } from './components/ChatWindow';
import { SettingsPanel } from './components/SettingsPanel';
import { AuditPanel } from './components/AuditPanel';
import { DashboardSimple } from './components/DashboardSimple';
import { vsCodeButton, provideVSCodeDesignSystem } from "@vscode/webview-ui-toolkit";

provideVSCodeDesignSystem().register(vsCodeButton());

type View = 'dashboard' | 'chat' | 'settings' | 'audit';

const App: React.FC = () => {
    const [view, setView] = useState<View>('dashboard');
    const projectId = 'aide_local'; // Default project ID

    return (
        <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
            <div style={{
                padding: '10px',
                borderBottom: '1px solid var(--vscode-panel-border)',
                display: 'flex',
                gap: '8px'
            }}>
                {/* @ts-ignore */}
                <vscode-button
                    appearance={view === 'dashboard' ? 'primary' : 'secondary'}
                    onClick={() => setView('dashboard')}
                >
                    Home
                </vscode-button>
                {/* @ts-ignore */}
                <vscode-button
                    appearance={view === 'chat' ? 'primary' : 'secondary'}
                    onClick={() => setView('chat')}
                >
                    Chat
                </vscode-button>
                {/* @ts-ignore */}
                <vscode-button
                    appearance={view === 'audit' ? 'primary' : 'secondary'}
                    onClick={() => setView('audit')}
                >
                    Audit
                </vscode-button>
                {/* @ts-ignore */}
                <vscode-button
                    appearance={view === 'settings' ? 'primary' : 'secondary'}
                    onClick={() => setView('settings')}
                >
                    Settings
                </vscode-button>
            </div>

            <div style={{ flex: 1, overflow: 'auto' }}>
                {view === 'dashboard' && <DashboardSimple projectId={projectId} onNavigate={(v) => setView(v as View)} />}
                {view === 'chat' && <ChatWindow />}
                {view === 'audit' && <AuditPanel />}
                {view === 'settings' && <SettingsPanel />}
            </div>
        </div>
    );
};

export default App;
