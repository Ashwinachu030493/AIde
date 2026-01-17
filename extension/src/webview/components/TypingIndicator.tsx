import React from 'react';

export function TypingIndicator() {
    return (
        <div className="typing-indicator">
            <div className="typing-indicator__avatar">AI</div>
            <div className="typing-indicator__dots">
                <span className="typing-indicator__dot" />
                <span className="typing-indicator__dot" />
                <span className="typing-indicator__dot" />
            </div>
        </div>
    );
}
