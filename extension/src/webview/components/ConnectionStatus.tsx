import React from 'react';
import { ConnectionStatus as ConnectionStatusType } from '../types';

interface Props {
    status: ConnectionStatusType;
}

export function ConnectionStatus({ status }: Props) {
    const labels: Record<ConnectionStatusType, string> = {
        connected: 'Connected',
        disconnected: 'Offline',
        connecting: 'Connecting...',
    };

    return (
        <div className={`connection-status connection-status--${status}`}>
            <span className="connection-status__dot" />
            <span>{labels[status]}</span>
        </div>
    );
}
