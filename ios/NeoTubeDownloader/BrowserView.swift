import SwiftUI
import WebKit

struct BrowserView: UIViewRepresentable {
    let url: URL
    let onResetServer: () -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(onResetServer: onResetServer)
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        let controller = WKUserContentController()
        controller.add(context.coordinator, name: "openFolder")
        controller.addUserScript(WKUserScript(
            source: """
            window.NeoTubeIOS = {
              openFolder: function(folder) {
                window.webkit.messageHandlers.openFolder.postMessage(folder || "");
              }
            };
            """,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: false
        ))
        configuration.userContentController = controller

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        webView.allowsBackForwardNavigationGestures = true
        webView.load(URLRequest(url: url))
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        if webView.url == nil || webView.url?.host != url.host || webView.url?.port != url.port {
            webView.load(URLRequest(url: url))
        }
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
        private let onResetServer: () -> Void

        init(onResetServer: @escaping () -> Void) {
            self.onResetServer = onResetServer
        }

        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            guard message.name == "openFolder" else {
                return
            }
            // iOS does not expose arbitrary folder opening like desktop/Android.
            // Keeping this bridge lets the shared UI call the native shell without crashing.
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            showLoadError(webView: webView, error: error)
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            showLoadError(webView: webView, error: error)
        }

        private func showLoadError(webView: WKWebView, error: Error) {
            let html = """
            <!doctype html>
            <html>
            <head>
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <style>
                body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 24px; color: #17202a; }
                h1 { font-size: 22px; }
                p { color: #526070; line-height: 1.4; }
              </style>
            </head>
            <body>
              <h1>Could not open NeoTube Downloader</h1>
              <p>Check that the NeoTube server is running and reachable from this iPhone.</p>
              <p>\(error.localizedDescription)</p>
            </body>
            </html>
            """
            webView.loadHTMLString(html, baseURL: nil)
        }
    }
}

