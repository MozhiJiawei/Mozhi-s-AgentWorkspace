import { readFileSync } from "node:fs";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";

const source = readFileSync(new URL("../app/web/dashboard.js", import.meta.url), "utf8");
const html = readFileSync(new URL("../app/web/dashboard.html", import.meta.url), "utf8");

// The small DOM double runs the real page, including its event handlers and rows.
class Element {
  constructor(tagName = "div") {
    this.tagName = tagName;
    this.children = [];
    this.dataset = {};
    this.listeners = new Map();
    this.attributes = new Map();
    this.className = "";
    this.value = "";
    this.textContent = "";
    this.hidden = false;
    this.disabled = false;
    this.checked = false;
    this.open = false;
    this.classList = {
      toggle: (name, force) => {
        const names = new Set(this.className.split(/\s+/).filter(Boolean));
        if (force ?? !names.has(name)) names.add(name); else names.delete(name);
        this.className = [...names].join(" ");
      },
      add: (name) => this.classList.toggle(name, true),
      remove: (name) => this.classList.toggle(name, false),
    };
  }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = [...children]; }
  setAttribute(name, value) { this.attributes.set(name, value); }
  getAttribute(name) { return this.attributes.get(name); }
  removeAttribute(name) { this.attributes.delete(name); }
  addEventListener(type, handler) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(handler);
  }
  async emit(type) {
    await Promise.all((this.listeners.get(type) || []).map((handler) => handler({
      target: this, currentTarget: this, preventDefault() {},
    })));
  }
  querySelectorAll(selector) {
    const selectors = selector.split(",").map((part) => part.trim());
    return this.children.flatMap((child) => {
      const matches = selectors.some((part) => part.startsWith(".")
        ? child.className.split(/\s+/).includes(part.slice(1)) : child.tagName === part);
      return [...(matches ? [child] : []), ...child.querySelectorAll(selector)];
    });
  }
  showModal() { this.open = true; }
  close() {
    if (!this.open) return;
    this.open = false;
    return this.emit("close");
  }
}

const response = (data, status = 200) => ({
  status, ok: status >= 200 && status < 300,
  json: async () => ({ status: status === 200 ? "success" : "error", data, error: { message: "unavailable" } }),
});
const tasks = (count, status) => Array.from({ length: count }, (_, index) => ({
  task_id: `task-${index + 1}`, row_number: index + 1,
  status: status || ["pending", "completed", "failed"][index % 3],
  content: "任务正文", url: "https://example.com/source", hotspot_id: "HS-001", period: "2026-W43",
  created_at: "2026-10-25T00:00:00Z", updated_at: "2026-10-26T00:00:00Z", latest_result: null,
}));
function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}

async function dashboard(initialTasks = tasks(501), initialResponse = response(initialTasks)) {
  const nodes = new Map();
  const node = (selector) => {
    if (!nodes.has(selector)) nodes.set(selector, new Element());
    return nodes.get(selector);
  };
  node("#limit-filter").value = "50";
  const fields = ["status", "query", "hotspot", "period", "limit"].map((name) => node(`#${name}-filter`));
  node("#filter-form").querySelectorAll = () => fields;
  node("#filter-form").reset = () => fields.forEach((field, index) => { field.value = index === 4 ? "50" : ""; });
  const queue = [initialResponse];
  const requests = [];
  const context = vm.createContext({
    document: {
      querySelector: node,
      getElementById: (id) => node(`#${id}`),
      createElement: (tag) => new Element(tag),
      querySelectorAll: (selector) => selector === "[data-copy-target]" ? [] : node("#task-rows").querySelectorAll(selector),
    },
    DateRangePicker: class {
      startInput = { value: "" };
      endInput = { value: "" };
      close() {}
      reset() { this.startInput.value = ""; this.endInput.value = ""; }
    },
    URLSearchParams, Intl, AbortController,
    fetch: async (url, options) => {
      requests.push({ url, options });
      assert.ok(queue.length, `Unexpected fetch: ${url}`);
      const next = queue.shift();
      return typeof next === "function" ? next() : next;
    },
  });
  vm.runInContext(source, context);
  await new Promise(setImmediate);
  const state = vm.runInContext("state", context);
  return {
    node, state, queue, requests,
    run: (code) => vm.runInContext(code, context),
    click: (id) => node(`#${id}`).emit("click"),
    checkboxes: () => node("#task-rows").querySelectorAll(".row-select"),
    ids: () => node("#task-rows").querySelectorAll(".row-select").map((box) => box.dataset.taskId),
    async goTo(page) { while (state.page < page) await node("#next-button").emit("click"); },
  };
}

function assertEmpty(page) {
  assert.equal(page.state.tasks.length, 0);
  assert.equal(page.state.page, 1);
  assert.equal(page.ids().length, 0);
  assert.equal(page.node("#metric-total").textContent, "0");
  assert.equal(page.node("#metric-pending").textContent, "0");
  assert.equal(page.node("#metric-completed").textContent, "0");
  assert.equal(page.node("#metric-failed").textContent, "0");
  assert.equal(page.node("#page-label").textContent, "第 1 / 1 页，共 0 个任务");
  assert.equal(page.node("#previous-button").disabled, true);
  assert.equal(page.node("#next-button").disabled, true);
  assert.equal(page.state.selected.size, 0);
}

test("501 results have complete metrics and eleven local pages without pagination requests", async () => {
  const page = await dashboard();
  assert.equal(page.state.tasks.length, 501);
  assert.equal(page.state.pageSize, 50);
  assert.equal(page.ids().length, 50);
  assert.equal(page.ids()[0], "task-1");
  assert.equal(page.node("#metric-total").textContent, "501");
  for (const status of ["pending", "completed", "failed"]) assert.equal(page.node(`#metric-${status}`).textContent, "167");
  assert.equal(page.node("#page-label").textContent, "第 1 / 11 页，共 501 个任务");
  assert.equal(page.requests[0].url, "/api/v1/tasks?sort=updated_desc");
  page.node("#select-all").checked = true;
  await page.node("#select-all").emit("change");
  assert.equal(page.state.selected.size, 50);
  await page.click("next-button");
  assert.equal(page.ids()[0], "task-51");
  assert.equal(page.state.selected.size, 0);
  assert.equal(page.node("#select-all").checked, false);
  await page.click("previous-button");
  assert.equal(page.ids()[0], "task-1");
  await page.goTo(11);
  assert.deepEqual(page.ids(), ["task-501"]);
  assert.equal(page.node("#next-button").disabled, true);
  await page.click("next-button");
  assert.equal(page.state.page, 11);
  assert.equal(page.requests.length, 1);
  assert.equal(page.node("#metric-total").textContent, "501");
});

test("page sizes slice locally, return to the first page and clear only-page selections", async () => {
  const page = await dashboard();
  for (const size of [25, 100, 200, 50]) {
    await page.click("next-button");
    const checkbox = page.checkboxes()[0];
    checkbox.checked = true;
    await checkbox.emit("change");
    page.node("#limit-filter").value = String(size);
    await page.node("#limit-filter").emit("change");
    assert.equal(page.state.page, 1);
    assert.equal(page.ids().length, size);
    assert.equal(page.ids()[0], "task-1");
    assert.equal(page.state.selected.size, 0);
    assert.equal(page.node("#selection-bar").hidden, true);
  }
  assert.equal(page.requests.length, 1);
});

test("apply, clear and refresh each fetch all matches and restart on page one", async () => {
  const page = await dashboard();
  await page.goTo(3);
  page.node("#status-filter").value = "completed";
  page.node("#query-filter").value = "  task  ";
  page.node("#hotspot-filter").value = "HS-001";
  page.node("#period-filter").value = "2026-W43";
  page.run('dateRange.startInput.value = "2026-10-01"; dateRange.endInput.value = "2026-10-26"');
  page.queue.push(response(tasks(104, "completed")));
  await page.node("#filter-form").emit("submit");
  const params = new URL(page.requests.at(-1).url, "http://localhost").searchParams;
  assert.deepEqual(Object.fromEntries(params), {
    sort: "updated_desc", status: "completed", q: "task", hotspot_id: "HS-001", period: "2026-W43",
    updated_from: "2026-10-01", updated_to: "2026-10-26",
  });
  assert.equal(page.state.page, 1);
  assert.equal(page.node("#metric-total").textContent, "104");
  assert.equal(page.node("#metric-completed").textContent, "104");
  await page.goTo(3);
  page.queue.push(response(tasks(501)));
  await page.click("reset-button");
  assert.equal(page.requests.at(-1).url, "/api/v1/tasks?sort=updated_desc");
  assert.equal(page.state.page, 1);
  await page.goTo(4);
  page.queue.push(response(tasks(501)));
  await page.click("refresh-button");
  assert.equal(page.state.page, 1);
  assert.equal(page.requests.length, 4);
});

test("deletion reloads all matches, preserves the page, clamps a shorter last page and handles zero results", async () => {
  const page = await dashboard();
  await page.goTo(4);
  page.run('openDeleteDialog(["task-151"])');
  page.queue.push(response({ deleted: true }), response(tasks(501)));
  await page.click("confirm-delete-button");
  assert.equal(page.requests.at(-2).options.method, "DELETE");
  assert.equal(page.requests.at(-1).url, "/api/v1/tasks?sort=updated_desc");
  assert.equal(page.state.page, 4);
  await page.goTo(11);
  page.checkboxes()[0].checked = true;
  await page.checkboxes()[0].emit("change");
  page.run('openDeleteDialog(["task-501"])');
  page.queue.push(response({ deleted: true }), response(tasks(500)));
  await page.click("confirm-delete-button");
  assert.equal(page.state.page, 10);
  assert.equal(page.node("#page-label").textContent, "第 10 / 10 页，共 500 个任务");
  assert.equal(page.node("#next-button").disabled, true);
  assert.equal(page.state.selected.size, 0);
  page.run('openDeleteDialog(["task-500"])');
  page.queue.push(response({ deleted: true }), response([]));
  await page.click("confirm-delete-button");
  assertEmpty(page);
  assert.equal(page.node("#empty-state").hidden, false);
});

test("pending refresh locks all deletion entry points and restores deletion when finished", async () => {
  const page = await dashboard();
  const pending = deferred();
  const oldDeleteButtons = page.node("#task-rows").querySelectorAll(".delete-row-button");
  page.queue.push(() => pending.promise);
  const loading = page.click("refresh-button");
  assert.ok(oldDeleteButtons.every((button) => button.disabled));
  assert.equal(page.node("#delete-selected-button").disabled, true);
  // Emit even on disabled controls to exercise the handler-level defenses.
  await oldDeleteButtons[0].emit("click");
  page.checkboxes()[0].checked = true;
  await page.checkboxes()[0].emit("change");
  await page.click("delete-selected-button");
  assert.equal(page.node("#delete-dialog").open, false);
  page.run('state.pendingDelete = ["task-1"]');
  await page.run("deletePendingTasks()");
  assert.equal(page.requests.length, 2);
  // Finishing a download must not accidentally unlock deletion during a reload.
  page.state.download = { ids: new Set(["task-1"]), controller: new AbortController() };
  page.run("downloadLocks()");
  page.state.download = null;
  page.run("downloadLocks()");
  assert.ok(oldDeleteButtons.every((button) => button.disabled));
  assert.equal(page.node("#delete-selected-button").disabled, true);
  pending.resolve(response(tasks(501)));
  await loading;
  const deleteButtons = page.node("#task-rows").querySelectorAll(".delete-row-button");
  assert.ok(deleteButtons.every((button) => !button.disabled));
  assert.equal(page.node("#delete-selected-button").disabled, false);
  await deleteButtons[0].emit("click");
  assert.equal(page.node("#delete-dialog").open, true);
  page.queue.push(response({ deleted: true }), response(tasks(500)));
  await page.click("confirm-delete-button");
  assert.equal(page.requests.at(-2).options.method, "DELETE");
  assert.equal(page.state.tasks.length, 500);
});

test("pending deletion prevents a refresh after Escape closes its native dialog", async () => {
  const page = await dashboard();
  const pending = deferred();
  page.run('openDeleteDialog(["task-501"])');
  page.queue.push(() => pending.promise);
  const deleting = page.click("confirm-delete-button");
  assert.equal(page.state.loading, true);
  assert.equal(page.node("#refresh-button").disabled, true);
  // Escape closes a native dialog even when its Cancel button is disabled.
  await page.node("#delete-dialog").close();
  await page.click("refresh-button");
  assert.equal(page.requests.length, 2);
  assert.equal(page.requests.at(-1).options.method, "DELETE");
  page.queue.push(response(tasks(500)));
  pending.resolve(response({ deleted: true }));
  await deleting;
  assert.equal(page.requests.length, 3);
  assert.equal(page.requests.at(-1).url, "/api/v1/tasks?sort=updated_desc");
  assert.equal(page.state.tasks.length, 500);
  assert.equal(page.state.tasks.some((task) => task.task_id === "task-501"), false);
  assert.equal(page.state.loading, false);
  assert.equal(page.node("#refresh-button").disabled, false);
});

test("a stale deletion cannot unlock a new login's pending list request", async () => {
  const page = await dashboard();
  const deleted = deferred();
  page.run('openDeleteDialog(["task-501"])');
  page.queue.push(() => deleted.promise);
  const deleting = page.click("confirm-delete-button");
  page.queue.push(response({}));
  await page.click("logout-button");
  page.node("#dashboard-password").value = "example-password";
  const loading = deferred();
  page.queue.push(response({}), () => loading.promise);
  const login = page.node("#login-form").emit("submit");
  await new Promise(setImmediate);
  assert.equal(page.state.loading, true);
  deleted.resolve(response({ deleted: true }));
  await deleting;
  assert.equal(page.state.loading, true);
  assert.equal(page.node("#refresh-button").disabled, true);
  assertEmpty(page);
  loading.resolve(response(tasks(500)));
  await login;
  assert.equal(page.state.tasks.length, 500);
  assert.equal(page.state.loading, false);
});

test("failed reloads retain the last successful rows, metrics and page while clearing selection", async () => {
  const page = await dashboard();
  await page.goTo(3);
  const rows = [...page.node("#task-rows").children];
  const updated = page.node("#updated-at").textContent;
  for (const failure of [() => { throw new Error("offline"); }, response(null, 500), response({ unexpected: true })]) {
    page.checkboxes()[0].checked = true;
    await page.checkboxes()[0].emit("change");
    page.queue.push(failure);
    await page.click("refresh-button");
    assert.deepEqual(page.node("#task-rows").children, rows);
    assert.equal(page.node("#metric-total").textContent, "501");
    assert.equal(page.node("#updated-at").textContent, updated);
    assert.equal(page.state.page, 3);
    assert.equal(page.node("#page-label").textContent, "第 3 / 11 页，共 501 个任务");
    assert.equal(page.state.selected.size, 0);
    assert.ok(page.checkboxes().every((box) => !box.checked));
    assert.match(page.node("#message").textContent, /数据加载失败/);
    assert.equal(page.node("#previous-button").disabled, false);
    assert.equal(page.node("#next-button").disabled, false);
  }
});

test("401 clears cached results and successful login loads a fresh first page", async () => {
  const page = await dashboard();
  await page.goTo(3);
  page.queue.push(response(null, 401));
  await page.click("refresh-button");
  assertEmpty(page);
  assert.equal(page.node("#login-layer").hidden, false);
  await page.click("refresh-button");
  assert.equal(page.requests.length, 2);
  page.node("#dashboard-password").value = "example-password";
  page.queue.push(response({}), response(tasks(9)));
  await page.node("#login-form").emit("submit");
  assert.equal(page.requests.at(-2).url, "/dashboard-auth/login");
  assert.equal(page.state.page, 1);
  assert.equal(page.state.tasks.length, 9);
  assert.equal(page.node("#login-layer").hidden, true);
});

test("an initial connection failure still allows login and public documentation", async () => {
  const page = await dashboard([], () => { throw new Error("offline"); });
  assert.equal(page.node("#login-layer").hidden, false);
  await page.click("login-docs-button");
  assert.equal(page.node("#api-docs-view").hidden, false);
  assert.equal(page.node("#login-layer").hidden, true);
  page.queue.push(response(null, 401));
  await page.click("records-tab");
  assert.equal(page.node("#login-layer").hidden, false);
  assert.equal(page.requests.length, 2);
});

test("deletion 401 also clears task caches and metrics", async () => {
  const page = await dashboard();
  await page.goTo(4);
  page.run('openDeleteDialog(["task-151"])');
  page.queue.push(response(null, 401));
  await page.click("confirm-delete-button");
  assertEmpty(page);
  assert.equal(page.node("#delete-dialog").open, false);
});

for (const stage of ["fetch", "json"]) {
  test(`logout clears immediately and ignores a pending list ${stage} response`, async () => {
    const page = await dashboard();
    await page.goTo(2);
    const pending = deferred();
    const logout = deferred();
    page.queue.push(stage === "fetch" ? () => pending.promise : { ok: true, status: 200, json: () => pending.promise });
    const loading = page.click("refresh-button");
    await Promise.resolve();
    page.queue.push(() => logout.promise);
    const loggingOut = page.click("logout-button");
    assertEmpty(page);
    assert.equal(page.node("#updated-at").textContent, "尚未加载");
    pending.resolve(stage === "fetch" ? response(tasks(501)) : { status: "success", data: tasks(501) });
    await loading;
    assertEmpty(page);
    assert.equal(page.node("#login-layer").hidden, false);
    logout.resolve(response({}));
    await loggingOut;
    await page.click("refresh-button");
    assertEmpty(page);
    assert.equal(page.requests.length, 3);
  });
}

test("page selection retains the 200-task limit and download/delete locking", async () => {
  const page = await dashboard();
  page.node("#limit-filter").value = "200";
  await page.node("#limit-filter").emit("change");
  page.node("#select-all").checked = true;
  await page.node("#select-all").emit("change");
  assert.equal(page.state.selected.size, 200);
  page.state.download = { ids: new Set(["task-1"]), controller: new AbortController() };
  page.run("downloadLocks()");
  assert.equal(page.node("#delete-selected-button").disabled, true);
  assert.equal(page.node("#download-selected-button").disabled, true);
  page.run('openDeleteDialog(["task-1"])');
  assert.equal(page.node("#delete-dialog").open, false);
  page.state.download = null;
  await page.click("next-button");
  assert.equal(page.state.selected.size, 0);
  for (let index = 0; index < 200; index++) page.state.selected.add(`reserved-${index}`);
  page.checkboxes()[0].checked = true;
  await page.checkboxes()[0].emit("change");
  assert.equal(page.checkboxes()[0].checked, false);
  assert.equal(page.state.selected.size, 200);
  assert.match(page.node("#message").textContent, /最多选择 200/);
});

test("dashboard documents the full response, server dates and sorting, with local page size default 50", () => {
  assert.match(html, /匹配任务总数/);
  assert.match(html, /aria-label="全部匹配任务状态统计"/);
  assert.match(html, /<option value="50" selected>50<\/option>/);
  assert.match(html, /一次返回全部匹配任务/);
  assert.match(html, /updated_from=2026-09-01&amp;updated_to=2026-09-09&amp;sort=updated_desc/);
  assert.doesNotMatch(html, /<code>(?:limit|cursor|page_token)<\/code>|&amp;limit=/);
  assert.match(html, /dashboard\.js\?v=9/);
});
