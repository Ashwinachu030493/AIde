import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';

interface Props {
    onSend: (message: string) => void;
    disabled?: boolean;
}

export function MessageInput({ onSend, disabled = false }: Props) {
    const [value, setValue] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea
    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
        }
    }, [value]);

    const handleSend = () => {
        if (value.trim() && !disabled) {
            onSend(value);
            setValue('');
            // Reset height
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
            }
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        // Send on Enter (without Shift)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="message-input">
            <div className="message-input__container">
                <textarea
                    ref={textareaRef}
                    className="message-input__textarea"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask anything..."
                    disabled={disabled}
                    rows={1}
                />
                <button
                    className="message-input__send"
                    onClick={handleSend}
                    disabled={!value.trim() || disabled}
                    title="Send message"
                >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                    </svg>
                </button>
            </div>
            <div className="message-input__hint">
                <span><kbd>Enter</kbd> to send</span>
                <span><kbd>Shift + Enter</kbd> for new line</span>
            </div>
        </div>
    );
}
