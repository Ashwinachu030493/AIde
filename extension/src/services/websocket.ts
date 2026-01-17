import * as vscode from 'vscode';

/**
 * Manages WebSocket connection with automatic reconnection
 * Implements exponential backoff with jitter to prevent thundering herd
 */
export class AideWebSocket {
  private ws: WebSocket | null = null;
  private url: string = '';
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private baseDelay = 1000;  // 1 second
  private maxDelay = 30000;   // 30 seconds
  
  private onMessageCallback: ((data: string) => void) | null = null;
  private onOpenCallback: (() => void) | null = null;
  private onErrorCallback: ((error: Event) => void) | null = null;
  private onCloseCallback: (() => void) | null = null;
  
  /**
   * Connect to WebSocket with automatic reconnection on failure
   */
  public async connect(url: string): Promise<void> {
    this.url = url;
    
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(url);
        
        this.ws.onopen = () => {
          console.log('[WebSocket] Connected to', url);
          this.reconnectAttempts = 0;  // Reset on successful connection
          
          if (this.onOpenCallback) {
            this.onOpenCallback();
          }
          
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          if (this.onMessageCallback) {
            this.onMessageCallback(event.data);
          }
        };
        
        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          
          if (this.onErrorCallback) {
            this.onErrorCallback(error);
          }
          
          reject(error);
        };
        
        this.ws.onclose = async (event) => {
          console.log('[WebSocket] Closed. Code:', event.code, 'Reason:', event.reason);
          
          if (this.onCloseCallback) {
            this.onCloseCallback();
          }
          
          // Attempt reconnection with exponential backoff
          if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.notifyMaxReconnectExceeded();
            return;  // Stop trying
          }
          
          // Calculate delay with exponential backoff + jitter
          const exponentialDelay = this.baseDelay * Math.pow(2, this.reconnectAttempts);
          const delay = Math.min(exponentialDelay, this.maxDelay) + Math.random() * 1000;
          
          console.log(`[WebSocket] Reconnecting in ${delay.toFixed(0)}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
          
          // Wait before reconnecting
          await new Promise(res => setTimeout(res, delay));
          
          this.reconnectAttempts++;
          
          try {
            await this.connect(this.url);
          } catch (error) {
            console.error('[WebSocket] Reconnection failed:', error);
            // Will be retried by onclose handler
          }
        };
      } catch (error) {
        console.error('[WebSocket] Connection error:', error);
        reject(error);
      }
    });
  }
  
  /**
   * Send message through WebSocket
   */
  public send(data: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    } else {
      console.warn('[WebSocket] Cannot send - connection not open. State:', this.ws?.readyState);
    }
  }
  
  /**
   * Close WebSocket connection
   */
  public close(): void {
    if (this.ws) {
      this.ws.close(1000, 'User closed connection');
      this.ws = null;
    }
  }
  
  /**
   * Get current connection state
   */
  public isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
  
  /**
   * Register callback for incoming messages
   */
  public onMessage(callback: (data: string) => void): void {
    this.onMessageCallback = callback;
  }
  
  /**
   * Register callback for connection open
   */
  public onOpen(callback: () => void): void {
    this.onOpenCallback = callback;
  }
  
  /**
   * Register callback for connection error
   */
  public onError(callback: (error: Event) => void): void {
    this.onErrorCallback = callback;
  }
  
  /**
   * Register callback for connection close
   */
  public onClose(callback: () => void): void {
    this.onCloseCallback = callback;
  }
  
  /**
   * Notify user that reconnection failed after max attempts
   */
  private notifyMaxReconnectExceeded(): void {
    vscode.window.showWarningMessage(
      '⚠️ AIde connection lost. Please refresh the VS Code window.',
      'Refresh'
    ).then((selection) => {
      if (selection === 'Refresh') {
        vscode.commands.executeCommand('workbench.action.reloadWindow');
      }
    });
  }
}
