This guide outlines the implementation of **RustFS** as a high-performance S3 gateway on your NAS, secured by **Cloudflare Zero Trust**, to serve data to your remote dashboard.

---

## 📄 Implementation Guide: Secure NAS Data Bridge

### 1. NAS Infrastructure (`docker-compose.yml`)

RustFS is preferred here for its low memory footprint and speed. We use the Cloudflare Tunnel to create a secure outbound connection.

```yaml
version: "3.9"
services:
  # RustFS: Lightweight S3-compatible storage
  rustfs:
    image: rustfs/rustfs:latest
    container_name: rustfs-server
    ports:
      - "9000:9000" # S3 API
      - "9001:9001" # Web Console
    environment:
      - RUSTFS_ACCESS_KEY=dashboard_user
      - RUSTFS_SECRET_KEY=secure_nas_password_123
      - RUSTFS_VOLUMES=/data
      - RUSTFS_ADDRESS=0.0.0.0:9000
      - RUSTFS_CONSOLE_ENABLE=true
    volumes:
      # Map your NAS data (including the SSHFS mount point)
      - /mnt/nas_data:/data 
    restart: unless-stopped

  # Cloudflare Tunnel: The "Safe Pipe" to the outside
  tunnel:
    image: cloudflare/cloudflared:latest
    container_name: cf-tunnel
    environment:
      - TUNNEL_TOKEN=your_cloudflare_tunnel_token
    command: tunnel run
    restart: unless-stopped

```

---

### 2. Python Scaffolding: `nas_bridge.py`

This script lives in your Dashboard project. It handles the specific headers required to pass through Cloudflare Zero Trust.

```python
import boto3
import polars as pl
from io import BytesIO
from botocore.config import Config

class NASBridge:
    def __init__(self, endpoint, access_key, secret_key, cf_id, cf_secret):
        self.endpoint = endpoint
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
            # Bypasses Cloudflare Access via Service Token
            extra_headers={
                "CF-Access-Client-Id": cf_id,
                "CF-Access-Client-Secret": cf_secret
            }
        )

    def load_data(self, bucket, csv_key):
        """Loads Parquet if available, otherwise falls back to CSV."""
        parquet_key = csv_key.replace(".csv", ".parquet")
        
        # Try Parquet first
        try:
            obj = self.s3.get_object(Bucket=bucket, Key=parquet_key)
            return pl.read_parquet(BytesIO(obj['Body'].read()))
        except:
            # Fallback to CSV
            try:
                obj = self.s3.get_object(Bucket=bucket, Key=csv_key)
                return pl.read_csv(BytesIO(obj['Body'].read()))
            except Exception as e:
                return None

```

---

### 3. Maintenance Script: `optimize_nas.py`

Run this script **locally on the NAS** (via Cron). It watches your SSHFS mount and creates optimized Parquet files inside RustFS.

```python
import polars as pl
import os
import glob

# Configuration
RAW_DIR = "/mnt/sshfs_mount/incoming_data/"
RUSTFS_DIR = "/mnt/nas_data/optimized_data/"

def maintenance_sync():
    # Find all CSVs in the finicky SSHFS mount
    csv_files = glob.glob(os.path.join(RAW_DIR, "*.csv"))
    
    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        parquet_name = filename.replace(".csv", ".parquet")
        target_path = os.path.join(RUSTFS_DIR, parquet_name)

        # Only convert if the CSV is newer than the existing Parquet
        if not os.path.exists(target_path) or os.path.getmtime(csv_path) > os.path.getmtime(target_path):
            print(f"Optimizing {filename}...")
            try:
                # Read raw (unstable source) -> Write optimized (stable target)
                df = pl.read_csv(csv_path)
                df.write_parquet(target_path, compression="zstd")
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

if __name__ == "__main__":
    maintenance_sync()

```

---

### 4. Implementation Checklist

| Step | Action | Notes |
| --- | --- | --- |
| **1** | **Create Tunnel** | Go to Cloudflare Zero Trust > Networks > Tunnels. |
| **2** | **Public Hostname** | Map `data.yourdomain.com` to `http://rustfs:9000`. |
| **3** | **Service Token** | Access > Service Auth > Create Token for `data.yourdomain.com`. |
| **4** | **Access Policy** | Create a policy for the domain allowing "Service Token" access. |
| **5** | **Deploy** | Run Docker Compose on NAS and the Cron script for conversion. |

### Summary of Benefits

* **Decoupled:** The dashboard doesn't care if the SSHFS mount is currently down; it reads from the "optimized" folder on the NAS.
* **Zero Exposure:** No open ports on your router.
* **Performance:** Parquet files are typically **5x–10x smaller** and load much faster over the internet than raw CSVs.

**Would you like me to generate a `crontab` example or a systemd service file to keep that maintenance script running automatically?**
