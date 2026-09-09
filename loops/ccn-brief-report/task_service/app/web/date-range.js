"use strict";

class DateRangePicker {
  constructor(root) {
    this.root = root;
    this.trigger = root.querySelector(".date-range-trigger");
    this.popup = root.querySelector(".date-range-popup");
    this.startInput = root.querySelector("[name=updated_from]");
    this.endInput = root.querySelector("[name=updated_to]");
    this.calendar = root.querySelector(".range-calendars");
    this.summary = root.querySelector(".range-summary");
    this.confirm = root.querySelector(".range-confirm");
    this.today = new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
    this.trigger.addEventListener("click", () => this.popup.hidden ? this.open() : this.close());
    root.querySelector(".range-previous").addEventListener("click", () => this.shift(-1));
    root.querySelector(".range-next").addEventListener("click", () => this.shift(1));
    root.querySelector(".range-year").addEventListener("change", (event) => { this.month.setUTCFullYear(Number(event.target.value)); this.render(); });
    root.querySelector(".range-month").addEventListener("change", (event) => { this.month.setUTCMonth(Number(event.target.value)); this.render(); });
    root.querySelectorAll("[data-days]").forEach((button) => button.addEventListener("click", () => {
      this.end = this.today;
      const start = new Date(`${this.today}T00:00:00Z`);
      start.setUTCDate(start.getUTCDate() - Number(button.dataset.days) + 1);
      this.start = this.iso(start);
      this.month = new Date(`${this.start.slice(0, 7)}-01T00:00:00Z`);
      this.render();
    }));
    root.querySelector(".range-clear").addEventListener("click", () => { this.start = ""; this.end = ""; this.render(); });
    root.querySelector(".range-cancel").addEventListener("click", () => this.close(true));
    this.confirm.addEventListener("click", () => {
      if (this.start && !this.end) return;
      this.startInput.value = this.start;
      this.endInput.value = this.end;
      this.updateLabel();
      this.close(true);
    });
    document.addEventListener("click", (event) => { if (!event.composedPath().includes(root)) this.close(); });
    root.addEventListener("keydown", (event) => {
      if (event.key === "Escape") { event.preventDefault(); this.close(true); }
    });
    root.addEventListener("focusout", () => {
      setTimeout(() => { if (!root.contains(document.activeElement)) this.close(); }, 0);
    });
  }
  iso(day) { return day.toISOString().slice(0, 10); }
  open() {
    this.start = this.startInput.value;
    this.end = this.endInput.value;
    this.month = new Date(`${(this.start || this.today).slice(0, 7)}-01T00:00:00Z`);
    this.popup.hidden = false;
    this.trigger.setAttribute("aria-expanded", "true");
    this.render();
    this.root.querySelector(".range-previous").focus();
  }
  close(focus = false) {
    this.popup.hidden = true;
    this.trigger.setAttribute("aria-expanded", "false");
    if (focus) this.trigger.focus();
  }
  reset() {
    this.startInput.value = "";
    this.endInput.value = "";
    this.updateLabel();
    this.close();
  }
  updateLabel() {
    this.trigger.querySelector(".date-range-value").textContent = this.startInput.value
      ? `${this.startInput.value} 至 ${this.endInput.value}` : "选择日期区间";
    this.trigger.classList.toggle("has-range", Boolean(this.startInput.value));
  }
  shift(offset) {
    this.month.setUTCMonth(this.month.getUTCMonth() + offset);
    this.render();
  }
  select(value) {
    if (!this.start || this.end) { this.start = value; this.end = ""; }
    else { [this.start, this.end] = [this.start, value].sort(); }
    this.render();
    this.calendar.querySelector(`[data-date="${value}"]`)?.focus();
  }
  render() {
    const year = this.month.getUTCFullYear();
    const years = this.root.querySelector(".range-year");
    years.replaceChildren();
    for (let value = year - 10; value <= year + 10; value++) years.add(new Option(`${value} 年`, String(value)));
    years.value = String(year);
    this.root.querySelector(".range-month").value = String(this.month.getUTCMonth());
    this.calendar.replaceChildren();
    for (let offset = 0; offset < 2; offset++) {
      const month = new Date(Date.UTC(year, this.month.getUTCMonth() + offset, 1));
      const panel = document.createElement("section");
      panel.className = "range-month-panel";
      const title = document.createElement("h4");
      title.textContent = `${month.getUTCFullYear()} 年 ${month.getUTCMonth() + 1} 月`;
      const grid = document.createElement("div");
      grid.className = "range-grid";
      for (const text of ["一", "二", "三", "四", "五", "六", "日"]) {
        const weekday = document.createElement("span");
        weekday.className = "range-weekday";
        weekday.textContent = text;
        grid.append(weekday);
      }
      const padding = (month.getUTCDay() + 6) % 7;
      for (let i = 0; i < padding; i++) grid.append(document.createElement("span"));
      const count = new Date(Date.UTC(month.getUTCFullYear(), month.getUTCMonth() + 1, 0)).getUTCDate();
      for (let day = 1; day <= count; day++) {
        const value = this.iso(new Date(Date.UTC(month.getUTCFullYear(), month.getUTCMonth(), day)));
        const button = document.createElement("button");
        button.type = "button";
        button.className = "range-day";
        button.dataset.date = value;
        button.textContent = String(day);
        button.setAttribute("aria-label", `${month.getUTCFullYear()}年${month.getUTCMonth() + 1}月${day}日`);
        button.setAttribute("aria-pressed", String(Boolean(this.start && this.end && value >= this.start && value <= this.end) || value === this.start));
        if (value === this.today) { button.classList.add("is-today"); button.setAttribute("aria-current", "date"); }
        if (value === this.start || value === this.end) button.classList.add("range-endpoint");
        else if (this.start && this.end && value > this.start && value < this.end) button.classList.add("in-range");
        button.addEventListener("click", () => this.select(value));
        grid.append(button);
      }
      panel.append(title, grid);
      this.calendar.append(panel);
    }
    this.confirm.disabled = Boolean(this.start && !this.end);
    this.summary.textContent = this.end ? `${this.start} 至 ${this.end}` : this.start ? `${this.start} — 请选择结束日期` : "先选开始日期，再选结束日期";
  }
}
