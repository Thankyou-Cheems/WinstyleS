const { test } = require("node:test");
const assert = require("node:assert/strict");
const { parseSummary, filterPlan, renderRows } = require("../../frontend/import-plan.js");

const plan = [
  { category: "theme", key: "theme.dark", risk: "high", action: "apply", operation: "set_registry_value", target: "HKCU\\fixture", requires_admin: false },
  { category: "terminal", key: "terminal.font", risk: "low", action: "apply", target: "C:\\fixture\\settings.json" },
  { category: "fonts", key: "inventory", risk: "low", action: "skip", reason: "只读项" },
];

test("composes category, risk and search filters without changing the package", () => {
  const snapshot = JSON.stringify(plan);
  assert.deepEqual(filterPlan(plan, "theme", "high", "HKCU"), [plan[0]]);
  assert.deepEqual(filterPlan(plan, "all", "low", "只读"), [plan[2]]);
  assert.deepEqual(filterPlan(plan, "terminal", "high"), []);
  assert.equal(JSON.stringify(plan), snapshot);
});

test("accepts structured or serialized plans and rejects text-only CLI responses", () => {
  const summary = { dry_run_plan: plan };
  assert.equal(parseSummary(summary), summary);
  assert.deepEqual(parseSummary(JSON.stringify(summary)), summary);
  assert.throws(() => parseSummary("Import completed"));
  assert.throws(() => parseSummary({ total: 3 }));
});

test("escapes package controlled text and refuses arbitrary risk class injection", () => {
  const html = renderRows([{ category: '<img src=x onerror=alert(1)>', key: '<script>bad()</script>', target: '" onmouseover="bad()', reason: "<svg onload=bad()>", risk: 'high" onclick="bad()', action: "skip" }]);
  assert.ok(!html.includes("<script>"));
  assert.ok(!html.includes("<img"));
  assert.ok(!html.includes("<svg"));
  assert.ok(html.includes("&lt;script&gt;"));
  assert.ok(html.includes("plan-risk-unknown"));
});

test("shows skip reasons, administrator requirements and empty states", () => {
  assert.ok(renderRows(plan).includes("只读项"));
  assert.ok(renderRows([{ ...plan[0], requires_admin: true }]).includes("需要管理员"));
  assert.ok(renderRows([]).includes("没有符合筛选条件"));
});
