import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    const provider = new ChatViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(ChatViewProvider.viewType, provider)
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('aide.start', () => {
            vscode.window.showInformationMessage('AIde started!');
        })
    );

    // Check server connection on startup
    checkServerConnection();
}

async function checkServerConnection() {
    try {
        const response = await fetch('http://localhost:8000/health');
        if (!response.ok) {
            throw new Error('Server returned ' + response.status);
        }
    } catch (error) {
        const item = await vscode.window.showWarningMessage(
            '⚠️ AIde server not detected. Is it running?',
            'Try Again'
        );
        if (item === 'Try Again') {
            checkServerConnection();
        }
    }
}

class ChatViewProvider implements vscode.WebviewViewProvider {

    public static readonly viewType = 'aide.chatView';

    constructor(
        private readonly _extensionUri: vscode.Uri,
    ) { }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                this._extensionUri
            ]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        // Vite build outputs to out/webview/assets/index.js
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'out', 'webview', 'assets', 'index.js'));
        // Note: In a real Vite build, usually CSS is emitted. For this minimal setup, we verify JS load first.
        // If Vite injects CSS in JS (which it sometimes does in dev), we might need that.
        // For production build, we might need to check the manifest or standard output.
        // Assuming single file output for now or we will list css if needed.

        return `<!DOCTYPE html>
			<html lang="en">
			<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src ${webview.cspSource} 'unsafe-inline'; connect-src http://localhost:8000 ws://localhost:8000;">
				<title>AIde Chat</title>
			</head>
			<body>
				<div id="root"></div>
				<script type="module" src="${scriptUri}"></script>
			</body>
			</html>`;
    }
}
