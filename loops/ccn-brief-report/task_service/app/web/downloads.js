"use strict";

// No report bytes pass through the task service. Keep this host/repository allowlist narrow.
const ReportDownloads = (() => {
  const FILE_LIMIT = 50 * 1024 * 1024;
  const TOTAL_LIMIT = 200 * 1024 * 1024;
  function mediaUrl(value, type) {
    const url = new URL(value);
    if (url.protocol !== "https:" || url.username || url.password || url.port) throw new Error("不支持的报告地址");
    let path = url.pathname;
    if (url.hostname === "github.com" && path.startsWith("/MozhiJiawei/ccn-report/raw/refs/heads/main/")) {
      path = path.replace("/MozhiJiawei/ccn-report/raw/", "/media/MozhiJiawei/ccn-report/");
    } else if (url.hostname !== "media.githubusercontent.com" || !path.startsWith("/media/MozhiJiawei/ccn-report/refs/heads/main/")) {
      throw new Error("不支持的报告地址");
    }
    if (!path.toLowerCase().endsWith(`.${type}`)) throw new Error("报告类型或文件后缀不匹配");
    return `https://media.githubusercontent.com${path}?download=true`;
  }
  function safeName(value) {
    return value.replace(/[\\/<>:"|?*\u0000-\u001f]/g, "_").replace(/\.\./g, "_").replace(/[. ]+$/g, "") || "report";
  }
  function filename(value, type) {
    try { return safeName(decodeURIComponent(new URL(value).pathname.split("/").pop())); }
    catch (_) { return `report.${type}`; }
  }
  function pause(ms, signal) {
    return new Promise((resolve, reject) => {
      signal.throwIfAborted();
      const abort = () => { clearTimeout(timer); reject(signal.reason); };
      const timer = setTimeout(() => { signal.removeEventListener("abort", abort); resolve(); }, ms);
      signal.addEventListener("abort", abort, { once: true });
    });
  }
  function retryDelay(response, attempt) {
    const header = response?.headers.get("Retry-After");
    if (header) {
      const seconds = Number(header);
      return Math.max(0, Number.isFinite(seconds) ? seconds * 1000 : Date.parse(header) - Date.now()) || 1000;
    }
    return 1000 * (2 ** attempt);
  }
  async function request(url, options, consume, signal) {
    for (let attempt = 0; ; attempt++) {
      signal.throwIfAborted();
      const timeout = new AbortController();
      const abort = () => timeout.abort(signal.reason);
      signal.addEventListener("abort", abort, { once: true });
      const timer = setTimeout(() => timeout.abort(new DOMException("请求超时", "TimeoutError")), 60000);
      let response;
      let delay;
      try {
        response = await fetch(url, { ...options, signal: timeout.signal, redirect: "error" });
        if (!response.ok) {
          const error = new Error(`HTTP ${response.status}`);
          error.retryable = response.status === 429 || response.status >= 500;
          delay = retryDelay(response, attempt);
          throw error;
        }
        return await consume(response);
      } catch (error) {
        signal.throwIfAborted();
        const transient = error.retryable || error instanceof TypeError || timeout.signal.aborted;
        if (!transient || attempt >= 2) throw error;
        delay ??= retryDelay(null, attempt);
      } finally {
        clearTimeout(timer);
        signal.removeEventListener("abort", abort);
        await response?.body?.cancel().catch(() => {});
      }
      await pause(delay, signal);
    }
  }
  async function file(url, type, signal, budget = { bytes: 0 }) {
    return request(mediaUrl(url, type), { mode: "cors", credentials: "omit" }, async (response) => {
      if (Number(response.headers.get("Content-Length")) > FILE_LIMIT) {
        const error = new Error("单文件超过 50 MiB，请缩小选择");
        error.limit = true;
        throw error;
      }
      const reader = response.body.getReader();
      const chunks = [];
      let size = 0;
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          size += value.byteLength;
          budget.bytes += value.byteLength;
          if (size > FILE_LIMIT || budget.bytes > TOTAL_LIMIT) {
            const error = new Error("文件超过 50 MiB 或累计超过 200 MiB，请缩小选择");
            error.limit = true;
            throw error;
          }
          chunks.push(value);
        }
      } finally {
        await reader.cancel().catch(() => {});
        reader.releaseLock();
      }
      const bytes = new Uint8Array(size);
      let offset = 0;
      for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
      const head = new TextDecoder().decode(bytes.subarray(0, 8192)).trimStart();
      if (!size || head.startsWith("version https://git-lfs.github.com/spec/v1")) throw new Error("未取得报告实体文件");
      if (type === "pptx" && !(bytes[0] === 80 && bytes[1] === 75 && bytes[2] === 3 && bytes[3] === 4)) throw new Error("PPTX 内容无效");
      if (type === "html" && (!/<(?:!doctype\s+html|html)[\s>]/i.test(head) || /<title>\s*(?:404|403|500|502|503|error|access denied|rate limit)/i.test(head))) throw new Error("HTML 内容无效或为错误页面");
      return bytes;
    }, signal);
  }
  async function detail(taskId, signal) {
    return request(`/api/v1/tasks/${encodeURIComponent(taskId)}`, { cache: "no-store", credentials: "same-origin" }, async (response) => {
      const payload = await response.json();
      if (payload.status !== "success") throw new Error("任务详情不可用");
      return payload.data;
    }, signal);
  }
  async function pool(items, worker, signal) {
    let next = 0;
    await Promise.all(Array.from({ length: Math.min(3, items.length) }, async () => {
      while (next < items.length && !signal.aborted) await worker(items[next++]);
    }));
  }
  function save(blob, name) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = name;
    document.body.append(anchor);
    try { anchor.click(); } finally { anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
  }
  function zipName() {
    const d = new Date();
    const n = (v) => String(v).padStart(2, "0");
    return `ccn-reports-${d.getFullYear()}${n(d.getMonth() + 1)}${n(d.getDate())}-${n(d.getHours())}${n(d.getMinutes())}${n(d.getSeconds())}.zip`;
  }
  return { file, detail, pool, save, filename, safeName, zipName, mediaUrl };
})();
