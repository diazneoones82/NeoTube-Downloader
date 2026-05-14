package com.neoapps.neotube;

import android.app.Activity;
import android.app.DownloadManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.AssetManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.DocumentsContract;
import android.provider.Settings;
import android.view.Gravity;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.URLUtil;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;

public class MainActivity extends Activity {
    private static final int REQUEST_TREE = 2201;
    private static final String PREFS = "neoapps.neotube";
    private static final String KEY_DOWNLOAD_DIR = "downloadDir";
    private static final String KEY_DOWNLOAD_TREE_URI = "downloadTreeUri";

    private WebView webView;
    private LinearLayout loadingView;
    private TextView folderLabel;
    private String activeDownloadDir;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        activeDownloadDir = getStoredDownloadDir();
        requestAllFilesAccessIfNeeded();

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.WHITE);

        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setOrientation(LinearLayout.HORIZONTAL);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setPadding(dp(12), dp(8), dp(12), dp(8));
        toolbar.setBackgroundColor(Color.rgb(32, 35, 42));

        ImageView icon = new ImageView(this);
        icon.setImageResource(getResources().getIdentifier("ic_launcher", "mipmap", getPackageName()));
        toolbar.addView(icon, new LinearLayout.LayoutParams(dp(34), dp(34)));

        TextView title = new TextView(this);
        title.setText("NeoTube Downloader");
        title.setTextColor(Color.WHITE);
        title.setTextSize(17);
        title.setGravity(Gravity.CENTER_VERTICAL);
        title.setPadding(dp(10), 0, dp(8), 0);
        toolbar.addView(title, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1));

        Button folderButton = new Button(this);
        folderButton.setText("Folder");
        folderButton.setOnClickListener(v -> chooseDownloadFolder());
        toolbar.addView(folderButton, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, dp(42)));

        LinearLayout folderBar = new LinearLayout(this);
        folderBar.setPadding(dp(12), dp(6), dp(12), dp(6));
        folderBar.setBackgroundColor(Color.rgb(245, 247, 251));
        folderLabel = new TextView(this);
        folderLabel.setText(activeDownloadDir);
        folderLabel.setTextColor(Color.rgb(52, 66, 86));
        folderLabel.setTextSize(12);
        folderBar.addView(folderLabel);

        webView = new WebView(this);
        configureWebView();

        loadingView = new LinearLayout(this);
        loadingView.setGravity(Gravity.CENTER);
        loadingView.setOrientation(LinearLayout.VERTICAL);
        ProgressBar progress = new ProgressBar(this);
        TextView loadingText = new TextView(this);
        loadingText.setText("Starting downloader...");
        loadingText.setTextColor(Color.rgb(32, 35, 42));
        loadingText.setTextSize(16);
        loadingText.setPadding(0, dp(12), 0, 0);
        loadingView.addView(progress);
        loadingView.addView(loadingText);

        root.addView(toolbar, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
        root.addView(folderBar, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
        root.addView(loadingView, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
        root.addView(webView, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
        webView.setVisibility(WebView.GONE);
        setContentView(root);

        startBackend();
    }

    private void configureWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);

        webView.addJavascriptInterface(new NeoTubeBridge(), "NeoTubeAndroid");
        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient());
        webView.setDownloadListener((url, userAgent, contentDisposition, mimetype, contentLength) -> {
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
            String cookies = CookieManager.getInstance().getCookie(url);
            if (cookies != null) {
                request.addRequestHeader("Cookie", cookies);
            }
            request.addRequestHeader("User-Agent", userAgent);
            request.setMimeType(mimetype);
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setDestinationInExternalPublicDir(
                Environment.DIRECTORY_DOWNLOADS,
                URLUtil.guessFileName(url, contentDisposition, mimetype)
            );
            DownloadManager manager = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
            manager.enqueue(request);
            Toast.makeText(this, "Download started", Toast.LENGTH_SHORT).show();
        });
    }

    private void startBackend() {
        new Thread(() -> {
            try {
                copyAssetDir("ui", new File(getFilesDir(), "www/ui"));
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(this));
                }
                Python py = Python.getInstance();
                PyObject server = py.getModule("android_server");
                String url = server.callAttr(
                    "start",
                    getFilesDir().getAbsolutePath(),
                    getBackendDownloadDir(),
                    "",
                    true
                ).toString();
                runOnUiThread(() -> {
                    loadingView.setVisibility(LinearLayout.GONE);
                    webView.setVisibility(WebView.VISIBLE);
                    webView.loadUrl(url);
                });
            } catch (Exception exc) {
                runOnUiThread(() -> Toast.makeText(this, "Startup failed: " + exc.getMessage(), Toast.LENGTH_LONG).show());
            }
        }, "neotube-python-startup").start();
    }

    private File extractFfmpeg() throws IOException {
        File dir = new File(getFilesDir(), "ffmpeg");
        File ffmpeg = new File(dir, "ffmpeg");
        copyAssetFile("ffmpeg/arm64-v8a/ffmpeg", ffmpeg);
        if (!ffmpeg.setExecutable(true, true)) {
            throw new IOException("Could not mark ffmpeg executable");
        }
        return ffmpeg;
    }

    private String getStoredDownloadDir() {
        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        String stored = prefs.getString(KEY_DOWNLOAD_DIR, null);
        if (stored != null && !stored.trim().isEmpty()) {
            return stored;
        }
        return new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), "NeoTube Downloader").getAbsolutePath();
    }

    private String getBackendDownloadDir() {
        if (Build.VERSION.SDK_INT >= 30 && !Environment.isExternalStorageManager()) {
            File fallback = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
            return fallback == null ? activeDownloadDir : fallback.getAbsolutePath();
        }
        return activeDownloadDir;
    }

    private void chooseDownloadFolder() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(intent, REQUEST_TREE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_TREE && resultCode == RESULT_OK && data != null) {
            Uri uri = data.getData();
            if (uri != null) {
                int flags = data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                getContentResolver().takePersistableUriPermission(uri, flags);
            }
            String path = pathFromTreeUri(uri);
            if (path == null) {
                Toast.makeText(this, "Choose a folder on internal phone storage.", Toast.LENGTH_LONG).show();
                return;
            }
            activeDownloadDir = path;
            getSharedPreferences(PREFS, MODE_PRIVATE)
                .edit()
                .putString(KEY_DOWNLOAD_DIR, path)
                .putString(KEY_DOWNLOAD_TREE_URI, uri.toString())
                .apply();
            folderLabel.setText(path);
            Toast.makeText(this, "Download folder saved. Restart app to use it.", Toast.LENGTH_LONG).show();
        }
    }

    private String pathFromTreeUri(Uri uri) {
        if (uri == null || !"com.android.externalstorage.documents".equals(uri.getAuthority())) {
            return null;
        }
        String docId = DocumentsContract.getTreeDocumentId(uri);
        String[] parts = docId.split(":", 2);
        if (parts.length == 0 || !"primary".equalsIgnoreCase(parts[0])) {
            return null;
        }
        File root = Environment.getExternalStorageDirectory();
        return parts.length == 1 || parts[1].isEmpty()
            ? root.getAbsolutePath()
            : new File(root, parts[1]).getAbsolutePath();
    }

    private void requestAllFilesAccessIfNeeded() {
        if (Build.VERSION.SDK_INT >= 30 && !Environment.isExternalStorageManager()) {
            Toast.makeText(this, "Allow all files access so NeoTube can save to your selected folder.", Toast.LENGTH_LONG).show();
            Intent intent = new Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION);
            intent.setData(Uri.parse("package:" + getPackageName()));
            startActivity(intent);
        }
    }

    private void copyAssetDir(String assetPath, File targetDir) throws IOException {
        AssetManager assets = getAssets();
        String[] children = assets.list(assetPath);
        if (children == null || children.length == 0) {
            copyAssetFile(assetPath, targetDir);
            return;
        }
        if (!targetDir.exists() && !targetDir.mkdirs()) {
            throw new IOException("Could not create " + targetDir);
        }
        for (String child : children) {
            copyAssetDir(assetPath + "/" + child, new File(targetDir, child));
        }
    }

    private void copyAssetFile(String assetPath, File targetFile) throws IOException {
        File parent = targetFile.getParentFile();
        if (parent != null && !parent.exists() && !parent.mkdirs()) {
            throw new IOException("Could not create " + parent);
        }
        try (InputStream in = getAssets().open(assetPath);
             FileOutputStream out = new FileOutputStream(targetFile, false)) {
            byte[] buffer = new byte[64 * 1024];
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }
        }
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    public class NeoTubeBridge {
        @JavascriptInterface
        public void openFolder(String folder) {
            runOnUiThread(() -> {
                SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
                String treeUri = prefs.getString(KEY_DOWNLOAD_TREE_URI, null);
                if (treeUri != null && !treeUri.trim().isEmpty()) {
                    Uri uri = Uri.parse(treeUri);
                    Intent intent = new Intent(Intent.ACTION_VIEW);
                    intent.setDataAndType(uri, "vnd.android.document/directory");
                    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                    try {
                        startActivity(intent);
                        return;
                    } catch (Exception ignored) {
                        Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
                        picker.putExtra(DocumentsContract.EXTRA_INITIAL_URI, uri);
                        picker.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                        startActivity(picker);
                        return;
                    }
                }
                Toast.makeText(MainActivity.this, "Download folder: " + activeDownloadDir, Toast.LENGTH_LONG).show();
            });
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
