# Browser Setup for Omnix AI

This application uses Playwright browsers for web automation. Follow these steps to set up browser support:

## Quick Setup

1. **Run the setup script:**
   ```bash
   ./setup_browser.sh
   ```

## Manual Setup

If the automatic setup doesn't work, follow these steps:

### 1. Install Playwright Browsers
```bash
playwright install chromium firefox webkit
```

### 2. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    libnss3 libnspr4 libatspi2.0-0 libdrm2 libxkbcommon0 \
    libxss1 libgconf-2-4 libxrandr2 libasound2 \
    libpangocairo-1.0-0 libatk1.0-0 libcairo-gobject2 \
    libgtk-3-0 libgdk-pixbuf2.0-0
```

**CentOS/RHEL/Fedora:**
```bash
sudo yum install -y \
    nss nspr atk at-spi2-atk gtk3 gdk-pixbuf2 \
    libdrm libxkbcommon libxss gconf libxrandr \
    alsa-lib pango cairo-gobject
```

### 3. Alternative: Use Playwright's built-in installer
```bash
playwright install-deps
```

## Troubleshooting

### Browser Not Found Error
If you see `FileNotFoundError: [Errno 2] No such file or directory`, it means the browser binaries are not installed. Run:
```bash
playwright install
```

### Missing System Libraries
If browsers fail to start with missing library errors, install the system dependencies listed above.

### Headless Mode
The application runs in headless mode by default to avoid GUI dependencies. This should work even without a display server.

### Browser Fallback
The application will try different browsers in this order:
1. Chromium (Playwright bundled)
2. Firefox  
3. WebKit

If one fails, it will automatically try the next one.

## Verification

To verify the setup works:
1. Start the application: `python main.py`
2. Go to `http://localhost:8001`
3. Try submitting a browser task like "go to google.com"

If successful, you should see browser automation logs in the console.