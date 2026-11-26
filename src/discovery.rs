use serde::Deserialize;
use std::path::PathBuf;
use crate::config::{root_dir, CATEGORIES};

#[derive(Clone, Debug)]
pub struct ToolEntry {
    pub name: String,
    pub desc: String,
    pub entry: PathBuf,
    pub runtime: String,
    pub cwd: PathBuf,
}

#[derive(Deserialize)]
struct ToolManifest {
    name: Option<String>,
    desc: Option<String>,
    entry: String,
    runtime: Option<String>,
}

const SUPPORTED_EXTS: &[&str] = &["py", "bat", "ps1", "sh", "js", "ts", "exe"];

pub fn discover_category_tools(folder: &str) -> Vec<ToolEntry> {
    let target = root_dir().join("scripts").join(folder);
    if !target.is_dir() {
        return Vec::new();
    }
    let mut entries: Vec<_> = match std::fs::read_dir(&target) {
        Ok(rd) => rd.filter_map(|e| e.ok()).collect(),
        Err(_) => return Vec::new(),
    };
    entries.sort_by_key(|e| e.file_name());

    let mut tools = Vec::new();
    for item in entries {
        let path = item.path();
        if path.is_file() {
            if let Some(ext) = path.extension().and_then(|s| s.to_str()) {
                let ext_l = ext.to_lowercase();
                if SUPPORTED_EXTS.contains(&ext_l.as_str()) {
                    let name = path.file_stem().and_then(|s| s.to_str()).unwrap_or("tool").to_string();
                    tools.push(ToolEntry {
                        name,
                        desc: format!("สคริปต์ {}", ext_l.to_uppercase()),
                        entry: path.clone(),
                        runtime: "auto".to_string(),
                        cwd: target.clone(),
                    });
                }
            }
        } else if path.is_dir() {
            let manifest = path.join("tool.json");
            if manifest.is_file() {
                if let Ok(raw) = std::fs::read_to_string(&manifest) {
                    if let Ok(meta) = serde_json::from_str::<ToolManifest>(&raw) {
                        let entry_path = path.join(&meta.entry);
                        if entry_path.exists() {
                            let dir_name = path.file_name().and_then(|s| s.to_str()).unwrap_or("plugin").to_string();
                            tools.push(ToolEntry {
                                name: meta.name.unwrap_or(dir_name),
                                desc: meta.desc.unwrap_or_else(|| "โมดูลปลั๊กอิน".to_string()),
                                entry: entry_path,
                                runtime: meta.runtime.unwrap_or_else(|| "auto".to_string()),
                                cwd: path,
                            });
                        }
                    }
                }
            }
        }
    }
    tools
}

pub fn discover_all_workspace_tools() -> Vec<ToolEntry> {
    let mut all = Vec::new();
    for &(_, _, _, folder, _, _) in CATEGORIES {
        all.extend(discover_category_tools(folder));
    }
    all
}
