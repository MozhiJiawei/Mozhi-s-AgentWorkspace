import { readFileSync } from "node:fs";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";

const source = readFileSync(new URL("../app/web/dashboard.js", import.meta.url), "utf8");
// Exercise the actual loading and selection handlers without booting the page.
const selection = source.slice(source.indexOf("function updateSelectionState("), source.indexOf("function captureFilters("));
const paging = source.slice(source.indexOf("function pageCount("), source.indexOf("function updateSelectionState("));
const loading = source.slice(source.indexOf("async function loadTasks("), source.indexOf("async function deletePendingTasks("));
const locks = source.slice(source.indexOf("function downloadLocks("), source.indexOf("async function batchDownload("));

test("failed reload clears both visible checkboxes and batch targets", async () => {
  const checkboxes = [{ checked: true }, { checked: true }];
  const state = { loading: false, selected: new Set(["a", "b"]), tasks: Array(150).fill({}), page: 2, pageSize: 50, requestId: 0, authRequired: false };
  const elements = {
    rows: { querySelectorAll: () => checkboxes },
    selectAll: {}, selectionBar: {}, selectedCount: {}, deleteSelected: {},
    previous: {}, next: {}, page: {}, reset: {}, refresh: {},
    filterForm: { querySelectorAll: () => [] },
  };
  let errorMessage = "";
  const context = vm.createContext({
    state, elements,
    document: { getElementById: () => ({}), querySelectorAll: () => [] },
    dateRange: { close() {} },
    queryString: () => "",
    fetch: async () => { throw new Error("offline"); },
    setOnline() {},
    setMessage(message) { errorMessage = message; },
  });
  vm.runInContext(paging + selection + loading + locks, context);
  await vm.runInContext("loadTasks()", context);
  assert.match(errorMessage, /offline/);
  assert.equal(state.selected.size, 0);
  assert.ok(checkboxes.every((checkbox) => !checkbox.checked));
  assert.equal(elements.selectAll.checked, false);
  assert.equal(elements.selectAll.indeterminate, false);
  assert.equal(elements.selectionBar.hidden, true);
  assert.equal(state.loading, false);
  assert.equal(state.page, 2);
  assert.equal(elements.previous.disabled, false);
  assert.equal(elements.next.disabled, false);
});
