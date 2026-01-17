import { useState, useEffect, useCallback, useRef } from 'react';
import { Message, ConnectionStatus, generateId } from '../types';
import { AideWebSocket } from '../../services/websocket';

const WS_URL = 'ws://localhost:8000/chat/ws/default';
const CONVERSATION_ID = 'default';  // Use default conversation ID

export function useChat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
    const [isTyping, setIsTyping] = useState(false);
    const wsRef = useRef<AideWebSocket | null>(null);

    const connect = useCallback(async () => {
        if (wsRef.current?.isConnected()) return;

        setConnectionStatus('connecting');
        
        try {
            const aidWs = new AideWebSocket();
            
            // Setup callbacks BEFORE connecting
            aidWs.onOpen(() => {
                setConnectionStatus('connected');
                console.log('[AIde] WebSocket connected');
            });

            aidWs.onMessage((data: string) => {
                setIsTyping(false);

                // For MVP, the backend echoes back the message
                // In production, this would parse JSON with role, content, etc.
                const newMessage: Message = {
                    id: generateId(),
                    role: 'assistant',
                    content: data.replace(/^Echo:\s*/, ''), // Remove "Echo: " prefix for cleaner display
                    timestamp: new Date(),
                };

                setMessages(prev => [...prev, newMessage]);
            });

            aidWs.onClose(() => {
                setConnectionStatus('disconnected');
                console.log('[AIde] WebSocket disconnected. Auto-reconnect in progress...');
                // Reconnection is handled by AideWebSocket, we just update UI
            });

            aidWs.onError((error: Event) => {
                console.error('[AIde] WebSocket error:', error);
                setConnectionStatus('error');
            });

            // Connect with conversation-specific URL
            await aidWs.connect(`${WS_URL}/${CONVERSATION_ID}`);
            wsRef.current = aidWs;
        } catch (error) {
            console.error('[AIde] Failed to connect:', error);
            setConnectionStatus('disconnected');
        }
    }, []);

    const disconnect = useCallback(() => {
        wsRef.current?.close();
        wsRef.current = null;
        setConnectionStatus('disconnected');
    }, []);

    const sendMessage = useCallback((content: string) => {
        if (!content.trim() || connectionStatus !== 'connected') return;

        // Add user message immediately
        const userMessage: Message = {
            id: generateId(),
            role: 'user',
            content: content.trim(),
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, userMessage]);

        // Send to server
        wsRef.current?.send(content.trim());

        // Show typing indicator
        setIsTyping(true);
    }, [connectionStatus]);

    const clearMessages = useCallback(() => {
        setMessages([]);
    }, []);

    // Connect on mount, disconnect on unmount
    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        messages,
        connectionStatus,
        isTyping,
        sendMessage,
        clearMessages,
        reconnect: connect,
    };
}
