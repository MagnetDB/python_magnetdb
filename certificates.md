# Certificate Installation Guide

This guide explains how to install self-signed certificates for local MagnetDB development across different web browsers.

## Understanding Certificate Installation

The `mkcert -install` command automatically installs the local Certificate Authority (CA) certificate into your system's trusted certificate stores. This should work automatically for most browsers on Linux, macOS, and Windows.

## Supported Browsers

- **Chrome/Chromium/Edge**: Use system certificate store (automatically configured by `mkcert -install`)
- **Firefox**: Uses its own certificate store (may require manual installation)
- **Safari (macOS)**: Uses system keychain (automatically configured by `mkcert -install`)
- **Opera**: Uses system certificate store (automatically configured by `mkcert -install`)

## Manual Certificate Installation

If you encounter SSL/TLS warnings in your browser, you may need to manually install the CA certificate:

### 1. Get the CA Certificate Location

```shell
mkcert -CAROOT
```

This will display the path to your CA certificate (typically `~/.local/share/mkcert` on Linux).

### 2. Firefox

Firefox uses its own certificate store and requires manual installation:

1. Open Firefox and go to `Settings` → `Privacy & Security` → `Certificates` → `View Certificates`
2. Click the `Authorities` tab
3. Click `Import`
4. Navigate to the mkcert CA root directory (use `mkcert -CAROOT` to find it)
5. Select `rootCA.pem`
6. Check "Trust this CA to identify websites"
7. Click OK
8. Restart Firefox

### 3. Chrome/Chromium (Linux)

**Automatic method using NSS tools:**

```shell
# Install NSS tools if not already installed
sudo apt-get install libnss3-tools  # Debian/Ubuntu
# OR
sudo dnf install nss-tools  # Fedora/RHEL

# Reinstall certificates
mkcert -install
```

Then restart Chrome/Chromium.

**Manual method:**

1. Go to `chrome://settings/certificates`
2. Click `Authorities` tab
3. Click `Import`
4. Navigate to the mkcert CA root directory
5. Select `rootCA.pem`
6. Check "Trust this certificate for identifying websites"
7. Click OK
8. Restart the browser

### 4. Microsoft Edge (Linux)

Follow the same steps as Chrome/Chromium above.

### 5. Safari (macOS)

Safari typically works automatically after `mkcert -install`. If issues persist:

1. Open Keychain Access
2. Select "System" keychain
3. Find the mkcert CA certificate
4. Double-click it
5. Expand "Trust" section
6. Set "When using this certificate" to "Always Trust"
7. Close the window and enter your password when prompted
8. Restart Safari

## Verifying Certificate Installation

After installation, access https://magnetdb-dev.local/ in your browser. You should see:

- ✓ A padlock icon in the address bar
- ✓ No SSL/TLS warnings
- ✓ Certificate issued by "mkcert" when viewing certificate details

## Troubleshooting

### Certificates Not Working After Installation

- **Restart your browser completely** - Close all windows and restart
- **For Firefox**: You must manually import the certificate (it doesn't use the system store)
- **For Chrome/Chromium on Linux**: Ensure NSS tools are installed (`libnss3-tools` or `nss-tools`)

### Still Seeing Warnings

1. Verify the certificate files exist:
   ```shell
   ls -la ../magnetdb-data/certs/
   ```

2. Check that the certificate was created for the correct domains:
   ```shell
   cd ../magnetdb-data/certs
   openssl x509 -in magnetdb-dev.local+2.pem -text -noout | grep DNS
   ```

3. Verify `/etc/hosts` entries match the certificate domains:
   ```shell
   grep magnetdb-dev.local /etc/hosts
   ```

### Permission Issues

If you see permission errors:

```shell
chmod 600 ../magnetdb-data/certs/*.key
chmod 644 ../magnetdb-data/certs/*.pem
```

### Regenerating Certificates

If you need to regenerate certificates:

```shell
cd ../magnetdb-data/certs
rm *.pem *.key
mkcert 'magnetdb-dev.local' '*.magnetdb-dev.local' '*.lemon.magnetdb-dev.local'
chmod 600 *.key
```

## Platform-Specific Notes

### Linux

- Most browsers use the NSS certificate database
- Firefox always requires manual installation
- Chrome/Chromium require `libnss3-tools` package

### macOS

- Safari and Chrome use the system keychain
- Firefox still requires manual installation
- `mkcert -install` should handle Safari and Chrome automatically

### Windows

- Browsers typically use the Windows certificate store
- `mkcert -install` should configure this automatically
- Firefox still requires manual installation

## Additional Resources

- [mkcert documentation](https://github.com/FiloSottile/mkcert)
- [Mozilla NSS documentation](https://firefox-source-docs.mozilla.org/security/nss/index.html)
