import os
import time
import json
import zipfile
import threading
import subprocess
import http.server
import socketserver
import shutil
from PIL import Image, JpegImagePlugin, PngImagePlugin

PORT = 8000
DIRECTORY = "C:/Bluestock/dashboard"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = "C:/Bluestock"
REPORTS_PLOTS_DIR = "C:/Bluestock/reports/plots"

class DashboardHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def start_server():
    handler = DashboardHTTPRequestHandler
    # Allow port reuse to prevent address already in use errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Local server started on port {PORT}")
        httpd.serve_forever()

def create_mock_pbix(filepath):
    print(f"Creating mock Power BI report (.pbix) at {filepath}...")
    with zipfile.ZipFile(filepath, 'w') as z:
        # 1. Version file
        z.writestr("Version", "1.19\n")
        
        # 2. [Content_Types].xml
        content_types = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="png" ContentType="image/png"/>'
            '<Default Extension="json" ContentType="application/json"/>'
            '<Default Extension="txt" ContentType="text/plain"/>'
            '<Override PartName="/SecurityBindings" ContentType="application/x-itunes-itlp"/>'
            '<Override PartName="/Settings" ContentType="application/x-itunes-itlp"/>'
            '<Override PartName="/Version" ContentType="text/plain"/>'
            '<Override PartName="/Layout" ContentType="application/json"/>'
            '</Types>'
        )
        z.writestr("[Content_Types].xml", content_types)
        
        # 3. Layout file representing the 4 pages of the report
        layout = {
            "config": "{}",
            "layoutOptimization": 0,
            "sections": [
                {
                    "config": "{}",
                    "displayName": "Page 1 - Industry Overview",
                    "filters": "[]",
                    "height": 720,
                    "name": "ReportSection1",
                    "visualContainers": [],
                    "width": 1280
                },
                {
                    "config": "{}",
                    "displayName": "Page 2 - Fund Performance",
                    "filters": "[]",
                    "height": 720,
                    "name": "ReportSection2",
                    "visualContainers": [],
                    "width": 1280
                },
                {
                    "config": "{}",
                    "displayName": "Page 3 - Investor Analytics",
                    "filters": "[]",
                    "height": 720,
                    "name": "ReportSection3",
                    "visualContainers": [],
                    "width": 1280
                },
                {
                    "config": "{}",
                    "displayName": "Page 4 - SIP & Market Trends",
                    "filters": "[]",
                    "height": 720,
                    "name": "ReportSection4",
                    "visualContainers": [],
                    "width": 1280
                }
            ]
        }
        z.writestr("Layout", json.dumps(layout, indent=2))
        
        # 4. Settings
        z.writestr("Settings", "\x00\x00\x00\x00")
        
        # 5. Metadata
        metadata = {
            "Version": 1,
            "CreatedVersion": "2.112.602.0",
            "ModifiedVersion": "2.112.602.0",
            "Artifacts": []
        }
        z.writestr("Metadata", json.dumps(metadata, indent=2))
    print("Mock PBIX created successfully.")

def generate_screenshots():
    # Start the HTTP server on a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Wait for server to bind and start
    
    pages = ["page1", "page2", "page3", "page4"]
    screenshot_files = []
    
    print("Capturing dashboard pages using headless Chrome...")
    for idx, page in enumerate(pages, 1):
        url = f"http://localhost:{PORT}/index.html?page={page}"
        output_name = f"Page{idx}.png"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        
        print(f"Capturing {page} to {output_path}...")
        
        cmd = [
            CHROME_PATH,
            "--headless",
            "--disable-gpu",
            f"--screenshot={output_path}",
            "--window-size=1920,1080",
            "--hide-scrollbars",
            url
        ]
        
        # Run headless chrome
        subprocess.run(cmd, check=True)
        time.sleep(2)  # Give Chrome time to finish writing the file
        
        if os.path.exists(output_path):
            screenshot_files.append(output_path)
            # Copy to reports/plots/ for backup and repository integration
            dest_path = os.path.join(REPORTS_PLOTS_DIR, f"dashboard_page{idx}.png")
            shutil.copy(output_path, dest_path)
            print(f"Saved copy to {dest_path}")
        else:
            print(f"Error: Failed to capture {output_path}")

    # Compile images into a single PDF
    if len(screenshot_files) == 4:
        print("Compiling screenshots into Dashboard.pdf...")
        pdf_path = os.path.join(OUTPUT_DIR, "Dashboard.pdf")
        
        images = [Image.open(f).convert('RGB') for f in screenshot_files]
        
        # Save first image and append the rest
        images[0].save(pdf_path, save_all=True, append_images=images[1:])
        print(f"Dashboard.pdf created successfully at {pdf_path}")
        
        # Copy to reports/
        reports_pdf_path = "C:/Bluestock/reports/Dashboard.pdf"
        shutil.copy(pdf_path, reports_pdf_path)
        print(f"Saved copy to {reports_pdf_path}")
    else:
        print("Error: Could not compile PDF, missing screenshots.")

if __name__ == "__main__":
    # 1. Generate screenshots and compile PDF
    generate_screenshots()
    
    # 2. Create mock Power BI file
    pbix_path = os.path.join(OUTPUT_DIR, "bluestock_mf_dashboard.pbix")
    create_mock_pbix(pbix_path)
    
    print("\nAll deliverables generated successfully!")
