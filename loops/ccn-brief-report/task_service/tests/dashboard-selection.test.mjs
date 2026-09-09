import { readFileSync } from "node:fs";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";

const source = readFileSync(new URL("../app/web/dashboard.js", import.meta.url), "utf8");
// Exercise the actual loading and selection handlers without booting the page.
const selection = source.slice(source.indexOf("function updateSelectionState("), source.indexOf("function captureFilters("));
const loading = source.slice(source.indexOf("async function loadTasks("), source.indexOf("async function deletePendingTasks("));

test("failed reload clears both visible checkboxes and batch targets", async () => {
  const checkboxes = [{ checked: true }, { checked: true }];
  const state = { loading: false, selected: new Set(["a", "b"]), cursorHistory: [], hasMore: false };
  const elements = {
    rows: { querySelectorAll: () => checkboxes },
    selectAll: {}, selectionBar: {}, selectedCount: {}, deleteSelected: {},
    previous: {}, next: {}, reset: {}, refresh: {},
    filterForm: { querySelectorAll: () => [] },
  };
  let errorMessage = "";
  const context = vm.createContext({
    state, elements,
    document: { getElementById: () => ({}) },
    dateRange: { close() {} },
    queryString: () => "",
    fetch: async () => { throw new Error("offline"); },
    setOnline() {},
    setMessage(message) { errorMessage = message; },
  });
  vm.runInContext(selection + loading, context);
  await vm.runInContext("loadTasks()", context);
  assert.match(errorMessage, /offline/);
  assert.equal(state.selected.size, 0);
  assert.ok(checkboxes.every((checkbox) => !checkbox.checked));
  assert.equal(elements.selectAll.checked, false);
  assert.equal(elements.selectAll.indeterminate, false);
  assert.equal(elements.selectionBar.hidden, true);
  assert.equal(state.loading, false);
});
