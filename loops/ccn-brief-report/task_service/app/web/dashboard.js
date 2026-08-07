"use strict";

const TOKEN_KEY = "ccn-dashboard-bearer";
const state = {
  cursor: null,
  cursorHistory: [],
  page: 1,
  hasMore: false,
  loading: false,
  selected: new Set(),
  pendingDelete: [],
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
  apiKey: document.querySelector("#api-key"),
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

function token() { return sessionStorage.getItem(TOKEN_KEY) || ""; }
function text(value, fallback = "—") { return value === null || value === undefined || value === "" ? fallback : String(value); }
function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}
function statusLabel(value) { return { pending: "待处理", completed: "已完成", failed: "失败" }[value] || value; }
function resultUrl(task) { return task.latest_result?.artifact_urls?.[0] || ""; }
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
  } else if (!token()) {
    showLogin();
  }
}
function resetPaging() {
  state.cursor = null;
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
}
function openDeleteDialog(taskIds) {
  state.pendingDelete = [...new Set(taskIds)];
  if (!state.pendingDelete.length) return;
  elements.deleteSummary.textContent = state.pendingDelete.length === 1
    ? `将永久删除任务 ${state.pendingDelete[0]}。`
    : `将永久删除选中的 ${state.pendingDelete.length} 个任务。`;
  elements.deleteDialog.showModal();
}
function queryString() {
  const params = new URLSearchParams({ limit: elements.limit.value });
  if (elements.status.value) params.set("status", elements.status.value);
  if (elements.query.value.trim()) params.set("q", elements.query.value.trim());
  if (elements.hotspot.value.trim()) params.set("hotspot_id", elements.hotspot.value.trim());
  if (elements.period.value.trim()) params.set("period", elements.period.value.trim());
  if (state.cursor !== null) params.set("cursor", String(state.cursor));
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
  const resultUrlValue = resultUrl(task);
  if (resultUrlValue) {
    const resultLink = document.createElement("a");
    resultLink.href = resultUrlValue;
    resultLink.target = "_blank";
    resultLink.rel = "noopener noreferrer";
    resultLink.textContent = resultUrlValue;
    result.append(resultLink);
  } else {
    result.textContent = "—";
  }
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
        const resultLink = document.createElement("a");
        resultLink.className = "result-link";
        resultLink.href = value;
        resultLink.target = "_blank";
        resultLink.rel = "noopener noreferrer";
        resultLink.textContent = value;
        cell.append(resultLink);
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
  elements.next.disabled = !state.hasMore;
  elements.previous.disabled = state.cursorHistory.length === 0;
  elements.page.textContent = `第 ${state.page} 页`;
  updateSelectionState();
}
async function loadTasks() {
  if (!token() || state.loading) return;
  state.loading = true;
  elements.refresh.disabled = true;
  setMessage();
  try {
    const response = await fetch(`/api/v1/tasks?${queryString()}`, {
      headers: { Authorization: `Bearer ${token()}` },
      cache: "no-store",
    });
    const payload = await response.json();
    if (response.status === 401) {
      sessionStorage.removeItem(TOKEN_KEY);
      showLogin("API Key 无效，请重新输入。");
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
  }
}

async function deletePendingTasks() {
  const taskIds = [...state.pendingDelete];
  if (!taskIds.length) return;
  elements.confirmDelete.disabled = true;
  elements.cancelDelete.disabled = true;
  try {
    const isBatch = taskIds.length > 1;
    const headers = { Authorization: `Bearer ${token()}` };
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
      sessionStorage.removeItem(TOKEN_KEY);
      elements.deleteDialog.close();
      showLogin("API Key 无效，请重新输入。");
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
  const value = elements.apiKey.value.trim();
  if (!value) return;
  sessionStorage.setItem(TOKEN_KEY, value);
  elements.apiKey.value = "";
  resetPaging();
  await loadTasks();
});
elements.recordsTab.addEventListener("click", async () => {
  showView("records");
  if (token()) await loadTasks();
});
elements.apiDocsTab.addEventListener("click", () => showView("docs"));
elements.loginDocs.addEventListener("click", () => showView("docs"));
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
elements.logout.addEventListener("click", () => {
  sessionStorage.removeItem(TOKEN_KEY);
  elements.rows.replaceChildren();
  state.selected.clear();
  updateSelectionState();
  showLogin();
});
elements.filterForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetPaging();
  await loadTasks();
});
elements.reset.addEventListener("click", async () => {
  elements.filterForm.reset();
  resetPaging();
  await loadTasks();
});
elements.refresh.addEventListener("click", loadTasks);
elements.next.addEventListener("click", async () => {
  if (!state.hasMore) return;
  const taskRows = Array.from(elements.rows.querySelectorAll("tr:not(.detail-row)"));
  const lastRow = taskRows[taskRows.length - 1];
  const rowNumber = lastRow?.dataset.rowNumber;
  if (!rowNumber) return;
  state.cursorHistory.push(state.cursor);
  state.cursor = Number(rowNumber);
  state.page += 1;
  await loadTasks();
});
elements.previous.addEventListener("click", async () => {
  if (!state.cursorHistory.length) return;
  state.cursor = state.cursorHistory.pop();
  state.page -= 1;
  await loadTasks();
});

showView("records");
if (token()) loadTasks(); else showLogin();
