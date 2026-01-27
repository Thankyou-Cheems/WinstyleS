document.addEventListener("DOMContentLoaded", () => {
  const tauri = window.__TAURI__ || null;
  const invoke =
    tauri && tauri.core && typeof tauri.core.invoke === "function"
      ? tauri.core.invoke
      : null;

  const pages = document.querySelectorAll(".page");
  const navItems = document.querySelectorAll(".nav-item");
  const pageTitle = document.getElementById("pageTitle");
  const pageDesc = document.getElementById("pageDesc");
  const statusText = document.getElementById("statusText");

  const descriptions = {
    scan: "扫描系统个性化配置并生成报告",
    export: "导出配置包，便于迁移与备份",
    import: "从配置包恢复个性化设置",
    inspect: "检视配置包元信息",
    diff: "对比两个配置包差异",
  };

  if (!invoke) {
    statusText.textContent = "前端未连接到 Tauri 后端";
  }

  navItems.forEach((item) => {
    item.addEventListener("click", () => {
      navItems.forEach((btn) => btn.classList.remove("active"));
      item.classList.add("active");
      const target = item.dataset.page;
      pages.forEach((page) => page.classList.remove("active"));
      document.getElementById(`page-${target}`).classList.add("active");
      pageTitle.textContent = item.textContent.trim();
      pageDesc.textContent = descriptions[target] || "";
    });
  });

  function setStatus(text) {
    statusText.textContent = text;
  }

  function outputTo(elementId, text) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = text;
  }

  function getSelectedCategories(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];
    return Array.from(container.querySelectorAll("input[type=checkbox]") || [])
      .filter((c) => c.checked)
      .map((c) => c.value);
  }

  async function invokeOrWarn(command, payload, outputId) {
    if (!invoke) {
      const message = "未连接到后端，无法执行命令。";
      outputTo(outputId, message);
      setStatus(message);
      return null;
    }

    try {
      return await invoke(command, payload);
    } catch (err) {
      throw err;
    }
  }

  document.getElementById("scanBtn").addEventListener("click", async () => {
    setStatus("扫描中...");
    const categories = getSelectedCategories("page-scan");
    const format = document.getElementById("scanFormat").value;
    const modifiedOnly = document.getElementById("scanModifiedOnly").checked;

    try {
      const result = await invokeOrWarn(
        "scan",
        { categories, format, modifiedOnly },
        "scanOutput"
      );
      if (result !== null) {
        outputTo("scanOutput", result);
        setStatus("扫描完成");
      }
    } catch (err) {
      outputTo("scanOutput", `扫描失败: ${err}`);
      setStatus("扫描失败");
    }
  });

  document.getElementById("exportBtn").addEventListener("click", async () => {
    setStatus("导出中...");
    const path = document.getElementById("exportPath").value.trim();
    const categories = document
      .getElementById("exportCategories")
      .value.trim();
    const includeDefaults = document.getElementById(
      "exportIncludeDefaults"
    ).checked;

    try {
      const result = await invokeOrWarn(
        "export_config",
        { path, categories, includeDefaults },
        "exportOutput"
      );
      if (result !== null) {
        outputTo("exportOutput", result);
        setStatus("导出完成");
      }
    } catch (err) {
      outputTo("exportOutput", `导出失败: ${err}`);
      setStatus("导出失败");
    }
  });

  document.getElementById("importBtn").addEventListener("click", async () => {
    setStatus("导入中...");
    const path = document.getElementById("importPath").value.trim();
    const dryRun = document.getElementById("importDryRun").checked;
    const skipRestore = document.getElementById("importSkipRestore").checked;

    try {
      const result = await invokeOrWarn(
        "import_config",
        { path, dryRun, skipRestore },
        "importOutput"
      );
      if (result !== null) {
        outputTo("importOutput", result);
        setStatus("导入完成");
      }
    } catch (err) {
      outputTo("importOutput", `导入失败: ${err}`);
      setStatus("导入失败");
    }
  });

  document.getElementById("inspectBtn").addEventListener("click", async () => {
    setStatus("检视中...");
    const path = document.getElementById("inspectPath").value.trim();

    try {
      const result = await invokeOrWarn(
        "inspect",
        { path },
        "inspectOutput"
      );
      if (result !== null) {
        outputTo("inspectOutput", result);
        setStatus("检视完成");
      }
    } catch (err) {
      outputTo("inspectOutput", `检视失败: ${err}`);
      setStatus("检视失败");
    }
  });

  document.getElementById("diffBtn").addEventListener("click", async () => {
    setStatus("对比中...");
    const pathA = document.getElementById("diffPathA").value.trim();
    const pathB = document.getElementById("diffPathB").value.trim();
    const showAll = document.getElementById("diffShowAll").checked;

    try {
      const result = await invokeOrWarn(
        "diff",
        { pathA, pathB, showAll },
        "diffOutput"
      );
      if (result !== null) {
        outputTo("diffOutput", result);
        setStatus("对比完成");
      }
    } catch (err) {
      outputTo("diffOutput", `对比失败: ${err}`);
      setStatus("对比失败");
    }
  });

  document.getElementById("openFolder").addEventListener("click", async () => {
    if (!invoke) {
      setStatus("无法打开目录（未连接后端）");
      return;
    }

    try {
      await invoke("open_output_folder");
    } catch (err) {
      setStatus("无法打开目录");
    }
  });
});
