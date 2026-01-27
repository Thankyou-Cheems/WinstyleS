/**
 * WinstyleS Frontend JavaScript
 * Handles UI interactions and Tauri backend communication
 */

document.addEventListener("DOMContentLoaded", () => {


  // DOM Elements
  const pages = document.querySelectorAll(".page");
  const navItems = document.querySelectorAll(".nav-item");
  const pageTitle = document.getElementById("pageTitle");
  const pageDesc = document.getElementById("pageDesc");
  const statusText = document.getElementById("statusText");

  // Page metadata
  const pageInfo = {
    scan: {
      title: "扫描",
      desc: "扫描系统个性化配置并生成差异数据"
    },
    report: {
      title: "分析报告",
      desc: "智能分析配置变更，识别开源字体"
    },
    updates: {
      title: "字体更新",
      desc: "检查已安装开源字体的最新版本"
    },
    export: {
      title: "导出",
      desc: "导出配置包，便于迁移与备份"
    },
    import: {
      title: "导入",
      desc: "从配置包恢复个性化设置"
    },
    settings: {
      title: "设置",
      desc: "管理应用偏好设置"
    }
  };

  // Status check
  setStatus("Web Mode (Local Server)");
  console.log("Running in Web Mode");

  // ============================================
  // Navigation
  // ============================================

  navItems.forEach((item) => {
    item.addEventListener("click", () => {
      const target = item.dataset.page;
      if (!target) return;

      // Update nav items
      navItems.forEach((btn) => btn.classList.remove("active"));
      item.classList.add("active");

      // Update pages
      pages.forEach((page) => page.classList.remove("active"));
      const targetPage = document.getElementById(`page-${target}`);
      if (targetPage) {
        targetPage.classList.add("active");
      }

      // Update header
      const info = pageInfo[target];
      if (info) {
        pageTitle.textContent = info.title;
        pageDesc.textContent = info.desc;
      }
    });
  });

  // ============================================
  // Utility Functions
  // ============================================

  function setStatus(text, isError = false) {
    const dot = document.querySelector(".status-dot");
    statusText.textContent = text;

    if (dot) {
      dot.style.background = isError ? "var(--danger)" : "var(--success)";
    }
  }

  function outputTo(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) {
      el.textContent = text;
    }
  }

  function appendOutput(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) {
      el.textContent += text;
    }
  }

  function getSelectedCategories(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];
    return Array.from(container.querySelectorAll("input[type=checkbox]:checked"))
      .map((c) => c.value);
  }

  function setButtonLoading(button, loading, originalText = null) {
    if (loading) {
      button.disabled = true;
      button._originalHTML = button.innerHTML;
      button.innerHTML = `
        <span class="loading">
          <span class="spinner"></span>
          处理中...
        </span>
      `;
    } else {
      button.disabled = false;
      button.innerHTML = button._originalHTML || originalText || "完成";
    }
  }

  async function invokeWeb(command, payload) {
    try {
      const response = await fetch(`/api/${command}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      console.error("Web invoke failed:", err);
      throw err;
    }
  }

  async function invokeOrWarn(command, payload, outputId) {
    try {
      return await invokeWeb(command, payload);
    } catch (err) {
      if (outputId) outputTo(outputId, `Web Interface Error: ${err}`);
      setStatus("Request Failed", true);
      return null;
    }
  }

  // ============================================
  // Chip Selection State
  // ============================================

  document.querySelectorAll(".chip").forEach((chip) => {
    const checkbox = chip.querySelector('input[type="checkbox"]');
    if (checkbox) {
      // Set initial state
      if (checkbox.checked) {
        chip.classList.add("selected");
      }

      checkbox.addEventListener("change", () => {
        chip.classList.toggle("selected", checkbox.checked);
      });
    }
  });

  // ============================================
  // Scan Page
  // ============================================

  const scanBtn = document.getElementById("scanBtn");
  const scanResults = document.getElementById("scanResults");

  scanBtn?.addEventListener("click", async () => {
    setStatus("扫描中...");
    setButtonLoading(scanBtn, true);

    const categories = getSelectedCategories("scanCategories");
    const modifiedOnly = document.getElementById("scanModifiedOnly")?.checked || false;

    // Use JSON format for data processing
    const format = "json";

    try {
      const result = await invokeOrWarn(
        "scan",
        { categories, format, modifiedOnly },
        "scanOutput"
      );

      if (result !== null) {
        renderScanTable(result);
        setStatus("扫描完成");
      }
    } catch (err) {
      console.error(err);
      scanResults.innerHTML = `
        <div class="empty-state">
           <p class="empty-title" style="color: var(--danger)">扫描出错</p>
           <p class="empty-desc">${err}</p>
        </div>
      `;
      setStatus("扫描失败", true);
    } finally {
      setButtonLoading(scanBtn, false);
    }
  });

  function renderScanTable(data) {
    let items = [];
    try {
      if (typeof data === "string") {
        // Check if it's already a JSON string (double encoded) or just string
        try {
          items = JSON.parse(data).items || [];
        } catch {
          // Try parsing the inner string if it's double encoded
          const inner = JSON.parse(data);
          if (typeof inner === "string") {
            items = JSON.parse(inner).items || [];
          } else {
            items = inner.items || [];
          }
        }
      } else {
        items = data.items || [];
      }
    } catch (e) {
      console.error("Parse error", e);
      items = [];
    }

    if (!items || items.length === 0) {
      scanResults.innerHTML = `
            <div class="empty-state">
                <p class="empty-title">未发现配置项</p>
                <p class="empty-desc">请尝试调整筛选条件</p>
            </div>
        `;
      return;
    }

    let html = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>类别</th>
                    <th>配置项</th>
                    <th>当前值</th>
                    <th>默认值</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
    `;

    items.forEach(item => {
      const isModified = item.change_type !== "default";

      // Status Badge
      let badgeClass = "badge-default";
      let statusText = "默认";

      if (item.change_type === "modified") {
        badgeClass = "badge-modified";
        statusText = "已修改";
      } else if (item.change_type === "added") {
        badgeClass = "badge-modified";
        statusText = "新增";
      } else if (item.change_type === "removed") {
        badgeClass = "badge-modified";
        statusText = "已移除";
      }

      const currentVal = formatValue(item.current_value);
      const defaultVal = formatValue(item.default_value);

      html += `
            <tr>
                <td><span class="badge" style="background: var(--surface-tertiary); color: var(--text-secondary)">${item.category}</span></td>
                <td title="${item.key}" style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${item.key}</td>
                <td title="${currentVal}" style="max-width: 150px; overflow: hidden; text-overflow: ellipsis;">${currentVal}</td>
                <td title="${defaultVal}" style="max-width: 150px; overflow: hidden; text-overflow: ellipsis; color: var(--text-tertiary)">${defaultVal}</td>
                <td><span class="badge ${badgeClass}">${statusText}</span></td>
            </tr>
        `;
    });

    html += `</tbody></table>`;
    scanResults.innerHTML = html;
  }

  function formatValue(val) {
    if (val === null || val === undefined) return "-";
    if (typeof val === "object") return JSON.stringify(val);
    return String(val);
  }

  // ============================================
  // Report Page
  // ============================================

  const generateReportBtn = document.getElementById("generateReportBtn");
  const reportOutput = document.getElementById("reportOutput");
  const reportPlaceholder = document.getElementById("reportPlaceholder");

  generateReportBtn?.addEventListener("click", async () => {
    setStatus("正在生成报告...");
    setButtonLoading(generateReportBtn, true);

    // Switch view
    reportPlaceholder.style.display = "none";
    reportOutput.style.display = "block";
    reportOutput.innerHTML = '<div class="loading" style="display:flex; justify-content:center; padding: 40px;"><span class="spinner"></span></div>';

    // Force HTML format for web view
    const format = "html";
    const checkUpdates = document.getElementById("checkFontUpdates")?.checked || true;

    try {
      const result = await invokeOrWarn(
        "generate_report",
        { format, checkUpdates },
        null
      );

      if (result !== null) {
        // Result is likely a JSON string containing the HTML string due to our backend wrapper
        let htmlContent = result;
        if (typeof result === "string" && (result.startsWith('"') || result.startsWith("'"))) {
          try {
            htmlContent = JSON.parse(result);
          } catch { }
        }

        reportOutput.innerHTML = htmlContent;
        setStatus("报告生成完成");
      }
    } catch (err) {
      reportOutput.innerHTML = `<div class="alert alert-error">生成失败: ${err}</div>`;
      setStatus("报告生成失败", true);
    } finally {
      setButtonLoading(generateReportBtn, false);
    }
  });

  // ============================================
  // Font Updates Page
  // ============================================

  const checkUpdatesBtn = document.getElementById("checkUpdatesBtn");
  const updatesList = document.getElementById("updatesList");

  checkUpdatesBtn?.addEventListener("click", async () => {
    setStatus("正在检查字体更新...");
    setButtonLoading(checkUpdatesBtn, true);

    // Show loading state
    updatesList.innerHTML = `
      <div class="empty-state">
        <span class="loading">
          <span class="spinner" style="width: 24px; height: 24px;"></span>
        </span>
        <p class="empty-title" style="margin-top: 16px;">正在扫描字体...</p>
        <p class="empty-desc">这可能需要几秒钟</p>
      </div>
    `;

    try {
      const result = await invokeOrWarn("check_font_updates", {}, null);

      if (result !== null) {
        renderUpdateResults(result);
        setStatus("更新检查完成");
      } else {
        showEmptyUpdates("未连接到后端，无法检查更新");
      }
    } catch (err) {
      showEmptyUpdates(`检查失败: ${err}`);
      setStatus("检查失败", true);
    } finally {
      setButtonLoading(checkUpdatesBtn, false);
    }
  });

  function renderUpdateResults(result) {
    // Parse the result (assuming it's JSON)
    let updates = [];
    try {
      if (typeof result === "string") {
        updates = JSON.parse(result);
      } else if (Array.isArray(result)) {
        updates = result;
      } else if (result.updates) {
        updates = result.updates;
      }
    } catch {
      updates = [];
    }

    if (!updates || updates.length === 0) {
      showEmptyUpdates("未检测到需要更新的字体", "all_up_to_date");
      return;
    }

    const hasUpdates = updates.filter(u => u.has_update);
    const noUpdates = updates.filter(u => !u.has_update);

    let html = '<div class="update-list">';

    // Show fonts with updates first
    if (hasUpdates.length > 0) {
      html += `<div class="update-section-title" style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">可更新 (${hasUpdates.length})</div>`;
      hasUpdates.forEach((item) => {
        html += createUpdateItem(item, true);
      });
    }

    // Show up-to-date fonts
    if (noUpdates.length > 0) {
      html += `<div class="update-section-title" style="font-size: 13px; color: var(--text-secondary); margin: 16px 0 8px;">已是最新 (${noUpdates.length})</div>`;
      noUpdates.forEach((item) => {
        html += createUpdateItem(item, false);
      });
    }

    html += '</div>';
    updatesList.innerHTML = html;

    // Add event listeners for download buttons
    updatesList.querySelectorAll(".btn-download").forEach((btn) => {
      btn.addEventListener("click", () => {
        const url = btn.dataset.url;
        if (url) {
          window.open(url, "_blank");
        }
      });
    });
  }

  function createUpdateItem(item, hasUpdate) {
    const statusClass = hasUpdate ? "has-update" : "up-to-date";
    const versionHtml = hasUpdate
      ? `<span class="update-item-version">${item.current_version || "未知"} → <span class="new">${item.latest_version}</span></span>`
      : `<span class="update-item-version">${item.current_version || item.latest_version || "已安装"}</span>`;

    const actionHtml = hasUpdate && item.download_url
      ? `<button class="btn-primary btn-sm btn-download" data-url="${item.download_url}">
           <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
             <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
             <polyline points="7 10 12 15 17 10"/>
             <line x1="12" y1="15" x2="12" y2="3"/>
           </svg>
           下载
         </button>`
      : "";

    return `
      <div class="update-item ${statusClass}">
        <div class="update-item-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="4 7 4 4 20 4 20 7"/>
            <line x1="9" y1="20" x2="15" y2="20"/>
            <line x1="12" y1="4" x2="12" y2="20"/>
          </svg>
        </div>
        <div class="update-item-info">
          <div class="update-item-name">${item.name || "未知字体"}</div>
          ${versionHtml}
        </div>
        <div class="update-item-actions">
          ${actionHtml}
        </div>
      </div>
    `;
  }

  function showEmptyUpdates(message, type = "default") {
    const iconSvg = type === "all_up_to_date"
      ? `<svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="1.5">
           <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
           <polyline points="22 4 12 14.01 9 11.01"/>
         </svg>`
      : `<svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
           <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
           <polyline points="7 10 12 15 17 10"/>
           <line x1="12" y1="15" x2="12" y2="3"/>
         </svg>`;

    const title = type === "all_up_to_date" ? "所有字体都是最新版本" : "";

    updatesList.innerHTML = `
      <div class="empty-state">
        ${iconSvg}
        <p class="empty-title">${title}</p>
        <p class="empty-desc">${message}</p>
      </div>
    `;
  }

  // ============================================
  // Export Page
  // ============================================

  const exportBtn = document.getElementById("exportBtn");
  const exportResultContainer = document.getElementById("exportResultContainer");

  exportBtn?.addEventListener("click", async () => {
    setStatus("导出中...");
    setButtonLoading(exportBtn, true);

    const path = document.getElementById("exportPath")?.value.trim() || "";
    const categories = getSelectedCategories("exportCategories").join(",");
    const includeDefaults = document.getElementById("exportIncludeDefaults")?.checked || false;
    const includeFontFiles = document.getElementById("exportIncludeFontFiles")?.checked || false;

    if (!path) {
      if (exportResultContainer) {
        exportResultContainer.innerHTML = `
          <div class="empty-state" style="padding: 32px 0;">
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" stroke-width="1.5" style="width: 48px; height: 48px;">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <p class="empty-title">请输入导出路径</p>
            <p class="empty-desc">在上方输入导出文件的保存路径</p>
          </div>
        `;
      }
      setStatus("请输入导出路径", true);
      setButtonLoading(exportBtn, false);
      return;
    }

    // Show loading state
    if (exportResultContainer) {
      exportResultContainer.innerHTML = `
        <div class="empty-state" style="padding: 32px 0;">
          <span class="loading">
            <span class="spinner" style="width: 32px; height: 32px;"></span>
          </span>
          <p class="empty-title" style="margin-top: 16px;">正在导出...</p>
          <p class="empty-desc">正在打包配置文件</p>
        </div>
      `;
    }

    try {
      const result = await invokeOrWarn(
        "export_config",
        { path, categories, includeDefaults, includeFontFiles },
        null
      );

      if (result !== null) {
        if (exportResultContainer) {
          exportResultContainer.innerHTML = `
            <div class="empty-state" style="padding: 32px 0;">
              <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="1.5" style="width: 48px; height: 48px;">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <p class="empty-title" style="color: var(--success);">导出成功</p>
              <p class="empty-desc">${path}</p>
            </div>
          `;
        }
        setStatus("导出完成");
      }
    } catch (err) {
      if (exportResultContainer) {
        exportResultContainer.innerHTML = `
          <div class="empty-state" style="padding: 32px 0;">
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="1.5" style="width: 48px; height: 48px;">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <p class="empty-title" style="color: var(--danger);">导出失败</p>
            <p class="empty-desc">${err}</p>
          </div>
        `;
      }
      setStatus("导出失败", true);
    } finally {
      setButtonLoading(exportBtn, false);
    }
  });

  // ============================================
  // Import Page
  // ============================================

  const importBtn = document.getElementById("importBtn");
  const importDryRunBtn = document.getElementById("importDryRunBtn");

  async function runImport(dryRun) {
    const btn = dryRun ? importDryRunBtn : importBtn;
    const statusPrefix = dryRun ? "预览" : "导入";

    setStatus(`${statusPrefix}中...`);
    setButtonLoading(btn, true);

    const path = document.getElementById("importPath")?.value.trim() || "";
    const skipRestore = document.getElementById("importSkipRestore")?.checked || false;

    if (!path) {
      outputTo("importOutput", "请输入配置包路径");
      setStatus("请输入配置包路径", true);
      setButtonLoading(btn, false);
      return;
    }

    try {
      const result = await invokeOrWarn(
        "import_config",
        { path, dryRun, skipRestore },
        "importOutput"
      );

      if (result !== null) {
        outputTo("importOutput", result);
        setStatus(`${statusPrefix}完成`);
      }
    } catch (err) {
      outputTo("importOutput", `${statusPrefix}失败: ${err}`);
      setStatus(`${statusPrefix}失败`, true);
    } finally {
      setButtonLoading(btn, false);
    }
  }

  importBtn?.addEventListener("click", () => runImport(false));
  importDryRunBtn?.addEventListener("click", () => runImport(true));

  // ============================================
  // Open Folder Button
  // ============================================

  document.getElementById("openFolder")?.addEventListener("click", async () => {
    try {
      await invokeWeb("open_output_folder", {});
      setStatus("已打开输出目录");
    } catch (err) {
      console.error(err);
      setStatus("打开目录失败", true);
    }
  });

  // ============================================
  // Copy Output Buttons
  // ============================================

  document.getElementById("copyOutput")?.addEventListener("click", () => {
    copyToClipboard("scanOutput");
  });

  document.getElementById("copyReport")?.addEventListener("click", () => {
    copyToClipboard("reportOutput");
  });

  async function copyToClipboard(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;

    try {
      await navigator.clipboard.writeText(el.textContent);
      setStatus("已复制到剪贴板");
    } catch {
      setStatus("复制失败", true);
    }
  }

  // ============================================
  // Settings Page
  // ============================================

  const themeMode = document.getElementById("themeMode");

  themeMode?.addEventListener("change", () => {
    const mode = themeMode.value;
    // Note: actual theme switching would require more implementation
    // This is a placeholder for future functionality
    console.log("Theme mode changed to:", mode);
  });

  // ============================================
  // Browse Path Buttons (Future Implementation)
  // ============================================

  document.getElementById("browseExportPath")?.addEventListener("click", () => {
    setStatus("Web模式下不支持浏览，请手动输入路径", true);
  });

  document.getElementById("browseImportPath")?.addEventListener("click", () => {
    setStatus("Web模式下不支持浏览，请手动输入路径", true);
  });

  // ============================================
  // Export Preset Cards
  // ============================================

  document.querySelectorAll(".preset-card").forEach((card) => {
    card.addEventListener("click", () => {
      // Remove active from all preset cards
      document.querySelectorAll(".preset-card").forEach((c) => c.classList.remove("active"));
      card.classList.add("active");

      const preset = card.dataset.preset;
      const exportCategories = document.getElementById("exportCategories");

      // Update checkboxes based on preset
      if (exportCategories) {
        const checkboxes = exportCategories.querySelectorAll('input[type="checkbox"]');

        switch (preset) {
          case "full":
            checkboxes.forEach((cb) => {
              cb.checked = true;
              cb.closest(".chip")?.classList.add("selected");
            });
            break;
          case "fonts":
            checkboxes.forEach((cb) => {
              cb.checked = cb.value === "fonts";
              cb.closest(".chip")?.classList.toggle("selected", cb.checked);
            });
            break;
          case "terminal":
            checkboxes.forEach((cb) => {
              cb.checked = cb.value === "terminal";
              cb.closest(".chip")?.classList.toggle("selected", cb.checked);
            });
            break;
          case "share":
            checkboxes.forEach((cb) => {
              cb.checked = cb.value === "fonts" || cb.value === "terminal";
              cb.closest(".chip")?.classList.toggle("selected", cb.checked);
            });
            // Enable include font files for share
            const fontFilesCheck = document.getElementById("exportIncludeFontFiles");
            if (fontFilesCheck) fontFilesCheck.checked = false;
            break;
        }
      }

      setStatus(`已选择预设: ${card.querySelector(".preset-title").textContent}`);
    });
  });

  // ============================================
  // Import Drop Zone
  // ============================================

  const dropZone = document.getElementById("importDropZone");
  const importPath = document.getElementById("importPath");

  if (dropZone && importPath) {
    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => {
      dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("drag-over");

      const files = e.dataTransfer?.files;
      if (files && files.length > 0) {
        const file = files[0];
        // In web mode, we can't get the full path, but we can show the filename
        importPath.value = file.name;
        setStatus(`已选择文件: ${file.name}`);
      }
    });

    dropZone.addEventListener("click", () => {
      // Create a hidden file input for click-to-browse
      const input = document.createElement("input");
      input.type = "file";
      input.accept = ".zip";
      input.onchange = (e) => {
        const file = e.target.files?.[0];
        if (file) {
          importPath.value = file.name;
          setStatus(`已选择文件: ${file.name}`);
        }
      };
      input.click();
    });
  }

  // ============================================
  // Chip Selection in Export Categories
  // ============================================

  document.querySelectorAll("#exportCategories .chip").forEach((chip) => {
    const checkbox = chip.querySelector('input[type="checkbox"]');
    if (checkbox) {
      if (checkbox.checked) {
        chip.classList.add("selected");
      }

      checkbox.addEventListener("change", () => {
        chip.classList.toggle("selected", checkbox.checked);
        // Deselect any active preset card when manually changing
        document.querySelectorAll(".preset-card").forEach((c) => c.classList.remove("active"));
      });
    }
  });

  // ============================================
  // Keyboard Shortcuts
  // ============================================

  document.addEventListener("keydown", (e) => {
    // Ctrl+1-6 for quick page navigation
    if (e.ctrlKey && e.key >= "1" && e.key <= "6") {
      e.preventDefault();
      const index = parseInt(e.key) - 1;
      const navItem = navItems[index];
      if (navItem) {
        navItem.click();
      }
    }

    // Escape to clear focus
    if (e.key === "Escape") {
      document.activeElement?.blur();
    }
  });
});
