import React, { useState } from 'react';

interface Props {
    code: string;
    language?: string;
}

export function CodeBlock({ code, language = 'plaintext' }: Props) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(code);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    return (
        <div className="code-block">
            <div className="code-block__header">
                <span className="code-block__language">{language}</span>
                <button
                    className={`code-block__copy ${copied ? 'code-block__copy--copied' : ''}`}
                    onClick={handleCopy}
                >
                    {copied ? '✓ Copied' : 'Copy'}
                </button>
            </div>
            <div className="code-block__content">
                <code>{code}</code>
            </div>
        </div>
    );
}
