#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;

fn python_cmd() -> String {
    std::env::var("PYTHON").unwrap_or_else(|_| "python".to_string())
}

fn run_command(args: &[String]) -> Result<String, String> {
    let output = Command::new(python_cmd())
        .args(args)
        .env("PYTHONUTF8", "1")
        .env("PYTHONIOENCODING", "utf-8")
        .output()
        .map_err(|err| err.to_string())?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        Err(stderr)
    }
}

#[tauri::command]
fn open_output_folder() -> Result<(), String> {
    let cwd = std::env::current_dir().map_err(|err| err.to_string())?;
    let status = Command::new("explorer")
        .arg(cwd)
        .status()
        .map_err(|err| err.to_string())?;

    if status.success() {
        Ok(())
    } else {
        Err("failed to open explorer".to_string())
    }
}

#[tauri::command]
fn scan(
    categories: Option<Vec<String>>,
    format: Option<String>,
    modified_only: Option<bool>,
) -> Result<String, String> {
    let mut cmd = vec![
        "-m".to_string(),
        "winstyles".to_string(),
        "scan".to_string(),
    ];

    if let Some(categories) = categories {
        for category in categories {
            cmd.push("-c".to_string());
            cmd.push(category);
        }
    }

    if let Some(format) = format {
        cmd.push("-f".to_string());
        cmd.push(format);
    }

    if modified_only.unwrap_or(false) {
        cmd.push("--modified-only".to_string());
    }

    run_command(&cmd)
}

#[tauri::command]
fn export_config(
    path: String,
    categories: Option<String>,
    include_defaults: Option<bool>,
) -> Result<String, String> {
    if path.trim().is_empty() {
        return Err("path is required".to_string());
    }

    let mut cmd = vec![
        "-m".to_string(),
        "winstyles".to_string(),
        "export".to_string(),
        path,
    ];

    if let Some(categories) = categories {
        for category in categories.split(',').map(|c| c.trim()).filter(|c| !c.is_empty()) {
            cmd.push("-c".to_string());
            cmd.push(category.to_string());
        }
    }

    if include_defaults.unwrap_or(false) {
        cmd.push("--include-defaults".to_string());
    }

    run_command(&cmd)
}

#[tauri::command]
fn import_config(
    path: String,
    dry_run: Option<bool>,
    skip_restore: Option<bool>,
) -> Result<String, String> {
    if path.trim().is_empty() {
        return Err("path is required".to_string());
    }

    let mut cmd = vec![
        "-m".to_string(),
        "winstyles".to_string(),
        "import".to_string(),
        path,
    ];

    if dry_run.unwrap_or(false) {
        cmd.push("--dry-run".to_string());
    }

    if skip_restore.unwrap_or(false) {
        cmd.push("--skip-restore-point".to_string());
    }

    run_command(&cmd)
}

#[tauri::command]
fn inspect(path: String) -> Result<String, String> {
    let cmd = vec![
        "-m".to_string(),
        "winstyles".to_string(),
        "inspect".to_string(),
        path,
        "-f".to_string(),
        "json".to_string(),
    ];

    run_command(&cmd)
}

#[tauri::command]
fn diff(path_a: String, path_b: String, show_all: Option<bool>) -> Result<String, String> {
    let mut cmd = vec![
        "-m".to_string(),
        "winstyles".to_string(),
        "diff".to_string(),
        path_a,
        path_b,
        "-f".to_string(),
        "json".to_string(),
    ];

    if show_all.unwrap_or(false) {
        cmd.push("--all".to_string());
    }

    run_command(&cmd)
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            scan,
            export_config,
            import_config,
            inspect,
            diff,
            open_output_folder
        ])
        .plugin(tauri_plugin_shell::init())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
