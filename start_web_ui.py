
import http.server
import socketserver
import json
import subprocess
import os
import sys
import threading
import webbrowser
from pathlib import Path

# Config
PORT = 8000

# Detect if running as bundled executable
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    ROOT_DIR = Path(sys._MEIPASS)
    FRONTEND_DIR = ROOT_DIR / "frontend"
    SRC_DIR = ROOT_DIR
    IS_FROZEN = True
else:
    # Running as script
    ROOT_DIR = Path(__file__).parent
    FRONTEND_DIR = ROOT_DIR / "frontend"
    SRC_DIR = ROOT_DIR / "src"
    IS_FROZEN = False

# Add src to path to allow running modules if needed (though we use subprocess)
if not IS_FROZEN:
    sys.path.append(str(SRC_DIR))

# Map specific commands to CLI arguments (for non-frozen mode)
# Note: output of these commands is expected to be JSON printed to stdout.
CMD_MAP = {
    "scan": [sys.executable, "-m", "winstyles", "scan", "-f", "json"],
    "export_config": [sys.executable, "-m", "winstyles", "export"],
    "import_config": [sys.executable, "-m", "winstyles", "import"],
    "generate_report": [sys.executable, "-m", "winstyles", "report", "-f", "markdown"],
    "diff": [sys.executable, "-m", "winstyles", "diff", "-f", "json"],
    "inspect": [sys.executable, "-m", "winstyles", "inspect", "-f", "json"],
}

# Direct module imports for frozen mode
def get_engine():
    """Get StyleEngine instance."""
    from winstyles.core.engine import StyleEngine
    return StyleEngine()

def get_report_generator(scan_result, check_updates=True):
    """Get ReportGenerator instance."""
    from winstyles.core.report import ReportGenerator
    return ReportGenerator(scan_result, check_updates=check_updates)

class ApiHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence logs to avoid cluttering if needed, or keep for debugging
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format%args))

    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        
        # Serve static files from frontend directory
        self.directory = str(FRONTEND_DIR)
        super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.handle_api()
        else:
            self.send_error(404, "API endpoint not found")

    def handle_api(self):
        content_len = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_len)
        try:
            payload = json.loads(post_body) if post_body else {}
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON body")
            return

        command_name = self.path.replace("/api/", "")
        
        try:
            result = self.dispatch_command(command_name, payload)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # If the result is a dict/list, dump it. If it's a string (JSON string from CLI), dump it as a string.
            # Tauri backend returns a String which contains JSON.
            # So here we return a JSON stringified String.
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def dispatch_command(self, name, payload):
        # In frozen mode, call modules directly
        if IS_FROZEN:
            return self.dispatch_command_direct(name, payload)
        
        # In development mode, use subprocess
        if name == "scan":
            return self.run_cli_command(CMD_MAP["scan"], payload, 
                                      args_mapper=self.map_scan_args)
        elif name == "export_config":
            return self.run_cli_command(CMD_MAP["export_config"], payload, 
                                      args_mapper=self.map_export_args)
        elif name == "import_config":
            return self.run_cli_command(CMD_MAP["import_config"], payload, 
                                      args_mapper=self.map_import_args)
        elif name == "generate_report":
            # Report usually returns text content
            args = [sys.executable, "-m", "winstyles", "report", "-f", payload.get("format", "markdown")]
            return self.run_cli_command_raw(args)
        
        elif name == "check_font_updates":
            # Not implemented in CLI yet, return empty list
            return json.dumps([])
        
        elif name == "open_output_folder":
            os.startfile(os.getcwd())
            return ""
            
        elif name == "open_report_in_browser":
            # Just ignore or handle if needed
            return ""
        
        elif name == "browse_save_path" or name == "browse_open_path":
             return "" # Not supported in web mode
            
        else:
            raise ValueError(f"Unknown command: {name}")

    def dispatch_command_direct(self, name, payload):
        """Direct module calls for frozen mode (no subprocess)."""
        if name == "scan":
            engine = get_engine()
            categories = payload.get("categories")
            modified_only = payload.get("modifiedOnly", False)
            result = engine.scan_all(categories=categories)
            # Convert to JSON
            return result.model_dump_json()
        
        elif name == "generate_report":
            engine = get_engine()
            result = engine.scan_all(categories=None)
            fmt = payload.get("format", "markdown")
            generator = get_report_generator(result, check_updates=True)
            if fmt == "html":
                return generator.generate_html()
            else:
                return generator.generate_markdown()
        
        elif name == "check_font_updates":
            return json.dumps([])
        
        elif name == "open_output_folder":
            os.startfile(os.getcwd())
            return ""
        
        elif name == "open_report_in_browser":
            return ""
        
        elif name == "browse_save_path" or name == "browse_open_path":
            return ""
        
        elif name == "export_config":
            # TODO: Implement direct export
            return json.dumps({"error": "Export not yet supported in packaged mode"})
        
        elif name == "import_config":
            # TODO: Implement direct import
            return json.dumps({"error": "Import not yet supported in packaged mode"})
        
        else:
            raise ValueError(f"Unknown command: {name}")

    def run_cli_command(self, base_cmd, payload, args_mapper):
        cmd = base_cmd.copy()
        cmd.extend(args_mapper(payload))
        return self.run_subprocess(cmd)

    def run_cli_command_raw(self, cmd):
        return self.run_subprocess(cmd)

    def run_subprocess(self, cmd):
        print(f"Executing: {' '.join(cmd)}")
        # Run in src directory
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["WINSTYLES_WEB_MODE"] = "1"
        
        result = subprocess.run(
            cmd, 
            cwd=str(SRC_DIR),
            capture_output=True,
            text=True,
            encoding='utf-8',
            env=env
        )
        
        if result.returncode != 0:
            raise Exception(f"Command failed: {result.stderr}")
            
        return result.stdout.strip()

    # Argument Mappers
    def map_scan_args(self, payload):
        args = []
        if payload.get("categories"):
            for cat in payload.get("categories"):
                # Ensure we don't double encode if categories is a list of strings
                if isinstance(cat, str):
                   args.extend(["-c", cat])
        
        if payload.get("modifiedOnly"):
            args.append("--modified-only")
            
        return args

    def map_export_args(self, payload):
        args = []
        path = payload.get("path")
        if not path:
            raise ValueError("Path is required")
        args.append(path)
        
        if payload.get("categories"):
            for cat in payload.get("categories").split(","):
                if cat.strip():
                    args.extend(["-c", cat.strip()])
        
        if payload.get("includeDefaults"):
            args.append("--include-defaults")
        return args

    def map_import_args(self, payload):
        args = []
        path = payload.get("path")
        if not path:
             raise ValueError("Path is required")
        args.append(path)
        
        if payload.get("dryRun"):
            args.append("--dry-run")
        if payload.get("skipRestore"):
            args.append("--skip-restore-point")
        return args

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run_server():
    with ReusableTCPServer(("", PORT), ApiHandler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        print("Press Ctrl+C to stop")
        webbrowser.open(f"http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    run_server()
