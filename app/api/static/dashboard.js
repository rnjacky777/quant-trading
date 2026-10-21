function persistForm(form) {
  const key = form.dataset.persistKey;
  if (!key) return;

  try {
    const saved = JSON.parse(localStorage.getItem(key) || "{}");
    for (const [name, value] of Object.entries(saved)) {
      if (name === "base_run_key") continue;
      const field = form.elements.namedItem(name);
      if (field && typeof value === "string") field.value = value;
    }
  } catch (_error) {
    localStorage.removeItem(key);
  }

  const save = () => {
    const values = {};
    for (const [name, value] of new FormData(form).entries()) {
      if (name === "base_run_key") continue;
      values[name] = value;
    }
    localStorage.setItem(key, JSON.stringify(values));
  };

  form.addEventListener("input", save);
  form.addEventListener("change", save);
  form.addEventListener("submit", save);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-persist-key]").forEach(persistForm);

  const historyFilters = document.getElementById("history-filters");
  const historyTable = document.getElementById("backtest-history-table");
  if (historyFilters && historyTable) {
    const rows = Array.from(historyTable.tBodies[0].rows);
    const visibleCount = document.getElementById("history-visible-count");
    const emptyMessage = document.getElementById("history-filter-empty");
    const applyHistoryFilters = () => {
      const values = Object.fromEntries(new FormData(historyFilters).entries());
      let count = 0;
      for (const row of rows) {
        const visible =
          (!values.recorded_from || row.dataset.recordedDate >= values.recorded_from) &&
          (!values.recorded_until || row.dataset.recordedDate <= values.recorded_until) &&
          (!values.strategy || row.dataset.strategy === values.strategy) &&
          (!values.timeframe || row.dataset.timeframe === values.timeframe) &&
          (!values.version || row.dataset.version === values.version);
        row.hidden = !visible;
        if (visible) count += 1;
      }
      visibleCount.textContent = String(count);
      emptyMessage.hidden = count !== 0;
      historyTable.hidden = count === 0;
    };
    historyFilters.addEventListener("input", applyHistoryFilters);
    historyFilters.addEventListener("change", applyHistoryFilters);
    historyFilters.addEventListener("reset", () => {
      window.setTimeout(() => {
        localStorage.removeItem(historyFilters.dataset.persistKey);
        applyHistoryFilters();
      }, 0);
    });
    applyHistoryFilters();
  }

  const adjustmentFilters = document.getElementById("adjustment-filters");
  const adjustmentTable = document.getElementById("strategy-adjustment-table");
  if (adjustmentFilters && adjustmentTable) {
    const rows = Array.from(adjustmentTable.tBodies[0].rows);
    const visibleCount = document.getElementById("adjustment-visible-count");
    const emptyMessage = document.getElementById("adjustment-filter-empty");
    const applyAdjustmentFilters = () => {
      const values = Object.fromEntries(new FormData(adjustmentFilters).entries());
      let count = 0;
      for (const row of rows) {
        const visible =
          (!values.recorded_from || row.dataset.recordedDate >= values.recorded_from) &&
          (!values.recorded_until || row.dataset.recordedDate <= values.recorded_until) &&
          (!values.strategy || row.dataset.strategy === values.strategy) &&
          (!values.timeframe || row.dataset.timeframe === values.timeframe) &&
          (!values.version || row.dataset.version === values.version);
        row.hidden = !visible;
        if (visible) count += 1;
      }
      visibleCount.textContent = String(count);
      emptyMessage.hidden = count !== 0;
      adjustmentTable.hidden = count === 0;
    };
    adjustmentFilters.addEventListener("input", applyAdjustmentFilters);
    adjustmentFilters.addEventListener("change", applyAdjustmentFilters);
    adjustmentFilters.addEventListener("reset", () => {
      window.setTimeout(() => {
        localStorage.removeItem(adjustmentFilters.dataset.persistKey);
        applyAdjustmentFilters();
      }, 0);
    });
    applyAdjustmentFilters();
  }

  const backtest = document.querySelector(
    'form[data-persist-key="quant-backtest-form"]'
  );
  const download = document.querySelector(
    'form[data-persist-key="quant-download-form"]'
  );
  if (!backtest || !download) return;

  const syncDownloadFields = () => {
    for (const name of ["symbol", "timeframe", "since", "until"]) {
      const source = backtest.elements.namedItem(name);
      const target = download.elements.namedItem(name);
      if (source && target) target.value = source.value;
    }
    download.dispatchEvent(new Event("change"));
  };

  syncDownloadFields();
  backtest.addEventListener("input", syncDownloadFields);
  backtest.addEventListener("change", syncDownloadFields);

  const versionSelect = document.getElementById("backtest-strategy-version");
  if (versionSelect) {
    const baseRunKey = backtest.elements.namedItem("base_run_key");
    const baseNote = document.getElementById("strategy-base-note");
    const versionOptions = Array.from(versionSelect.options)
      .slice(1)
      .map((option) => option.cloneNode(true));
    const showBaseVersion = () => {
      const base = versionOptions.find(
        (option) => option.dataset.runKey === baseRunKey.value
      );
      baseNote.hidden = !base;
      baseNote.textContent = base
        ? `新候選版本將基於 ${base.textContent.split(" · ")[0]}；你可以修改設定後建立下一版。`
        : "";
    };
    const refreshVersions = (selectedValue = "") => {
      const symbol = backtest.elements.namedItem("symbol").value;
      const timeframe = backtest.elements.namedItem("timeframe").value;
      const strategy = backtest.elements.namedItem("strategy").value;
      versionSelect.length = 1;
      for (const option of versionOptions) {
        if (
          option.dataset.symbol === symbol &&
          option.dataset.timeframe === timeframe &&
          option.dataset.strategy === strategy
        ) {
          versionSelect.append(option.cloneNode(true));
        }
      }
      const baseOption = Array.from(versionSelect.options).find(
        (option) => option.dataset.runKey === baseRunKey.value
      );
      versionSelect.value = selectedValue || (baseOption ? baseOption.value : "");
    };

    versionSelect.addEventListener("change", () => {
      if (!versionSelect.value) {
        baseRunKey.value = "";
        showBaseVersion();
        return;
      }
      const selectedValue = versionSelect.value;
      baseRunKey.value = versionSelect.selectedOptions[0].dataset.runKey;
      showBaseVersion();
      const savedVersion = new URL(selectedValue, window.location.origin);
      for (const [name, value] of savedVersion.searchParams.entries()) {
        const field = backtest.elements.namedItem(name);
        if (field) field.value = value;
      }
      backtest.dispatchEvent(new Event("change", { bubbles: true }));
      backtest.dispatchEvent(new Event("input", { bubbles: true }));
      refreshVersions(selectedValue);
    });

    for (const name of ["symbol", "timeframe", "strategy"]) {
      backtest.elements.namedItem(name).addEventListener("change", () => {
        baseRunKey.value = "";
        showBaseVersion();
        refreshVersions();
      });
    }
    backtest.addEventListener("input", showBaseVersion);
    backtest.addEventListener("change", showBaseVersion);
    refreshVersions();

    const pageQuery = new URLSearchParams(window.location.search);
    if (["advisor", "history", "development_branch"].includes(pageQuery.get("load_strategy"))) {
      for (const [name, value] of pageQuery.entries()) {
        const field = backtest.elements.namedItem(name);
        if (field) field.value = value;
      }
      refreshVersions();
      showBaseVersion();
      backtest.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }
});
