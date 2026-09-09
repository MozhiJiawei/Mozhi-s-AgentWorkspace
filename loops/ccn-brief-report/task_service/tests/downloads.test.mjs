import { readFileSync } from "node:fs";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";

const source = readFileSync(new URL("../app/web/downloads.js", import.meta.url), "utf8");
const htmlUrl = "https://media.githubusercontent.com/media/MozhiJiawei/ccn-report/refs/heads/main/中文/报告.html";
const html = "<!doctype html><html><title>报告</title><body>正文</body></html>";
function harness(fetch, extras = {}) {
  const context = vm.createContext({ URL, TextDecoder, Uint8Array, AbortController, DOMException, TypeError, Blob,
    setTimeout, clearTimeout, fetch, ...extras });
  vm.runInContext(source, context);
  return vm.runInContext("ReportDownloads", context);
}
const signal = () => new AbortController().signal;

test("strict repository mapping and safe Chinese filename", () => {
  const api = harness();
  assert.equal(api.mediaUrl("https://github.com/MozhiJiawei/ccn-report/raw/refs/heads/main/报告.pptx?download=1", "pptx"),
    "https://media.githubusercontent.com/media/MozhiJiawei/ccn-report/refs/heads/main/%E6%8A%A5%E5%91%8A.pptx?download=true");
  for (const url of ["https://github.com/other/repo/raw/refs/heads/main/a.pptx", "https://evil.test/a.pptx", htmlUrl + "/", "https://media.githubusercontent.com.evil.test/a.html"]) {
    assert.throws(() => api.mediaUrl(url, "pptx"));
  }
  assert.equal(api.filename(htmlUrl, "html"), "报告.html");
  assert.equal(api.safeName("../a\\报告.html"), "__a_报告.html");
});

test("fetch omits credentials, rejects redirects and preserves bytes", async () => {
  const api = harness(async (url, options) => {
    assert.equal(options.credentials, "omit");
    assert.equal(options.redirect, "error");
    assert.match(url, /^https:\/\/media\.githubusercontent\.com\//);
    return new Response(html);
  });
  assert.equal(new TextDecoder().decode(await api.file(htmlUrl, "html", signal())), html);
});

test("404, LFS pointers and error pages never become reports", async () => {
  for (const response of [new Response("missing", { status: 404 }), new Response("version https://git-lfs.github.com/spec/v1\noid sha256:abc"), new Response("<html><title>404 Not Found</title></html>")]) {
    let calls = 0;
    const api = harness(async () => { calls++; return response; });
    await assert.rejects(api.file(htmlUrl, "html", signal()));
    assert.equal(calls, 1);
  }
  const api = harness(async () => new Response(html));
  await assert.rejects(api.file(htmlUrl.replace(".html", ".pptx"), "pptx", signal()), /PPTX/);
});

test("429 respects Retry-After and retries twice at most", async () => {
  let calls = 0;
  const delays = [];
  const api = harness(async () => { calls++; return new Response("busy", { status: 429, headers: { "Retry-After": "2" } }); }, {
    setTimeout: (fn, ms) => { delays.push(ms); return setTimeout(fn, ms === 60000 ? 60000 : 0); },
  });
  await assert.rejects(api.file(htmlUrl, "html", signal()), /429/);
  assert.equal(calls, 3);
  assert.deepEqual(delays.filter((ms) => ms !== 60000), [2000, 2000]);
});

test("missing Content-Length still enforces per-file and total byte limits", async () => {
  let cancelled = 0;
  function largeResponse() {
    return new Response(new ReadableStream({
      pull(controller) { controller.enqueue(new Uint8Array(1024 * 1024)); },
      cancel() { cancelled++; },
    }));
  }
  const api = harness(async () => largeResponse());
  await assert.rejects(api.file(htmlUrl, "html", signal()), /50 MiB/);
  await assert.rejects(api.file(htmlUrl, "html", signal(), { bytes: 200 * 1024 * 1024 }), /200 MiB/);
  assert.equal(cancelled, 2);
});

test("abort stops queue, concurrency never exceeds three", async () => {
  const controller = new AbortController();
  const api = harness();
  let active = 0, max = 0, started = 0;
  await api.pool(Array.from({ length: 200 }), async () => {
    started++; active++; max = Math.max(max, active);
    await new Promise((resolve) => setTimeout(resolve, 2));
    controller.abort(); active--;
  }, controller.signal);
  assert.equal(max, 3);
  assert.equal(started, 3);
});

test("timeouts retry at most twice and user cancellation does not retry", async () => {
  let calls = 0;
  const fetch = async (_url, options) => {
    calls++;
    return new Promise((_resolve, reject) => {
      options.signal.addEventListener("abort", () => reject(options.signal.reason), { once: true });
    });
  };
  const api = harness(fetch, { setTimeout: (fn) => setTimeout(fn, 0) });
  await assert.rejects(api.file(htmlUrl, "html", signal()));
  assert.equal(calls, 3);
  calls = 0;
  const controller = new AbortController();
  const normal = harness(fetch);
  const pending = normal.file(htmlUrl, "html", controller.signal);
  controller.abort();
  await assert.rejects(pending);
  assert.equal(calls, 1);
});

test("save revokes object URL and ZIP preserves Chinese names", () => {
  const context = vm.createContext({});
  vm.runInContext(readFileSync(new URL("../app/web/fflate-0.8.2.js", import.meta.url), "utf8"), context);
  const lib = context.fflate;
  const chunks = [];
  const zip = new lib.Zip((error, data) => { assert.ifError(error); chunks.push(data); });
  const entry = new lib.ZipPassThrough("task/报告.html");
  zip.add(entry); entry.push(lib.strToU8(html), true); zip.end();
  const bytes = Buffer.concat(chunks);
  const unpacked = lib.unzipSync(bytes);
  assert.equal(lib.strFromU8(unpacked["task/报告.html"]), html);
  let revoked = false, removed = false, clicked = false;
  const api = harness(null, {
    URL: { createObjectURL: () => "blob:test", revokeObjectURL: () => { revoked = true; } },
    document: { createElement: () => ({ click: () => { clicked = true; }, remove: () => { removed = true; } }), body: { append() {} } },
    setTimeout: (fn) => fn(),
  });
  api.save(new Blob([bytes]), "test.zip");
  assert.ok(revoked && removed && clicked);
});
