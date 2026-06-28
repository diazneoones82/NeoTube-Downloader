import SwiftUI

struct ContentView: View {
    @AppStorage("serverURL") private var serverURL = ""
    @State private var draftURL = ""
    @State private var showingBrowser = false

    private var platformLabel: String {
        #if targetEnvironment(macCatalyst)
        return "NEO Apps : Mac"
        #else
        return "NEO Apps : iOS"
        #endif
    }

    var body: some View {
        Group {
            if showingBrowser, let url = URL(string: serverURL), !serverURL.isEmpty {
                BrowserView(url: url) {
                    showingBrowser = false
                }
                .ignoresSafeArea(edges: .bottom)
            } else {
                setupView
            }
        }
        .onAppear {
            draftURL = serverURL.isEmpty ? "http://127.0.0.1:8081/" : serverURL
            showingBrowser = !serverURL.isEmpty
        }
    }

    private var setupView: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 18) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("NeoTube Downloader")
                        .font(.largeTitle.bold())
                    Text(platformLabel)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(.secondary)
                }

                Text("Enter the NeoTube server URL to open the downloader on this device.")
                    .foregroundStyle(.secondary)

                TextField("Server URL", text: $draftURL)
                    .keyboardType(.URL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .padding(12)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8))

                Button {
                    let normalized = normalize(url: draftURL)
                    serverURL = normalized
                    draftURL = normalized
                    showingBrowser = true
                } label: {
                    Label("Open Downloader", systemImage: "arrow.up.right.square")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .disabled(normalize(url: draftURL).isEmpty)

                Spacer()

                VStack(alignment: .leading, spacing: 4) {
                    Text("NeoTube Downloader by Neo Apps saves videos and audio for offline use.")
                    Text("Contributor: diazneoones82")
                }
                .font(.footnote)
                .foregroundStyle(.secondary)
            }
            .padding(22)
            .navigationTitle("NeoTube")
        }
    }

    private func normalize(url: String) -> String {
        let trimmed = url.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            return ""
        }
        if trimmed.hasPrefix("http://") || trimmed.hasPrefix("https://") {
            return trimmed
        }
        return "http://\(trimmed)"
    }
}
