// Message types
export interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    isStreaming?: boolean;
}

// Connection states
export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'error';

// Chat state
export interface ChatState {
    messages: Message[];
    isTyping: boolean;
    connectionStatus: ConnectionStatus;
}

// WebSocket message format
export interface WSMessage {
    type: 'message' | 'typing' | 'error' | 'system';
    payload: {
        content?: string;
        role?: 'user' | 'assistant';
        error?: string;
    };
}

// Utility type for generating unique IDs
export const generateId = (): string => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

// Format timestamp for display
export const formatTime = (date: Date): string => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};
