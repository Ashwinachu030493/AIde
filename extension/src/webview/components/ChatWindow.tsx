import React from 'react';
import { useChat } from '../hooks/useChat';
import { ConnectionStatus } from './ConnectionStatus';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';

export function ChatWindow() {
    const { messages, connectionStatus, isTyping, sendMessage } = useChat();

    return (
        <div className="chat-window">
            <header className="chat-header">
                <h1 className="chat-header__title">AIde</h1>
                <ConnectionStatus status={connectionStatus} />
            </header>

            <MessageList messages={messages} isTyping={isTyping} />

            <MessageInput
                onSend={sendMessage}
                disabled={connectionStatus !== 'connected'}
            />
        </div>
    );
}
