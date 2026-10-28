function persistForm(form) {
  const key = form.dataset.persistKey;
  if (!key) return;

  try {
    const saved = JSON.parse(localStorage.getItem(key) || "{}");
    for (const [name, value] of Object.entries(saved)) {
      if (["base_run_key", "research_plan_id", "stage"].includes(name)) continue;
      const field = form.elements.namedItem(name);
      if (field && typeof value === "string") field.value = value;
    }
  } catch (_error) {
    localStorage.removeItem(key);
  }

  const save = () => {
    const values = {};
    for (const [name, value] of new FormData(form).entries()) {
      if (["base_run_key", "research_plan_id", "stage"].includes(name)) continue;
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

  const periodSelection = document.getElementById("period-comparison-selection");
  if (periodSelection) {
    const boxes = Array.from(periodSelection.querySelectorAll('input[name="run_keys"]'));
    const update = (event) => {
      let checked = boxes.filter(box => box.checked);
      let message = "";
      if (checked.length > 2 && event && event.target.type === "checkbox") {
        event.target.checked = false;
        checked = boxes.filter(box => box.checked);
        message = "最多選兩筆，請先取消其中一筆";
      }
      periodSelection.querySelector('button[type="submit"]').disabled = checked.length !== 2;
      periodSelection.querySelector("[data-period-selection-status]").textContent = message || `已選 ${checked.length} / 2 筆`;
      periodSelection.querySelector("[data-period-selected-labels]").textContent = checked.length
        ? checked.map(box => box.dataset.label).join(" 與 ") : "例如勾選 V1 與 V3，再按比較。";
      boxes.forEach(box => box.closest("tr").classList.toggle("is-selected", box.checked));
    };
    periodSelection.addEventListener("change", update);
    periodSelection.addEventListener("submit", event => {
      if (boxes.filter(box => box.checked).length !== 2) { event.preventDefault(); update(); }
    });
    update();
  }

  const comparisonForm = document.querySelector("[data-comparison-form]");
  if (comparisonForm) {
    const boxes = Array.from(document.querySelectorAll(".compare-select"));
    const storageKey = "quant-comparison-selection";
    let selected = [];
    try {
      const saved = JSON.parse(sessionStorage.getItem(storageKey) || "[]");
      if (Array.isArray(saved)) selected = saved.filter(item => item && typeof item.key === "string" && /^[a-f0-9]{64}$/.test(item.key) && typeof item.label === "string").slice(0, 2);
    } catch (_) {}
    const renderComparison = (message = "") => {
      boxes.forEach(box => { box.checked = selected.some(item => item.key === box.value); });
      const inputs = comparisonForm.querySelector("[data-comparison-inputs]");
      inputs.replaceChildren();
      selected.forEach(item => {
        const input = document.createElement("input");
        input.type = "hidden"; input.name = "run_keys"; input.value = item.key;
        inputs.append(input);
      });
      comparisonForm.querySelector("[data-comparison-selection]").textContent = selected.map(item => item.label).join(" ／ ");
      comparisonForm.querySelector("[data-comparison-status]").textContent = message || `已選 ${selected.length} / 2 筆，可跨版本頁選擇`;
      comparisonForm.querySelector("[data-comparison-submit]").disabled = selected.length !== 2;
      try { sessionStorage.setItem(storageKey, JSON.stringify(selected)); } catch (_) {}
    };
    boxes.forEach(box => box.addEventListener("change", () => {
      selected = selected.filter(item => item.key !== box.value);
      if (box.checked && selected.length === 2) {
        renderComparison("最多選兩筆，請先取消其中一筆"); return;
      }
      if (box.checked) selected.push({ key: box.value, label: box.dataset.label });
      renderComparison();
    }));
    comparisonForm.querySelector("[data-comparison-clear]").addEventListener("click", () => { selected = []; renderComparison(); });
    renderComparison();
  }

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
  const versionGroups = document.getElementById("strategy-version-groups");
  if (adjustmentFilters && versionGroups) {
    const cards = Array.from(versionGroups.querySelectorAll("[data-version-card]"));
    const visibleCount = document.getElementById("adjustment-visible-count");
    const emptyMessage = document.getElementById("adjustment-filter-empty");
    const applyAdjustmentFilters = () => {
      const values = Object.fromEntries(new FormData(adjustmentFilters).entries());
      const filtering = Object.values(values).some(Boolean);
      let count = 0;
      for (const card of cards) {
        const visible =
          (!values.recorded_from || card.dataset.recordedDate >= values.recorded_from) &&
          (!values.recorded_until || card.dataset.recordedDate <= values.recorded_until) &&
          (!values.strategy || card.dataset.strategy === values.strategy) &&
          (!values.timeframe || card.dataset.timeframe === values.timeframe) &&
          (!values.version || card.dataset.version === values.version) &&
          (!values.category || card.dataset.category === values.category);
        card.hidden = !visible;
        if (visible) count += 1;
      }
      for (const group of versionGroups.querySelectorAll("[data-version-group]")) {
        group.hidden = !Array.from(group.querySelectorAll("[data-version-card]")).some(card => !card.hidden);
      }
      for (const bucket of versionGroups.querySelectorAll("[data-catalog-section]")) {
        bucket.hidden = !Array.from(bucket.querySelectorAll("[data-version-card]")).some(card => !card.hidden);
        bucket.open = filtering ? !bucket.hidden : bucket.dataset.defaultOpen === "true";
      }
      visibleCount.textContent = String(count);
      emptyMessage.hidden = count !== 0;
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
    const archivedToggle = document.getElementById("show-archived-versions");
    const baseRunKey = backtest.elements.namedItem("base_run_key");
    const baseNote = document.getElementById("strategy-base-note");
    const options = Array.from(versionSelect.options).slice(1).map(option => option.cloneNode(true));
    const parameterNames = ["fast", "slow", "lookback", "momentum_threshold", "entry_deviation",
      "stop_loss_pct", "take_profit_pct", "intraday_strong_close", "intraday_min_atr_pct", "intraday_entry", "max_entries_per_day", "max_holding_bars", "higher_timeframe_filter", "risk_regime", "risk_per_trade_pct", "max_exposure_pct", "exit_mode", "stop_reentry_mode", "trend_entry_buffer_pct", "trailing_activation_pct", "trailing_distance_pct", "trailing_reentry_mode", "leverage"];
    const applyVersion = () => {
      const option = versionSelect.selectedOptions[0];
      const locked = Boolean(option && option.value);
      if (locked) {
        const params = JSON.parse(option.dataset.settings);
        for (const name of parameterNames) {
          const field = backtest.elements.namedItem(name);
          if (field && params[name] !== undefined) field.value = params[name];
        }
        baseRunKey.value = option.dataset.runKey;
      }
      const family = backtest.elements.namedItem("strategy").value;
      for (const name of parameterNames) {
        const field = backtest.elements.namedItem(name);
        if (field) {
          field.disabled = locked;
          if (name === "trend_entry_buffer_pct" && family !== "sma") field.value = "0";
          if (name === "risk_regime" && family !== "sma" && field.value === "slow_slope") field.value = "fixed";
          if (name === "higher_timeframe_filter" && family !== "sma") field.value = "false";
          const onlySma = ["fast", "slow", "trend_entry_buffer_pct", "higher_timeframe_filter"].includes(name);
          const onlyLookback = name === "lookback";
          field.closest("label").hidden = (onlySma && family !== "sma")
            || (onlyLookback && !["momentum", "mean-reversion"].includes(family))
            || (name === "momentum_threshold" && family !== "momentum")
            || (name === "entry_deviation" && family !== "mean-reversion")
            || (["intraday_entry", "intraday_min_atr_pct", "intraday_strong_close"].includes(name) && family !== "intraday");
        }
      }
      baseNote.hidden = false;
      baseNote.textContent = locked
        ? `${option.textContent}：使用此版本的固定參數，可以自由調整回測日期、資金和交易成本。`
        : "自訂參數：完成回測後會保存為候選版本。要測試既有版本，請在上方選擇版本。";
      backtest.dispatchEvent(new Event("input", { bubbles: true }));
    };
    const refreshVersions = (preferred, useLatest = false) => {
      const current = preferred === undefined ? versionSelect.value : preferred;
      const market = ["symbol", "timeframe", "strategy"].map(name => backtest.elements.namedItem(name).value);
      versionSelect.length = 1;
      for (const option of options) {
        if ([option.dataset.symbol, option.dataset.timeframe, option.dataset.strategy].every((v, i) => v === market[i])
            && (option.dataset.category !== "archived" || archivedToggle?.checked || option.value === current)) {
          versionSelect.append(option.cloneNode(true));
        }
      }
      versionSelect.value = current;
      if (!versionSelect.value && useLatest && versionSelect.options.length > 1) {
        const available = Array.from(versionSelect.options).slice(1);
        const preferredOption = available.find(option => option.dataset.category === "focus")
          || available.find(option => option.dataset.category === "candidate") || available[0];
        versionSelect.value = preferredOption.value;
      }
      applyVersion();
    };
    archivedToggle?.addEventListener("change", () => refreshVersions(undefined, false));
    versionSelect.addEventListener("change", applyVersion);
    for (const name of ["symbol", "timeframe", "strategy"]) {
      backtest.elements.namedItem(name).addEventListener("change", () => {
        baseRunKey.value = "";
        refreshVersions("", true);
      });
    }
    const query = new URLSearchParams(window.location.search);
    if (["advisor", "history", "development_branch"].includes(query.get("load_strategy"))) {
      for (const [name, value] of query.entries()) {
        if (["research_plan_id", "stage"].includes(name)) continue;
        const field = backtest.elements.namedItem(name);
        if (field) field.value = value;
      }
      // Advisor links intentionally create a custom candidate; history keeps its saved version.
      refreshVersions(query.get("load_strategy") === "advisor" ? "" : query.get("strategy_key") || "", false);
    } else {
      let hasSavedSelection = false;
      try { hasSavedSelection = Object.hasOwn(JSON.parse(localStorage.getItem(backtest.dataset.persistKey) || "{}"), "strategy_key"); } catch (_) {}
      refreshVersions(undefined, !hasSavedSelection);
    }
  }
});
