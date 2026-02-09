import base64
import http.server
import json
import os
import socketserver
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

# Config
PORT = 8000

# Detect if running as bundled executable
if getattr(sys, "frozen", False):
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
    "scan": [sys.executable, "-m", "winstyles", "scan"],
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
        sys.stderr.write(
            f"{self.client_address[0]} - - " f"[{self.log_date_time_string()}] {format % args}\n"
        )

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
        content_len = int(self.headers.get("Content-Length", 0))
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
            self.send_header("Content-type", "application/json")
            self.end_headers()

            # If the result is a dict/list, dump it.
            # If it's a string (JSON string from CLI), dump it as a string.
            # Tauri backend returns a String which contains JSON.
            # So here we return a JSON stringified String.
            self.wfile.write(json.dumps(result).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def dispatch_command(self, name, payload):
        # In frozen mode, call modules directly
        if IS_FROZEN:
            return self.dispatch_command_direct(name, payload)

        # In development mode, use subprocess
        if name == "scan":
            return self.run_cli_command(CMD_MAP["scan"], payload, args_mapper=self.map_scan_args)
        elif name == "export_config":
            return self.run_cli_command(
                CMD_MAP["export_config"], payload, args_mapper=self.map_export_args
            )
        elif name == "import_config":
            return self.run_import_command(payload)
        elif name == "generate_report":
            # Report usually returns text content
            args = [
                sys.executable,
                "-m",
                "winstyles",
                "report",
                "-f",
                payload.get("format", "markdown"),
            ]
            if not bool(payload.get("checkUpdates", True)):
                args.append("--no-check-updates")
            return self.run_cli_command_raw(args)

        elif name == "check_font_updates":
            return self.check_font_updates()
        elif name == "refresh_font_db":
            return self.refresh_font_db()

        elif name == "open_output_folder":
            os.startfile(os.getcwd())
            return ""

        elif name == "open_report_in_browser":
            # Just ignore or handle if needed
            return ""

        elif name == "browse_save_path" or name == "browse_open_path":
            return ""  # Not supported in web mode

        else:
            raise ValueError(f"Unknown command: {name}")

    def dispatch_command_direct(self, name, payload):
        """Direct module calls for frozen mode (no subprocess)."""
        if name == "scan":
            engine = get_engine()
            categories = payload.get("categories")
            result = engine.scan_all(categories=categories)
            if payload.get("modifiedOnly"):
                result = self._filter_scan_result(result, keep_defaults=False)
            return result.model_dump_json()

        elif name == "generate_report":
            engine = get_engine()
            result = engine.scan_all(categories=None)
            fmt = payload.get("format", "markdown")
            check_updates = bool(payload.get("checkUpdates", True))
            generator = get_report_generator(result, check_updates=check_updates)
            if fmt == "html":
                return generator.generate_html()
            else:
                return generator.generate_markdown()

        elif name == "check_font_updates":
            return self.check_font_updates()
        elif name == "refresh_font_db":
            return self.refresh_font_db()

        elif name == "open_output_folder":
            os.startfile(os.getcwd())
            return ""

        elif name == "open_report_in_browser":
            return ""

        elif name == "browse_save_path" or name == "browse_open_path":
            return ""

        elif name == "export_config":
            output_path = payload.get("path")
            if not output_path:
                raise ValueError("Path is required")

            categories = payload.get("categories")
            if isinstance(categories, str):
                categories = [c.strip() for c in categories.split(",") if c.strip()]
            if not categories:
                categories = None

            include_defaults = bool(payload.get("includeDefaults"))
            include_font_files = bool(payload.get("includeFontFiles"))

            engine = get_engine()
            scan_result = engine.scan_all(categories=categories)
            if not include_defaults:
                scan_result = self._filter_scan_result(scan_result, keep_defaults=False)

            manifest = engine.export_package(
                scan_result,
                Path(output_path),
                include_assets=True,
                include_font_files=include_font_files,
            )
            return manifest.model_dump(mode="json")

        elif name == "import_config":
            temp_path = None
            try:
                package_path, temp_path = self.resolve_import_path(payload)
                engine = get_engine()
                summary = engine.import_package(
                    Path(package_path),
                    dry_run=bool(payload.get("dryRun")),
                    create_restore_point=not bool(payload.get("skipRestore")),
                )
                return summary
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

        else:
            raise ValueError(f"Unknown command: {name}")

    def run_cli_command(self, base_cmd, payload, args_mapper):
        cmd = base_cmd.copy()
        cmd.extend(args_mapper(payload))
        return self.run_subprocess(cmd)

    def run_cli_command_raw(self, cmd):
        return self.run_subprocess(cmd)

    def run_import_command(self, payload):
        temp_path = None
        try:
            package_path, temp_path = self.resolve_import_path(payload)
            args = self.map_import_args({**payload, "path": package_path})
            cmd = CMD_MAP["import_config"].copy()
            cmd.extend(args)
            return self.run_subprocess(cmd)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def resolve_import_path(self, payload):
        path = payload.get("path")
        if path:
            return path, None

        file_name = payload.get("fileName", "import_package.zip")
        file_b64 = payload.get("fileBase64")
        if not file_b64:
            raise ValueError("Path or uploaded file is required")

        # Supports raw base64 and data URL formats.
        encoded = file_b64.split(",", 1)[1] if "," in file_b64 else file_b64
        data = base64.b64decode(encoded)

        suffix = Path(file_name).suffix or ".zip"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(data)
            return temp_file.name, temp_file.name

    def check_font_updates(self):
        from winstyles.core.update_checker import UpdateChecker
        from winstyles.domain.models import OpenSourceFontInfo
        from winstyles.utils.font_utils import find_font_path, get_font_version

        engine = get_engine()
        result = engine.scan_all(categories=["fonts"])

        checker = UpdateChecker()
        db = checker.fetch_remote_db()
        if not db:
            return []

        updates = []
        fonts_info = db.get("fonts", [])
        for item in result.items:
            if item.category != "fonts":
                continue

            font_name = str(item.current_value)
            for font_info in fonts_info:
                patterns = font_info.get("patterns", [])
                name = font_info.get("name", "")
                matched = False

                for pattern in patterns:
                    pattern_lower = pattern.lower().replace("*", "")
                    if pattern_lower in font_name.lower():
                        matched = True
                        break

                if not matched:
                    continue

                font_path = find_font_path(font_name)
                local_version = get_font_version(font_path) if font_path else None

                os_font = OpenSourceFontInfo(
                    name=name,
                    patterns=patterns,
                    homepage=font_info.get("homepage", ""),
                    download=font_info.get("download", ""),
                    license=font_info.get("license", ""),
                    description=font_info.get("description", ""),
                )
                update_info = checker.check_font_update(os_font, local_version)
                if update_info:
                    updates.append(
                        {
                            "name": name,
                            "current_version": update_info.current_version,
                            "latest_version": update_info.latest_version,
                            "download_url": update_info.download_url,
                            "has_update": update_info.has_update,
                        }
                    )
                break

        return updates

    def refresh_font_db(self):
        from winstyles.core.update_checker import UpdateChecker

        checker = UpdateChecker()
        db = checker.fetch_remote_db()
        if not db:
            return {"ok": False, "message": "无法获取远程字体数据库"}
        return {
            "ok": True,
            "message": "字体数据库刷新完成",
            "font_count": len(db.get("fonts", [])),
        }

    def run_subprocess(self, cmd):
        print(f"Executing: {' '.join(cmd)}")
        # Run in src directory
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["WINSTYLES_WEB_MODE"] = "1"

        result = subprocess.run(
            cmd, cwd=str(SRC_DIR), capture_output=True, text=True, encoding="utf-8", env=env
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

        requested_format = str(payload.get("format", "json")).lower()
        format_arg = "json" if requested_format == "table" else requested_format
        args.extend(["-f", format_arg])

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
        if payload.get("includeFontFiles"):
            args.append("--include-font-files")
        return args

    def _filter_scan_result(self, result, keep_defaults):
        if keep_defaults:
            return result
        filtered_items = [item for item in result.items if item.change_type.value == "modified"]
        summary = {}
        for item in filtered_items:
            summary[item.category] = summary.get(item.category, 0) + 1

        from winstyles.domain.models import ScanResult

        return ScanResult(
            scan_id=result.scan_id,
            scan_time=result.scan_time,
            os_version=result.os_version,
            items=filtered_items,
            summary=summary,
            duration_ms=result.duration_ms,
        )

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
