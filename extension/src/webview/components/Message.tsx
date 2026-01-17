import React, { useState } from 'react';
import { Message as MessageType, formatTime } from '../types';
import { CodeBlock } from './CodeBlock';

interface Props {
    message: MessageType;
}

// Simple regex to detect code blocks in markdown format
const CODE_BLOCK_REGEX = /```(\w+)?\n?([\s\S]*?)```/g;

export function Message({ message }: Props) {
    const [copied, setCopied] = useState(false);
    const isUser = message.role === 'user';

    const handleCopyMessage = async () => {
        try {
            await navigator.clipboard.writeText(message.content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    // Parse content for code blocks
    const renderContent = () => {
        const parts: React.ReactNode[] = [];
        let lastIndex = 0;
        let match;

        const regex = new RegExp(CODE_BLOCK_REGEX);
        while ((match = regex.exec(message.content)) !== null) {
            // Add text before code block
            if (match.index > lastIndex) {
                parts.push(
                    <span key={`text-${lastIndex}`}>
                        {message.content.slice(lastIndex, match.index)}
                    </span>
                );
            }

            // Add code block
            const language = match[1] || 'plaintext';
            const code = match[2].trim();
            parts.push(<CodeBlock key={`code-${match.index}`} code={code} language={language} />);

            lastIndex = match.index + match[0].length;
        }

        // Add remaining text
        if (lastIndex < message.content.length) {
            parts.push(
                <span key={`text-${lastIndex}`}>
                    {message.content.slice(lastIndex)}
                </span>
            );
        }

        return parts.length > 0 ? parts : message.content;
    };

    return (
        <div className={`message message--${isUser ? 'user' : 'ai'}`}>
            <div className="message__avatar">
                {isUser ? 'U' : 'AI'}
            </div>
            <div className="message__content">
                <div className="message__bubble">
                    {renderContent()}
                </div>
                <div className="message__meta">
                    <span className="message__time">{formatTime(message.timestamp)}</span>
                    {!isUser && (
                        <div className="message__actions">
                            <button
                                className="icon-btn"
                                onClick={handleCopyMessage}
                                title={copied ? 'Copied!' : 'Copy message'}
                            >
                                {copied ? '✓' : '📋'}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
