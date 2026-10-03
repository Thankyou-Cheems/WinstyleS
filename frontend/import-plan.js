/* Import review is presentation only. Filters never change the applied package. */
(function (root) {
  "use strict";
  const categories = { fonts: "字体", terminal: "终端", theme: "主题", wallpaper: "壁纸", cursor: "鼠标指针", vscode: "VS Code" };
  const risks = { high: "高风险", medium: "中风险", low: "低风险" };
  const operations = { set_registry_value: "写入注册表", write_file: "写入文件", invoke_system_api: "调用系统 API", skip: "跳过", apply: "应用" };

  function escape(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  }

  function parseSummary(value) {
    const summary = typeof value === "string" ? JSON.parse(value) : value;
    if (!summary || !Array.isArray(summary.dry_run_plan)) throw new Error("预览响应缺少逐项计划");
    return summary;
  }

  function filterPlan(plan, category = "all", risk = "all", query = "") {
    const needle = query.trim().toLocaleLowerCase();
    return plan.filter(item => (category === "all" || item.category === category)
      && (risk === "all" || item.risk === risk)
      && [item.key, item.target, item.reason, categories[item.category] || item.category]
        .some(value => String(value ?? "").toLocaleLowerCase().includes(needle)));
  }

  function renderRows(plan) {
    if (!plan.length) return '<p class="plan-empty">没有符合筛选条件的配置项</p>';
    return plan.map(item => {
      const risk = Object.hasOwn(risks, item.risk) ? item.risk : "unknown";
      return `<article class="plan-item">
        <div class="plan-item-heading"><span class="plan-category">${escape(categories[item.category] || item.category)}</span>
          <span class="plan-risk plan-risk-${risk}">${escape(risks[risk] || "风险未知")}</span>
          <span class="plan-action">${item.action === "apply" ? "计划写入" : "跳过"}</span>
          ${item.requires_admin ? '<span class="plan-admin">需要管理员</span>' : ""}</div>
        <h3 class="plan-key">${escape(item.key)}</h3>
        <dl class="plan-details"><dt>操作</dt><dd>${escape(operations[item.operation] || item.operation)}</dd>
          <dt>包内来源路径</dt><dd class="plan-target">${escape(item.target || "未提供")}</dd>
          <dt>原因</dt><dd>${escape(item.reason)}${item.risk_reason ? ` · ${escape(item.risk_reason)}` : ""}</dd></dl>
      </article>`;
    }).join("");
  }

  function mount(container, value) {
    const summary = parseSummary(value);
    const plan = summary.dry_run_plan;
    const writable = plan.filter(item => item.action === "apply").length;
    const high = plan.filter(item => item.risk === "high").length;
    const needsAdmin = plan.some(item => item.requires_admin);
    const categoryNames = [...new Set(plan.map(item => item.category))];
    container.innerHTML = `<div class="plan-summary">
        <div><strong>${plan.length}</strong><span>配置项</span></div><div><strong>${writable}</strong><span>计划写入</span></div>
        <div><strong>${plan.length - writable}</strong><span>跳过</span></div><div><strong>${high}</strong><span>高风险</span></div></div>
      <p class="plan-notice">预览已完成，尚未应用。${needsAdmin ? "部分项需要管理员权限。" : ""}来源路径取自配置包，资源路径可能在导入时迁移；此计划不保证跨设备兼容或自动回滚。</p>
      <div class="plan-filters"><label>类别<select class="form-input" data-plan-category><option value="all">全部类别</option>
        ${categoryNames.map(name => `<option value="${escape(name)}">${escape(categories[name] || name)}</option>`).join("")}</select></label>
        <label>风险<select class="form-input" data-plan-risk><option value="all">全部风险</option><option value="high">高风险</option><option value="medium">中风险</option><option value="low">低风险</option></select></label>
        <label class="plan-search">搜索<input class="form-input" type="search" data-plan-query placeholder="配置项、路径或原因" /></label></div>
      <p class="plan-count" data-plan-count role="status"></p><div class="plan-list" data-plan-list></div>
      <details class="plan-raw"><summary>查看原始计划 JSON</summary><pre>${escape(JSON.stringify(summary, null, 2))}</pre></details>`;
    const category = container.querySelector("[data-plan-category]");
    const risk = container.querySelector("[data-plan-risk]");
    const query = container.querySelector("[data-plan-query]");
    function update() {
      const visible = filterPlan(plan, category.value, risk.value, query.value);
      container.querySelector("[data-plan-list]").innerHTML = renderRows(visible);
      container.querySelector("[data-plan-count]").textContent = `显示 ${visible.length} / ${plan.length} 项 · 筛选仅影响展示，导入仍处理整个配置包`;
    }
    category.addEventListener("change", update);
    risk.addEventListener("change", update);
    query.addEventListener("input", update);
    update();
    return summary;
  }

  const api = { parseSummary, filterPlan, renderRows, mount };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.WinstyleSImportPlan = api;
})(globalThis);
