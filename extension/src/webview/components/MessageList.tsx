import React, { useRef, useEffect } from 'react';
import { Message as MessageType } from '../types';
import { Message } from './Message';
import { TypingIndicator } from './TypingIndicator';

interface Props {
    messages: MessageType[];
    isTyping: boolean;
}

export function MessageList({ messages, isTyping }: Props) {
    const bottomRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isTyping]);

    if (messages.length === 0 && !isTyping) {
        return (
            <div className="message-list">
                <div className="message-list__empty">
                    <div className="message-list__empty-icon">💬</div>
                    <p>No messages yet. Start a conversation!</p>
                </div>
            </div>
        );
    }

    return (
        <div className="message-list">
            {messages.map((message) => (
                <Message key={message.id} message={message} />
            ))}
            {isTyping && <TypingIndicator />}
            <div ref={bottomRef} />
        </div>
    );
}
