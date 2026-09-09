"use strict";

const state = {
  cursor: null,
  nextCursor: null,
  cursorHistory: [],
  page: 1,
  hasMore: false,
  loading: false,
  filters: {},
  selected: new Set(),
  pendingDelete: [],
  download: null,
  retryFiles: [],
};
const elements = {
  headerActions: document.querySelector(".header-actions"),
  recordsTab: document.querySelector("#records-tab"),
  apiDocsTab: document.querySelector("#api-docs-tab"),
  recordsView: document.querySelector("#records-view"),
  apiDocsView: document.querySelector("#api-docs-view"),
  loginLayer: document.querySelector("#login-layer"),
  loginForm: document.querySelector("#login-form"),
  loginError: document.querySelector("#login-error"),
  password: document.querySelector("#dashboard-password"),
  loginDocs: document.querySelector("#login-docs-button"),
  logout: document.querySelector("#logout-button"),
  refresh: document.querySelector("#refresh-button"),
  reset: document.querySelector("#reset-button"),
  filterForm: document.querySelector("#filter-form"),
  status: document.querySelector("#status-filter"),
  query: document.querySelector("#query-filter"),
  hotspot: document.querySelector("#hotspot-filter"),
  period: document.querySelector("#period-filter"),
  limit: document.querySelector("#limit-filter"),
  rows: document.querySelector("#task-rows"),
  selectAll: document.querySelector("#select-all"),
  selectionBar: document.querySelector("#selection-bar"),
  selectedCount: document.querySelector("#selected-count"),
  deleteSelected: document.querySelector("#delete-selected-button"),
  deleteDialog: document.querySelector("#delete-dialog"),
  deleteSummary: document.querySelector("#delete-summary"),
  confirmDelete: document.querySelector("#confirm-delete-button"),
  cancelDelete: document.querySelector("#cancel-delete-button"),
  empty: document.querySelector("#empty-state"),
  message: document.querySelector("#message"),
  connection: document.querySelector("#connection-state"),
  updated: document.querySelector("#updated-at"),
  previous: document.querySelector("#previous-button"),
  next: document.querySelector("#next-button"),
  page: document.querySelector("#page-label"),
  metrics: {
    total: document.querySelector("#metric-total"),
    pending: document.querySelector("#metric-pending"),
    completed: document.querySelector("#metric-completed"),
    failed: document.querySelector("#metric-failed"),
  },
};

const dateRange = new DateRangePicker(document.getElementById("date-range-filter"));

function text(value, fallback = "—") { return value === null || value === undefined || value === "" ? fallback : String(value); }
function formatDate(value) {
  if (!value) return "—";
  const timestamp = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value) ? value : `${value}Z`;
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Shanghai" }).format(new Date(timestamp));
}
function statusLabel(value) { return { pending: "待处理", completed: "已完成", failed: "失败" }[value] || value; }
function resultArtifacts(task) {
  const urls = task.latest_result?.artifact_urls || [];
  return {
    directory: urls[0] || "",
    html: urls[1] || "",
    pptx: urls[2] || "",
  };
}
function resultUrl(task) { return resultArtifacts(task).directory; }
function resultLink(url, label, className = "") {
  const link = document.createElement("a");
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = label;
  if (className) link.className = className;
  return link;
}
async function downloadBlob(event, url, fallbackFilename) {
  event.preventDefault();
  if (event.currentTarget.getAttribute("aria-disabled") === "true") return;
  const link = event.currentTarget;
  const originalLabel = link.textContent;
  link.classList.add("result-download-loading");
  link.setAttribute("aria-disabled", "true");
  link.textContent = "下载中…";
  try {
    const type = fallbackFilename.endsWith(".pptx") ? "pptx" : "html";
    const bytes = await ReportDownloads.file(url, type, new AbortController().signal);
    ReportDownloads.save(new Blob([bytes]), ReportDownloads.filename(url, type));
  } catch (error) {
    setMessage(`报告下载失败：${error.message}`);
  } finally {
    link.classList.remove("result-download-loading");
    link.removeAttribute("aria-disabled");
    link.textContent = originalLabel;
  }
}
function appendResultLinks(parent, task) {
  const artifacts = resultArtifacts(task);
  if (!artifacts.directory) {
    parent.textContent = "—";
    return;
  }
  parent.append(resultLink(artifacts.directory, artifacts.directory, "result-link"));
  if (!artifacts.html && !artifacts.pptx) return;
  const downloads = document.createElement("div");
  downloads.className = "result-downloads";
  if (artifacts.html) {
    const htmlDownload = resultLink(
      artifacts.html,
      "下载报告",
      "result-download result-download-html",
    );
    htmlDownload.addEventListener("click", (event) => {
      downloadBlob(event, artifacts.html, "source_understanding_review.html");
    });
    downloads.append(htmlDownload);
  }
  if (artifacts.pptx) {
    const ppt = resultLink(artifacts.pptx, "下载PPT", "result-download result-download-pptx");
    ppt.addEventListener("click", (event) => downloadBlob(event, artifacts.pptx, "single_page_tech_report.pptx"));
    downloads.append(ppt);
  }
  parent.append(downloads);
}
function setMessage(message = "", tone = "error") {
  elements.message.textContent = message;
  elements.message.hidden = !message;
  elements.message.classList.toggle("message-success", tone === "success");
}
function setOnline(online) {
  elements.connection.textContent = online ? "已连接资料服务器" : "连接已断开";
  elements.connection.classList.toggle("online", online);
}
function showLogin(message = "") {
  state.download?.controller.abort();
  state.retryFiles = [];
  state.selected.clear();
  updateSelectionState();
  document.getElementById("retry-download-button").hidden = true;
  elements.loginLayer.hidden = false;
  elements.loginError.textContent = message;
  elements.loginError.hidden = !message;
  setOnline(false);
}
function hideLogin() {
  elements.loginLayer.hidden = true;
  elements.loginError.hidden = true;
}
function showView(view) {
  const showDocs = view === "docs";
  elements.recordsView.hidden = showDocs;
  elements.apiDocsView.hidden = !showDocs;
  elements.recordsTab.classList.toggle("active", !showDocs);
  elements.apiDocsTab.classList.toggle("active", showDocs);
  elements.recordsTab.setAttribute("aria-selected", String(!showDocs));
  elements.apiDocsTab.setAttribute("aria-selected", String(showDocs));
  elements.headerActions.hidden = showDocs;

  if (showDocs) {
    elements.loginLayer.hidden = true;
  } else if (elements.loginLayer.hidden === false) {
    showLogin();
  }
}
function resetPaging() {
  state.cursor = null;
  state.nextCursor = null;
  state.cursorHistory = [];
  state.page = 1;
}
function updateSelectionState() {
  const checkboxes = Array.from(elements.rows.querySelectorAll(".row-select"));
  const checkedCount = checkboxes.filter((checkbox) => checkbox.checked).length;
  elements.selectedCount.textContent = String(state.selected.size);
  elements.selectionBar.hidden = state.selected.size === 0;
  elements.selectAll.checked = checkboxes.length > 0 && checkedCount === checkboxes.length;
  elements.selectAll.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
  elements.selectAll.disabled = checkboxes.length === 0;
  elements.deleteSelected.disabled = Boolean(state.download && [...state.selected].some((id) => state.download.ids.has(id)));
  document.getElementById("download-selected-button").disabled = Boolean(state.download) || state.selected.size === 0;
}
function openDeleteDialog(taskIds) {
  if (state.download && taskIds.some((id) => state.download.ids.has(id))) return;
  state.pendingDelete = [...new Set(taskIds)];
  if (!state.pendingDelete.length) return;
  elements.deleteSummary.textContent = state.pendingDelete.length === 1
    ? `将永久删除任务 ${state.pendingDelete[0]}。`
    : `将永久删除选中的 ${state.pendingDelete.length} 个任务。`;
  elements.deleteDialog.showModal();
}
function captureFilters() {
  state.filters = { status: elements.status.value, q: elements.query.value.trim(),
    hotspot_id: elements.hotspot.value.trim(), period: elements.period.value.trim(),
    updated_from: dateRange.startInput.value, updated_to: dateRange.endInput.value };
}
function queryString() {
  const params = new URLSearchParams({ limit: elements.limit.value, sort: "updated_desc" });
  Object.entries(state.filters).forEach(([key, value]) => { if (value) params.set(key, value); });
  if (state.cursor !== null) params.set("page_token", state.cursor);
  return params.toString();
}
function appendDetail(parent, label, value, wide = false) {
  const block = document.createElement("div");
  block.className = `detail-block${wide ? " detail-block-wide" : ""}`;
  const title = document.createElement("span");
  title.className = "detail-label";
  title.textContent = label;
  const body = document.createElement("p");
  body.className = "detail-value";
  body.textContent = text(value);
  block.append(title, body);
  parent.append(block);
  return body;
}
function detailRow(task) {
  const row = document.createElement("tr");
  row.className = "detail-row";
  row.hidden = true;
  const cell = document.createElement("td");
  cell.colSpan = 10;
  const grid = document.createElement("div");
  grid.className = "detail-grid";
  appendDetail(grid, "任务正文", task.content, true);
  appendDetail(grid, "指定分类", task.category || "由 AI 自动分类", true);
  const source = appendDetail(grid, "来源 URL", "");
  const link = document.createElement("a");
  link.href = task.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = task.url;
  source.append(link);
  appendDetail(grid, "创建时间", formatDate(task.created_at));
  appendDetail(grid, "更新时间", formatDate(task.updated_at));
  const result = appendDetail(grid, "结果 URL", "", true);
  appendResultLinks(result, task);
  cell.append(grid);
  row.append(cell);
  return row;
}
function taskRow(task) {
  const row = document.createElement("tr");
  row.dataset.rowNumber = String(task.row_number);
  const detail = detailRow(task);
  const selectCell = document.createElement("td");
  selectCell.className = "select-cell";
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.className = "row-select";
  checkbox.dataset.taskId = task.task_id;
  checkbox.setAttribute("aria-label", `选择任务 ${task.task_id}`);
  checkbox.addEventListener("change", () => {
    if (checkbox.checked && state.selected.size >= 200) { checkbox.checked = false; setMessage("最多选择 200 个任务。"); }
    if (checkbox.checked) state.selected.add(task.task_id);
    else state.selected.delete(task.task_id);
    updateSelectionState();
  });
  selectCell.append(checkbox);
  row.append(selectCell);
  const values = [
    text(task.row_number), task.task_id, task.status, task.hotspot_id, task.period,
    task.content, formatDate(task.updated_at), resultUrl(task), "",
  ];
  values.forEach((value, index) => {
    const cell = document.createElement("td");
    if (index === 1) cell.className = "task-id";
    if (index === 2) {
      const badge = document.createElement("span");
      badge.className = `status status-${task.status}`;
      badge.textContent = statusLabel(task.status);
      cell.append(badge);
    } else if (index === 7) {
      if (value) {
        appendResultLinks(cell, task);
      } else {
        cell.textContent = "—";
      }
    } else if (index === 5) {
      const preview = document.createElement("span");
      preview.className = "content-preview";
      preview.textContent = text(value);
      cell.append(preview);
    } else if (index === 8) {
      const actions = document.createElement("div");
      actions.className = "row-actions";
      const detailButton = document.createElement("button");
      detailButton.type = "button";
      detailButton.className = "detail-button";
      detailButton.textContent = "详情";
      detailButton.addEventListener("click", () => {
        detail.hidden = !detail.hidden;
        detailButton.textContent = detail.hidden ? "详情" : "收起";
      });
      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.dataset.taskId = task.task_id;
      deleteButton.disabled = Boolean(state.download?.ids.has(task.task_id));
      deleteButton.className = "delete-row-button";
      deleteButton.textContent = "删除";
      deleteButton.addEventListener("click", () => openDeleteDialog([task.task_id]));
      actions.append(detailButton, deleteButton);
      cell.append(actions);
      row.append(cell);
      return;
    } else {
      cell.textContent = text(value);
    }
    row.append(cell);
  });
  return { row, detail };
}
function render(tasks, pagination) {
  elements.rows.replaceChildren();
  document.querySelector(".table-scroll").scrollTop = 0;
  state.selected.clear();
  tasks.forEach((task) => {
    const rendered = taskRow(task);
    elements.rows.append(rendered.row, rendered.detail);
  });
  elements.empty.hidden = tasks.length !== 0;
  const counts = { pending: 0, completed: 0, failed: 0 };
  tasks.forEach((task) => { if (counts[task.status] !== undefined) counts[task.status] += 1; });
  elements.metrics.total.textContent = String(tasks.length);
  Object.keys(counts).forEach((key) => { elements.metrics[key].textContent = String(counts[key]); });
  state.hasMore = Boolean(pagination?.has_more);
  state.nextCursor = pagination?.next_page_token || null;
  elements.next.disabled = !state.hasMore;
  elements.previous.disabled = state.cursorHistory.length === 0;
  elements.page.textContent = `第 ${state.page} 页`;
  updateSelectionState();
}
async function loadTasks() {
  if (state.loading) return;
  state.loading = true;
  dateRange.close();
  state.selected.clear();
  elements.rows.querySelectorAll(".row-select").forEach((checkbox) => { checkbox.checked = false; });
  updateSelectionState();
  elements.previous.disabled = true;
  elements.next.disabled = true;
  elements.filterForm.querySelectorAll("input, select, button").forEach((el) => { el.disabled = true; });
  elements.reset.disabled = true;
  elements.refresh.disabled = true;
  setMessage();
  try {
    const response = await fetch(`/api/v1/tasks?${queryString()}`, {
      cache: "no-store",
    });
    const payload = await response.json();
    if (response.status === 401) {
      showLogin("登录已失效，请重新输入密码。");
      return;
    }
    if (!response.ok || payload.status !== "success") throw new Error(payload.error?.message || `请求失败（${response.status}）`);
    render(payload.data, payload.pagination);
    setOnline(true);
    hideLogin();
    elements.updated.textContent = `更新于 ${new Intl.DateTimeFormat("zh-CN", { timeStyle: "medium" }).format(new Date())}`;
  } catch (error) {
    setOnline(false);
    setMessage(`数据加载失败：${error.message}`);
  } finally {
    state.loading = false;
    elements.refresh.disabled = false;
    elements.filterForm.querySelectorAll("input, select, button").forEach((el) => { el.disabled = false; });
    elements.reset.disabled = false;
    elements.previous.disabled = state.cursorHistory.length === 0;
    elements.next.disabled = !state.hasMore;
  }
}

async function deletePendingTasks() {
  const taskIds = [...state.pendingDelete];
  if (state.download && taskIds.some((id) => state.download.ids.has(id))) return;
  if (!taskIds.length) return;
  elements.confirmDelete.disabled = true;
  elements.cancelDelete.disabled = true;
  try {
    const isBatch = taskIds.length > 1;
    const headers = {};
    const options = { method: "DELETE", headers };
    let url = `/api/v1/tasks/${encodeURIComponent(taskIds[0])}`;
    if (isBatch) {
      url = "/api/v1/tasks";
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify({ task_ids: taskIds });
    }
    const response = await fetch(url, options);
    const payload = await response.json();
    if (response.status === 401) {
      elements.deleteDialog.close();
      showLogin("登录已失效，请重新输入密码。");
      return;
    }
    if (!response.ok || payload.status !== "success") {
      throw new Error(payload.error?.message || `删除失败（${response.status}）`);
    }
    const deletedCount = isBatch ? payload.data.deleted : Number(payload.data.deleted);
    elements.deleteDialog.close();
    await loadTasks();
    setMessage(`已删除 ${deletedCount} 个任务。`, "success");
  } catch (error) {
    elements.deleteDialog.close();
    setMessage(`删除失败：${error.message}`);
  } finally {
    elements.confirmDelete.disabled = false;
    elements.cancelDelete.disabled = false;
  }
}

elements.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = elements.password.value;
  if (!value) return;
  elements.loginError.hidden = true;
  try {
    const response = await fetch("/dashboard-auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: value }),
      cache: "no-store",
    });
    if (!response.ok) {
      showLogin(response.status === 401 ? "密码不正确，请重试。" : "登录暂不可用，请稍后重试。");
      return;
    }
    elements.password.value = "";
    resetPaging();
    await loadTasks();
  } catch (_error) {
    showLogin("无法连接服务器，请稍后重试。");
  }
});
elements.recordsTab.addEventListener("click", async () => {
  showView("records");
  await loadTasks();
});
elements.apiDocsTab.addEventListener("click", () => showView("docs"));
elements.loginDocs.addEventListener("click", () => showView("docs"));
document.getElementById("create-category").addEventListener("change", (event) => {
  const value = event.target.value;
  const literal = value ? "'" + value.replaceAll("'", "''") + "'" : "$null";
  const code = document.getElementById("code-create");
  code.textContent = code.textContent.replace(/^    category   = .*$/m, "    category   = " + literal);
});
document.querySelectorAll("[data-copy-target]").forEach((button) => {
  button.addEventListener("click", async () => {
    const originalLabel = button.textContent;
    const code = document.getElementById(button.dataset.copyTarget);
    try {
      await navigator.clipboard.writeText(code.textContent);
      button.textContent = "已复制";
      button.classList.add("copied");
    } catch (_error) {
      button.textContent = "复制失败";
    }
    window.setTimeout(() => {
      button.textContent = originalLabel;
      button.classList.remove("copied");
    }, 1600);
  });
});
elements.selectAll.addEventListener("change", () => {
  if (elements.selectAll.checked && elements.rows.querySelectorAll(".row-select").length > 200) { elements.selectAll.checked = false; setMessage("最多选择 200 个任务。"); return; }
  elements.rows.querySelectorAll(".row-select").forEach((checkbox) => {
    checkbox.checked = elements.selectAll.checked;
    if (checkbox.checked) state.selected.add(checkbox.dataset.taskId);
    else state.selected.delete(checkbox.dataset.taskId);
  });
  updateSelectionState();
});
elements.deleteSelected.addEventListener("click", () => openDeleteDialog([...state.selected]));
elements.cancelDelete.addEventListener("click", () => elements.deleteDialog.close());
elements.confirmDelete.addEventListener("click", deletePendingTasks);
elements.deleteDialog.addEventListener("close", () => { state.pendingDelete = []; });
elements.logout.addEventListener("click", async () => {
  state.download?.controller.abort();
  state.retryFiles = [];
  document.getElementById("retry-download-button").hidden = true;
  await fetch("/dashboard-auth/logout", { method: "POST", cache: "no-store" });
  elements.rows.replaceChildren();
  state.selected.clear();
  updateSelectionState();
  showLogin();
});
elements.filterForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.loading) return;
  captureFilters();
  resetPaging();
  await loadTasks();
});
elements.reset.addEventListener("click", async () => {
  if (state.loading) return;
  elements.filterForm.reset();
  dateRange.reset();
  captureFilters();
  resetPaging();
  await loadTasks();
});
elements.refresh.addEventListener("click", async () => { resetPaging(); await loadTasks(); });
elements.limit.addEventListener("change", async () => { resetPaging(); await loadTasks(); });
elements.next.addEventListener("click", async () => {
  if (state.loading || !state.hasMore) return;
  if (!state.nextCursor) return;
  state.cursorHistory.push(state.cursor);
  state.cursor = state.nextCursor;
  state.page += 1;
  await loadTasks();
});
elements.previous.addEventListener("click", async () => {
  if (state.loading || !state.cursorHistory.length) return;
  state.cursor = state.cursorHistory.pop();
  state.page -= 1;
  await loadTasks();
});

function downloadLocks() {
  document.querySelectorAll(".delete-row-button").forEach((button) => {
    button.disabled = Boolean(state.download?.ids.has(button.dataset.taskId));
  });
  updateSelectionState();
}

async function batchDownload(retry = false) {
  if (state.download || elements.deleteDialog.open) return;
  const types = document.getElementById("download-type").value;
  const requested = retry ? state.retryFiles.map((item) => ({ ...item }))
    : [...state.selected].flatMap((task_id) => (types === "all" ? ["html", "pptx"] : [types]).map((type) => ({ task_id, type })));
  if (!requested.length) return;
  const controller = new AbortController();
  const ids = new Set(requested.map((item) => item.task_id));
  state.download = { controller, ids };
  state.retryFiles = [];
  const progress = document.getElementById("download-progress");
  const list = document.getElementById("download-results");
  const cancel = document.getElementById("cancel-download-button");
  document.getElementById("download-panel").hidden = false;
  document.getElementById("retry-download-button").hidden = true;
  cancel.hidden = false;
  list.replaceChildren();
  downloadLocks();
  const records = [];
  const chunks = [];
  const budget = { bytes: 0 };
  let zipError;
  let fatal;
  const zip = new fflate.Zip((error, data) => { if (error) zipError = error; else chunks.push(data); });
  const names = new Set();
  function record(item, result, reason = "", name = "") {
    records.push({ task_id: item.task_id, type: item.type, filename: name, result, reason });
    if (result === "failed") state.retryFiles.push({ task_id: item.task_id, type: item.type });
    const li = document.createElement("li");
    li.textContent = `${item.task_id} / ${item.type}：${{ success: "成功", failed: "失败", skipped: "跳过" }[result]} ${reason}`;
    list.append(li);
    progress.textContent = `已处理 ${records.length}/${requested.length}，成功 ${records.filter((r) => r.result === "success").length}，失败 ${records.filter((r) => r.result === "failed").length}，跳过 ${records.filter((r) => r.result === "skipped").length}`;
  }
  try {
    const details = new Map();
    let refreshed = 0;
    progress.textContent = `正在核对任务 0/${ids.size}`;
    await ReportDownloads.pool([...ids], async (id) => {
      try { details.set(id, { task: await ReportDownloads.detail(id, controller.signal) }); }
      catch (error) {
        if (error.message === "HTTP 401") showLogin("登录已失效，请重新输入密码。");
        details.set(id, { error: error.message });
      }
      refreshed++;
      progress.textContent = `正在核对任务 ${refreshed}/${ids.size}`;
    }, controller.signal);
    controller.signal.throwIfAborted();
    const queue = [];
    for (const item of requested) {
      const found = details.get(item.task_id);
      if (found.error) { record(item, found.error === "HTTP 404" ? "skipped" : "failed", found.error); continue; }
      if (found.task.status !== "completed") { record(item, "skipped", "任务尚未完成"); continue; }
      const url = resultArtifacts(found.task)[item.type];
      if (!url) { record(item, "skipped", "缺少该类型文件链接"); continue; }
      queue.push({ ...item, url });
    }
    await ReportDownloads.pool(queue, async (item) => {
      try {
        const bytes = await ReportDownloads.file(item.url, item.type, controller.signal, budget);
        controller.signal.throwIfAborted();
        const original = ReportDownloads.filename(item.url, item.type);
        const directory = ReportDownloads.safeName(item.task_id);
        let name = `${directory}/${original}`;
        let suffix = 2;
        while (names.has(name)) { name = `${directory}/${original.replace(/(\.[^.]+)$/, `-${suffix++}$1`)}`; }
        names.add(name);
        const entry = new fflate.ZipPassThrough(name);
        zip.add(entry);
        entry.push(bytes, true);
        if (zipError) throw zipError;
        record(item, "success", "", name);
      } catch (error) {
        if (error.limit) { fatal = error.message; controller.abort(); }
        if (!controller.signal.aborted) record(item, "failed", error.message);
      }
    }, controller.signal);
    controller.signal.throwIfAborted();
    if (records.some((item) => item.result === "success")) {
      const manifest = new fflate.ZipPassThrough("manifest.json");
      zip.add(manifest);
      manifest.push(fflate.strToU8(JSON.stringify({ generated_at: new Date().toISOString(), items: records }, null, 2)), true);
      zip.end();
      if (zipError) throw zipError;
      ReportDownloads.save(new Blob(chunks, { type: "application/zip" }), ReportDownloads.zipName());
      progress.textContent += "。已生成 ZIP 并触发浏览器保存。";
    } else {
      progress.textContent += "。没有可下载文件，未生成 ZIP。";
    }
  } catch (error) {
    progress.textContent = fatal || (controller.signal.aborted ? "已取消下载，未生成 ZIP。" : `下载失败：${error.message}`);
  } finally {
    zip.terminate();
    chunks.length = 0;
    if (controller.signal.aborted) state.retryFiles = [];
    state.download = null;
    cancel.hidden = true;
    document.getElementById("retry-download-button").hidden = state.retryFiles.length === 0;
    downloadLocks();
  }
}

document.getElementById("download-selected-button").addEventListener("click", () => batchDownload());
document.getElementById("retry-download-button").addEventListener("click", () => batchDownload(true));
document.getElementById("cancel-download-button").addEventListener("click", () => state.download?.controller.abort());
captureFilters();
showView("records");
loadTasks();
