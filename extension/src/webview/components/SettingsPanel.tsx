import React, { useState, useEffect } from 'react';
import './SettingsPanel.css';

interface SettingsState {
    openaiKey: string;
    anthropicKey: string;
    groqKey: string;
    huggingfaceKey: string;
    githubToken: string;
    defaultModel: string;
    theme: string;
    autoIngest: boolean;
    maxFileSize: number;
}

const MODELS = [
    { value: 'gpt-4-turbo-preview', label: 'GPT-4 Turbo' },
    { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' },
    { value: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B (Groq)' },
    { value: 'huggingface/meta-llama/Meta-Llama-3-8B-Instruct', label: 'Llama 3 8B (HuggingFace)' }
];

export const SettingsPanel: React.FC = () => {
    const [settings, setSettings] = useState<SettingsState>({
        openaiKey: '',
        anthropicKey: '',
        groqKey: '',
        huggingfaceKey: '',
        githubToken: '',
        defaultModel: 'gpt-4-turbo-preview',
        theme: 'system',
        autoIngest: true,
        maxFileSize: 10
    });

    const [isLoading, setIsLoading] = useState(true);
    const [saveStatus, setSaveStatus] = useState<string | null>(null);
    const [providers, setProviders] = useState<Record<string, boolean>>({});

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const response = await fetch('http://localhost:8000/settings/');
            const data = await response.json();

            if (data.has_settings) {
                setSettings(prev => ({
                    ...prev,
                    defaultModel: data.preferences.default_model || prev.defaultModel,
                    theme: data.preferences.theme || prev.theme,
                    autoIngest: data.preferences.auto_ingest ?? prev.autoIngest,
                    maxFileSize: data.preferences.max_file_size_mb || prev.maxFileSize
                }));
                setProviders(data.providers_configured || {});
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
            setSaveStatus('Error loading settings');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async () => {
        setSaveStatus('Saving...');
        try {
            // Save keys one by one if changed (simple approach)
            const keysToSave = [
                { p: 'openai', k: settings.openaiKey },
                { p: 'anthropic', k: settings.anthropicKey },
                { p: 'groq', k: settings.groqKey },
                { p: 'huggingface', k: settings.huggingfaceKey },
                { p: 'github', k: settings.githubToken }
            ];

            for (const { p, k } of keysToSave) {
                if (k) {
                    await fetch('http://localhost:8000/settings/api-keys', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ provider: p, api_key: k })
                    });
                }
            }

            // Save prefs
            await fetch('http://localhost:8000/settings/preferences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    default_model: settings.defaultModel,
                    theme: settings.theme,
                    auto_ingest: settings.autoIngest,
                    max_file_size_mb: settings.maxFileSize
                })
            });

            setSaveStatus('Saved successfully!');
            setTimeout(() => setSaveStatus(null), 3000);
            loadSettings(); // Reload to update "configured" status

        } catch (e) {
            setSaveStatus(`Save failed: ${e}`);
        }
    };

    if (isLoading) return <div className="p-4">Loading settings...</div>;

    return (
        <div className="settings-panel p-4 max-w-2xl mx-auto">
            <h2 className="text-xl font-bold mb-4">AIde Settings</h2>

            {saveStatus && (
                <div className={`mb-4 p-2 rounded ${saveStatus.includes('failed') ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                    {saveStatus}
                </div>
            )}

            <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">API Keys</h3>
                <p className="text-sm text-gray-500 mb-4">Keys are encrypted locally and never shown again.</p>

                <div className="space-y-3">
                    {['openai', 'anthropic', 'groq', 'huggingface', 'github'].map(provider => (
                        <div key={provider} className="flex flex-col">
                            <label className="capitalize text-sm font-medium mb-1">
                                {provider} {providers[provider] && <span className="text-green-600 ml-2">✓ Configured</span>}
                            </label>
                            <input
                                type="password"
                                className="vs-input p-2 border rounded bg-transparent"
                                placeholder={providers[provider] ? "•••••••• (Enter new to replace)" : `Enter ${provider} key`}
                                value={(settings as any)[`${provider}Key`]}
                                onChange={e => setSettings({ ...settings, [`${provider}Key`]: e.target.value })}
                            />
                        </div>
                    ))}
                </div>
            </div>

            <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">Preferences</h3>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Default Model</label>
                        <select
                            className="vs-select w-full p-2 border rounded bg-transparent"
                            value={settings.defaultModel}
                            onChange={e => setSettings({ ...settings, defaultModel: e.target.value })}
                        >
                            {MODELS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                        </select>
                    </div>

                    <div className="flex items-center">
                        <input
                            type="checkbox"
                            id="autoIngest"
                            checked={settings.autoIngest}
                            onChange={e => setSettings({ ...settings, autoIngest: e.target.checked })}
                            className="mr-2"
                        />
                        <label htmlFor="autoIngest">Auto-ingest files on save</label>
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">Max File Size (MB)</label>
                        <input
                            type="number"
                            className="vs-input p-2 border rounded bg-transparent w-24"
                            value={settings.maxFileSize}
                            onChange={e => setSettings({ ...settings, maxFileSize: parseInt(e.target.value) })}
                        />
                    </div>
                </div>
            </div>

            <div className="flex gap-2">
                <button
                    onClick={handleSave}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                    Save Settings
                </button>
                <button
                    onClick={loadSettings}
                    className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300"
                >
                    Reload
                </button>
            </div>
        </div>
    );
};
