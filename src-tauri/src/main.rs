#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::Deserialize;
use std::process::Command;

#[derive(Deserialize)]
struct ScanArgs {
    categories: Option<Vec<String>>,
    format: Option<String>,
    modified_only: Option<bool>,
}

#[derive(Deserialize)]
struct ExportArgs {
    path: String,
    categories: Option<String>,
    include_defaults: Option<bool>,
}

#[derive(Deserialize)]
struct ImportArgs {
    path: String,
    dry_run: Option<bool>,
    skip_restore: Option<bool>,
}

#[derive(Deserialize)]
struct InspectArgs {
    path: String,
}

#[derive(Deserialize)]
struct DiffArgs {
    path_a: String,
    path_b: String,
    show_all: Option<bool>,
}

fn python_cmd() -> String {
    std::env::var("PYTHON").unwrap_or_else(|_| "python".to_string())
}

fn run_command(args: &[String]) -> Result<String, String> {
    let output = Command::new(python_cmd())
        .args(args)
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
fn scan(args: ScanArgs) -> Result<String, String> {
    let mut cmd = vec![
        "-m".to_string(),
        "winstyles".to_string(),
        "scan".to_string(),
    ];

    if let Some(categories) = args.categories {
        for category in categories {
            cmd.push("-c".to_string());
            cmd.push(category);
        }
    }

    if let Some(format) = args.format {
        cmd.push("-f".to_string());
        cmd.push(format);
    }

    if args.modified_only.unwrap_or(false) {
        cmd.push("--modified-only".to_string());
    }

    run_command(&cmd)
}

#[tauri::command]
fn export_config(args: ExportArgs) -> Result<String, String> {
    if args.path.trim().is_empty() {
        return Err("path is required".to_string());
    }

    let mut cmd = vec![
        "-m".to_string(),
        "winstyles".to_string(),
        "export".to_string(),
        args.path,
    ];

    if let Some(categories) = args.categories {
        for category in categories.split(',').map(|c| c.trim()).filter(|c| !c.is_empty()) {
            cmd.push("-c".to_string());
            cmd.push(category.to_string());
        }
    }

    if args.include_defaults.unwrap_or(false) {
        cmd.push("--include-defaults".to_string());
    }

    run_command(&cmd)
}

#[tauri::command]
fn import_config(args: ImportArgs) -> Result<String, String> {
    if args.path.trim().is_empty() {
        return Err("path is required".to_string());
    }

    let mut cmd = vec![
        "-m".to_string(),
        "winstyles".to_string(),
        "import".to_string(),
        args.path,
    ];

    if args.dry_run.unwrap_or(false) {
        cmd.push("--dry-run".to_string());
    }

    if args.skip_restore.unwrap_or(false) {
        cmd.push("--skip-restore-point".to_string());
    }

    run_command(&cmd)
}

#[tauri::command]
fn inspect(args: InspectArgs) -> Result<String, String> {
    let mut cmd = vec![
        "-m".to_string(),
        "winstyles".to_string(),
        "inspect".to_string(),
        args.path,
        "-f".to_string(),
        "json".to_string(),
    ];

    run_command(&cmd)
}

#[tauri::command]
fn diff(args: DiffArgs) -> Result<String, String> {
    let mut cmd = vec![
        "-m".to_string(),
        "winstyles".to_string(),
        "diff".to_string(),
        args.path_a,
        args.path_b,
        "-f".to_string(),
        "json".to_string(),
    ];

    if args.show_all.unwrap_or(false) {
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
            diff
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
