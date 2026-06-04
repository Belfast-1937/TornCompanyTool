// ==================== 行业数据（来自 config.py） ====================
const INDUSTRY_MAP = {
  1: "Hair Salon", 2: "Law Firm", 3: "Flower Shop",
  4: "Car Dealership", 5: "Clothing Store", 6: "Gun Shop",
  7: "Game Shop", 8: "Candle Shop", 9: "Toy Shop",
  10: "Adult Novelties", 11: "Cyber Cafe", 12: "Grocery Store",
  13: "Theater", 14: "Sweet Shop", 15: "Cruise Line",
  16: "Television Network", 18: "Zoo", 19: "Firework Stand",
  20: "Property Broker", 21: "Furniture Store", 22: "Gas Station",
  23: "Music Store", 24: "Nightclub", 25: "Pub",
  26: "Gents Strip Club", 27: "Restaurant", 28: "Oil Rig",
  29: "Fitness Center", 30: "Mechanic Shop", 31: "Amusement Park",
  32: "Lingerie Store", 33: "Meat Warehouse", 34: "Farm",
  35: "Software Corporation", 36: "Ladies Strip Club",
  37: "Private Security Firm", 38: "Mining Corporation",
  39: "Detective Agency", 40: "Logistics Management"
};

// ==================== 初始化行业下拉框 ====================
function initIndustrySelect() {
  const sel = document.getElementById("industry-select");
  Object.entries(INDUSTRY_MAP).forEach(([id, name]) => {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = `${id} - ${name}`;
    sel.appendChild(opt);
  });
}

// ==================== localStorage API Key ====================
function saveApiKey() {
  const apiKey = document.getElementById("apikey-input").value.trim();
  if (!apiKey) return;
  showConfirm(
    "⚠️ 警告：API Key 将明文存储在浏览器本地存储(localStorage)中。\n\n任何能访问此浏览器的人都可以获取此 Key。是否继续？",
    function() {
      try { localStorage.setItem("torn_industry_api_key", apiKey); }
      catch (e) { showError("存储失败：" + e.message); }
    }
  );
}

function clearApiKey() {
  try { localStorage.removeItem("torn_industry_api_key"); }
  catch (e) {}
  document.getElementById("apikey-input").value = "";
}

function loadSavedApiKey() {
  try {
    const saved = localStorage.getItem("torn_industry_api_key");
    if (saved) {
      document.getElementById("apikey-input").value = saved;
    }
  } catch (e) {}
}

// ==================== 字段转写（与 data_processor.py get_industry_companies 一致） ====================
function extractCompanyRow(company) {
  const director = company.director || {};
  const income = company.income || {};
  const customers = company.customers || {};
  const employees = company.employees || {};

  return {
    CompanyID: company.id || 0,
    Name: company.name || "Unknown",
    DirectorName: (director != null && typeof director === "object" ? director.name : director) || "Unknown",
    DirectorID: (director != null && typeof director === "object" ? (director.id ?? director.player_id) : null) || null,
    Stars: company.rating || 0,
    Daily_Income: income.daily || 0,
    Weekly_Income: income.weekly || 0,
    Daily_Customers: customers.daily || 0,
    Weekly_Customers: customers.weekly || 0,
    Employees_Hired: employees.hired || 0,
    Employees_Capacity: employees.capacity || 0,
    Days_Old: company.days_old || 0,
    Rank: 0
  };
}

// ==================== API 数据获取（含分页） ====================
async function fetchAllIndustryCompanies(industryId, apiKey, signal) {
  const all = [];
  let offset = 0;
  const limit = 100;

  while (true) {
    const url = `https://api.torn.com/v2/company/${industryId}/companies?limit=${limit}&offset=${offset}&striptags=false&key=${apiKey}`;
    const resp = await fetch(url, { signal });

    if (!resp.ok) {
      const errText = await resp.text().catch(() => "");
      let errMsg = `HTTP ${resp.status}`;
      try {
        const json = JSON.parse(errText);
        if (json.error) errMsg = `${json.error.code || ""} ${json.error.error || json.error}`;
      } catch (_) {}
      throw new Error(errMsg);
    }

    const data = await resp.json();

    if (data.error) {
      const e = data.error;
      throw new Error(`[${e.code}] ${e.error}`);
    }

    const companies = data.companies || [];
    all.push(...companies);

    const nextLink = data._metadata?.links?.next;
    if (!nextLink || companies.length === 0) break;
    offset += limit;
  }

  return all;
}

// ==================== 全局状态（单对象封装） ====================
const state = {
  currentData: [],
  filteredData: [],
  searchTerm: "",
  sortColumn: "Stars",
  sortDirection: "desc",
  currentPage: 1,
  pageSize: 20,
  loading: false,
  abortController: null,
  searchTimer: null,
};

// ==================== 查询 ====================
async function doQuery() {
  const industryId = document.getElementById("industry-select").value;
  const apiKey = document.getElementById("apikey-input").value;

  if (!apiKey.trim()) {
    showError("请输入 API Key");
    return;
  }

  if (state.abortController) state.abortController.abort();
  state.abortController = new AbortController();

  state.loading = true;
  showLoading();

  try {
    const rawCompanies = await fetchAllIndustryCompanies(industryId, apiKey, state.abortController.signal);
    if (state.abortController.signal.aborted) return;

    const rows = rawCompanies.map(extractCompanyRow);
    // 按周收入降序分配排名
    rows.sort((a, b) => b.Weekly_Income - a.Weekly_Income);
    rows.forEach((r, i) => { r.Rank = i + 1; });

    state.currentData = rows;
    state.filteredData = rows;
    state.searchTerm = "";
    document.getElementById("search-input").value = "";
    state.sortColumn = "Stars";
    state.sortDirection = "desc";
    state.currentPage = 1;

    // 显示搜索栏和分析按钮
    document.getElementById("search-bar").style.display = "block";
    document.getElementById("analysis-btn").disabled = false;

    renderTable();
  } catch (err) {
    if (err.name === "AbortError") return;
    showError(err.message || String(err));
  } finally {
    state.loading = false;
    state.abortController = null;
  }
}

// ==================== 防抖搜索 ====================
function debounceSearch(value) {
  if (state.searchTimer) clearTimeout(state.searchTimer);
  state.searchTimer = setTimeout(() => handleSearch(value), 150);
}

function handleSearch(value) {
  state.searchTerm = value.trim();
  if (!state.searchTerm) {
    state.filteredData = state.currentData;
  } else {
    const termLower = state.searchTerm.toLowerCase();
    // 判断是否为纯数字
    const isNumeric = /^\d+$/.test(state.searchTerm);
    state.filteredData = state.currentData.filter(row => {
      if (isNumeric) {
        // 纯数字：匹配公司ID
        return String(row.CompanyID) === state.searchTerm || String(row.CompanyID).includes(state.searchTerm);
      }
      // 文本：匹配公司名称（不区分大小写）
      return row.Name.toLowerCase().includes(termLower);
    });
  }
  state.currentPage = 1;
  renderTable();
}

// ==================== 渲染 ====================
function showLoading() {
  document.getElementById("content-area").innerHTML = `
    <div class="loading-box">
      <div class="spinner"></div>
      <p>正在获取行业公司数据，请稍候...</p>
    </div>`;
}

function showError(msg) {
  document.getElementById("content-area").innerHTML = `
    <div class="error-box">
      <p style="font-size:18px;margin-bottom:8px;">❌ 请求失败</p>
      <p>${escapeHtml(msg)}</p>
    </div>`;
}

function showEmpty() {
  document.getElementById("content-area").innerHTML = `
    <div class="empty-box">
      <div class="icon">📭</div>
      <p>该行业暂无公司数据</p>
    </div>`;
}

function renderTable() {
  if (state.currentData.length === 0) {
    showEmpty();
    return;
  }

  // 如果过滤后为空
  if (state.filteredData.length === 0 && state.searchTerm) {
    document.getElementById("content-area").innerHTML = `
      <div class="search-result-info">
        未找到匹配「${escapeHtml(state.searchTerm)}」的公司
        <button onclick="clearSearch()">清除搜索</button>
      </div>
      <div class="empty-box">
        <div class="icon">🔍</div>
        <p>没有找到匹配的公司</p>
      </div>`;
    return;
  }

  // 对过滤后数据排序（多重排序：按主排序列排，主列相同时按周收入降序）
  const sorted = [...state.filteredData].sort((a, b) => {
    let va = a[state.sortColumn], vb = b[state.sortColumn];
    let cmp;
    if (typeof va === "string") {
      cmp = state.sortDirection === "asc"
        ? va.localeCompare(vb, "zh-Hans-CN")
        : vb.localeCompare(va, "zh-Hans-CN");
    } else {
      cmp = state.sortDirection === "asc" ? va - vb : vb - va;
    }
    // 主列相同时，按周收入降序
    if (cmp === 0) {
      cmp = b.Weekly_Income - a.Weekly_Income;
    }
    return cmp;
  });

  const totalPages = Math.ceil(sorted.length / state.pageSize);
  if (totalPages <= 0) totalPages = 1;
  if (state.currentPage > totalPages) state.currentPage = totalPages;
  const start = (state.currentPage - 1) * state.pageSize;
  const pageData = sorted.slice(start, start + state.pageSize);

  const colDefs = [
    { key: "Rank", label: "排名", cls: "center", isNum: true, width: "70px" },
    { key: "CompanyID", label: "公司ID", cls: "center", isNum: true, width: "90px" },
    { key: "Name", label: "公司名称", isName: true, width: "200px" },
    { key: "DirectorName", label: "董事", isDirector: true, width: "140px" },
    { key: "Stars", label: "星级", cls: "center", isStars: true, width: "110px" },
    { key: "Daily_Income", label: "日收入", cls: "num", isMoney: true, width: "100px" },
    { key: "Weekly_Income", label: "周收入", cls: "num", isMoney: true, width: "100px" },
    { key: "Daily_Customers", label: "日客户", cls: "num", isNum: true, width: "80px" },
    { key: "Weekly_Customers", label: "周客户", cls: "num", isNum: true, width: "80px" },
    { key: "Employees_Hired", label: "已雇佣", cls: "center", isNum: true, width: "75px" },
    { key: "Employees_Capacity", label: "员工容量", cls: "center", isNum: true, width: "80px" },
    { key: "Days_Old", label: "成立天数", cls: "num", isNum: true, width: "80px" },
  ];

  let theadHtml = "<tr>";
  colDefs.forEach(c => {
    const sortedCls = state.sortColumn === c.key ? " sorted" : "";
    const arrow = state.sortColumn === c.key
      ? (state.sortDirection === "asc" ? " ▲" : " ▼")
      : " ⇅";
    theadHtml += `<th class="${sortedCls}" onclick="handleSort('${c.key}')" style="min-width:${c.width}">${c.label}<span class="sort-arrow">${arrow}</span></th>`;
  });
  theadHtml += "</tr>";

  let tbodyHtml = "";
  pageData.forEach(row => {
    tbodyHtml += "<tr>";
    colDefs.forEach(c => {
      let val = row[c.key];
      if (c.isStars) {
        const cnt = Math.min(val, 10);
        tbodyHtml += `<td class="center"><span class="stars-gold">${"★".repeat(cnt)}${"☆".repeat(10 - cnt)}</span></td>`;
      } else if (c.isName) {
        const escaped = escapeHtml(val);
        const display = highlightInEscaped(escaped, state.searchTerm);
        tbodyHtml += `<td><a href="https://www.torn.com/company/${row.CompanyID}" target="_blank" rel="noopener">${display}</a></td>`;
      } else if (c.isDirector) {
        const escaped = escapeHtml(val);
        const display = highlightInEscaped(escaped, state.searchTerm);
        if (row.DirectorID) {
          tbodyHtml += `<td><a href="https://www.torn.com/profiles.php?XID=${row.DirectorID}" target="_blank" rel="noopener">${display}</a></td>`;
        } else {
          tbodyHtml += `<td>${display}</td>`;
        }
      } else if (c.isMoney) {
        tbodyHtml += `<td class="${c.cls}">$${(val || 0).toLocaleString()}</td>`;
      } else if (c.isNum && c.cls) {
        tbodyHtml += `<td class="${c.cls}">${(val || 0).toLocaleString()}</td>`;
      } else {
        tbodyHtml += `<td>${escapeHtml(String(val || ""))}</td>`;
      }
    });
    tbodyHtml += "</tr>";
  });

  const startNum = start + 1;
  const endNum = Math.min(start + state.pageSize, sorted.length);

  // 搜索信息
  let searchInfoHtml = "";
  if (state.searchTerm) {
    searchInfoHtml = `<div class="search-result-info">
      搜索「${escapeHtml(state.searchTerm)}」找到 ${sorted.length} 条结果（共 ${state.currentData.length} 条）
      <button onclick="clearSearch()">清除搜索</button>
    </div>`;
  }

  const paginationHtml = buildPagination(sorted.length, totalPages, startNum, endNum);

  document.getElementById("content-area").innerHTML = `
    ${searchInfoHtml}
    <table>
      <thead>${theadHtml}</thead>
      <tbody>${tbodyHtml}</tbody>
    </table>
    ${paginationHtml}
  `;
}

// 在已 escape 后的 HTML 安全字符串中做搜索高亮
// 先对搜索词做 escape 再构建正则，避免搜索词包含 HTML 特殊字符时误匹配
function highlightInEscaped(escapedText, rawTerm) {
  if (!rawTerm) return escapedText;
  const escapedTerm = escapeHtml(rawTerm);
  if (!escapedTerm) return escapedText;
  const re = new RegExp(`(${escapedTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  return escapedText.replace(re, '<span class="highlight">$1</span>');
}

function clearSearch() {
  document.getElementById("search-input").value = "";
  handleSearch("");
}

function buildPagination(total, totalPages, startNum, endNum) {
  let html = '<div class="pagination">';
  html += `<span class="info">共 ${total} 条，第 ${startNum}-${endNum} 条</span>`;
  html += `<button ${state.currentPage === 1 ? "disabled" : ""} onclick="goPage(1)">«</button>`;
  html += `<button ${state.currentPage === 1 ? "disabled" : ""} onclick="goPage(${state.currentPage - 1})">‹</button>`;

  const startP = Math.max(1, state.currentPage - 2);
  const endP = Math.min(totalPages, state.currentPage + 2);
  if (startP > 1) {
    html += `<button onclick="goPage(1)">1</button>`;
    if (startP > 2) html += `<span style="padding:0 4px;">...</span>`;
  }
  for (let i = startP; i <= endP; i++) {
    html += `<button class="${i === state.currentPage ? "active" : ""}" onclick="goPage(${i})">${i}</button>`;
  }
  if (endP < totalPages) {
    if (endP < totalPages - 1) html += `<span style="padding:0 4px;">...</span>`;
    html += `<button onclick="goPage(${totalPages})">${totalPages}</button>`;
  }

  html += `<button ${state.currentPage === totalPages ? "disabled" : ""} onclick="goPage(${state.currentPage + 1})">›</button>`;
  html += `<button ${state.currentPage === totalPages ? "disabled" : ""} onclick="goPage(${totalPages})">»</button>`;
  html += `<select onchange="changePageSize(this.value)">`;
  [10, 20, 50, 100, 200].forEach(s => {
    html += `<option value="${s}" ${state.pageSize === s ? "selected" : ""}>${s}条/页</option>`;
  });
  html += `</select>`;
  html += '</div>';
  return html;
}

function handleSort(colKey) {
  if (state.sortColumn === colKey) {
    state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
  } else {
    state.sortColumn = colKey;
    state.sortDirection = "asc";
  }
  state.currentPage = 1;
  renderTable();
}

function goPage(p) {
  state.currentPage = p;
  renderTable();
}

function changePageSize(size) {
  state.pageSize = parseInt(size);
  state.currentPage = 1;
  renderTable();
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ==================== 星级分析 ====================
function showAnalysis() {
  if (state.currentData.length === 0) return;

  const industryId = document.getElementById("industry-select").value;
  const industryName = INDUSTRY_MAP[industryId] || `ID ${industryId}`;
  document.getElementById("modal-title").textContent = `${industryName} - 星级分布与晋升门槛分析`;

  // 按周收入降序排列
  const allSorted = [...state.currentData].sort((a, b) => b.Weekly_Income - a.Weekly_Income);
  const totalCount = allSorted.length;

  // 统计各星级实际分布
  const starGroups = {};
  for (let s = 0; s <= 10; s++) starGroups[s] = [];
  allSorted.forEach(row => {
    const s = Math.min(row.Stars, 10);
    starGroups[s].push(row);
  });

  // 各星级实际数据（从10★到0★）
  const starStats = [];
  for (let s = 10; s >= 0; s--) {
    const companies = starGroups[s];
    if (companies.length > 0) {
      const w = companies.map(c => c.Weekly_Income);
      const d = companies.map(c => c.Daily_Income);
      starStats.push({
        star: s, count: companies.length,
        pct: (companies.length / totalCount) * 100,
        minWeekly: Math.min(...w), maxWeekly: Math.max(...w),
        minDaily: Math.min(...d), maxDaily: Math.max(...d),
      });
    } else {
      starStats.push({ star: s, count: 0, pct: 0,
        minWeekly: 0, maxWeekly: 0, minDaily: 0, maxDaily: 0 });
    }
  }

  // 用 Map 加速查找
  const starStatsMap = new Map(starStats.map(s => [s.star, s]));

  // ---------- 计算晋升门槛（占位者顺延） ----------
  let cumulativeCount = 0;
  const promotionThresholds = [];

  for (let s = 9; s >= 0; s--) {
    const targetStat = starStatsMap.get(s + 1);
    const targetPct = targetStat ? targetStat.pct : 0;
    const targetCount = Math.round(targetPct / 100 * totalCount);

    const quotaFrom = cumulativeCount + 1;
    cumulativeCount += targetCount;
    let quotaTo = s === 0 ? totalCount : cumulativeCount;
    quotaTo = Math.min(quotaTo, totalCount);

    if (quotaFrom > totalCount || targetCount === 0) {
      promotionThresholds.push({
        fromStar: s, toStar: s + 1,
        quotaFrom: quotaFrom, quotaTo: quotaTo,
        blockerCount: 0, thresholdRank: "—",
        thresholdWeekly: 0, thresholdDaily: 0,
        intervalDist: "—"
      });
      continue;
    }

    // 统计配额区间内各星级的分布
    const fromIdx = Math.max(0, quotaFrom - 1);
    const toIdx = Math.min(totalCount - 1, quotaTo - 1);
    const intervalCos = allSorted.slice(fromIdx, toIdx + 1);
    const distMap = {};
    intervalCos.forEach(c => {
      const st = Math.min(c.Stars, 10);
      distMap[st] = (distMap[st] || 0) + 1;
    });
    const distStr = Object.entries(distMap)
      .sort((a, b) => b[0] - a[0])
      .map(([st, cnt]) => `${st}★:${cnt}`).join(", ");

    const blockers = intervalCos.filter(c => Math.min(c.Stars, 10) < s).length;

    let thresholdRank = Math.min(quotaTo + blockers, totalCount);
    let thresholdCo = allSorted[thresholdRank - 1];
    while (thresholdCo && thresholdCo.Weekly_Income <= 0 && thresholdRank < totalCount) {
      thresholdRank++;
      thresholdCo = allSorted[thresholdRank - 1];
    }
    const validWeekly = (thresholdCo && thresholdCo.Weekly_Income > 0) ? thresholdCo.Weekly_Income : 0;
    const validDaily = validWeekly > 0 ? Math.ceil(validWeekly / 7) : 0;

    promotionThresholds.push({
      fromStar: s, toStar: s + 1,
      quotaFrom: quotaFrom, quotaTo: quotaTo,
      blockerCount: blockers,
      thresholdRank: thresholdRank,
      thresholdWeekly: validWeekly,
      thresholdDaily: validDaily,
      intervalDist: distStr
    });
  }

  // ========== 第一部分：各星级实际分布 ==========
  const isMobile = window.innerWidth < 768;
  let html = `<h3 style="margin-bottom:12px;color:#1677ff;">📋 各星级实际分布</h3>`;
  const maxCount = Math.max(...starStats.map(s => s.count), 1);

  if (isMobile) {
    // 移动端简略版：卡片列表
    html += `<div class="mobile-star-list">`;
    for (let s = 10; s >= 0; s--) {
      const stat = starStatsMap.get(s);
      const cnt = stat ? stat.count : 0;
      const pct = stat ? stat.pct : 0;
      const barWidth = Math.max((cnt / maxCount) * 80, cnt > 0 ? 2 : 0);
      html += `<div class="mobile-star-row">
        <span class="stars-gold">${"★".repeat(Math.min(s, 10))}</span>
        <span class="threshold-bar" style="width:${barWidth}px;height:6px;border-radius:3px;background:#1677ff;display:inline-block;vertical-align:middle;margin:0 6px;"></span>
        <span style="font-size:13px;">${cnt}家 (${pct.toFixed(1)}%)</span>
      </div>`;
    }
    html += `</div>`;
  } else {
    html += `<table style="margin-bottom:20px;">
      <thead>
        <tr>
          <th>星级</th><th>公司数</th><th>占比</th><th>分布</th>
          <th>周收入范围</th><th>日收入范围</th>
        </tr>
      </thead><tbody>`;
    for (let s = 10; s >= 0; s--) {
      const stat = starStatsMap.get(s);
      const cnt = stat ? stat.count : 0;
      const pct = stat ? stat.pct : 0;
      const barWidth = Math.max((cnt / maxCount) * 120, cnt > 0 ? 2 : 0);
      html += `<tr>
        <td class="center"><span class="stars-gold">${"★".repeat(Math.min(s, 10))}</span> ${s}★</td>
        <td class="center">${cnt}</td>
        <td class="center">${pct.toFixed(1)}%</td>
        <td style="width:130px;"><span class="threshold-bar" style="width:${barWidth}px;"></span></td>
        <td class="num">${cnt > 0 ? `$${stat.minWeekly.toLocaleString()} ~ $${stat.maxWeekly.toLocaleString()}` : "-"}</td>
        <td class="num">${cnt > 0 ? `$${stat.minDaily.toLocaleString()} ~ $${stat.maxDaily.toLocaleString()}` : "-"}</td>
      </tr>`;
    }
    html += `</tbody></table>`;
  }

  // ========== 第二部分：晋升门槛分析 ==========
  html += `<h3 style="margin-bottom:12px;color:#52c41a;">🚀 晋升门槛预估</h3>`;
  if (isMobile) {
    // 移动端简略版：方向 | 数量 | ≥周收入
    html += `<table style="margin-bottom:20px;">
      <thead>
        <tr><th>晋升方向</th><th>数量</th><th>≥周收入</th></tr>
      </thead><tbody>`;
    for (const pt of promotionThresholds) {
      if (pt.thresholdWeekly === 0 && pt.quotaFrom > totalCount) continue;
      const s = pt.fromStar;
      const target = pt.toStar;
      const count = pt.quotaTo - pt.quotaFrom + 1;
      html += `<tr>
        <td class="center" style="font-weight:600;">
          <span class="stars-gold" style="font-size:12px;">${s}★</span>
          <span style="margin:0 2px;">→</span>
          <span class="stars-gold" style="font-size:12px;">${target}★</span>
        </td>
        <td class="center">${count}家</td>
        <td class="num" style="font-weight:600;color:#1677ff;">${pt.thresholdWeekly > 0 ? `$${pt.thresholdWeekly.toLocaleString()}` : "—"}</td>
      </tr>`;
    }
    html += `</tbody></table>`;
  } else {
    html += `<table style="margin-bottom:20px;">
      <thead>
        <tr>
          <th>晋升方向</th><th>目标配额</th><th>区间内分布</th>
          <th style="color:#ff4d4f;">占位者</th><th>顺延至排名</th>
          <th>门槛周收入</th><th>门槛日收入</th>
        </tr>
      </thead><tbody>`;
    for (const pt of promotionThresholds) {
      if (pt.thresholdWeekly === 0 && pt.quotaFrom > totalCount) continue;
      const s = pt.fromStar;
      const target = pt.toStar;
      const targetStars = "★".repeat(Math.min(target, 10));
      html += `<tr>
        <td class="center" style="font-weight:600;">
          <span class="stars-gold">${"★".repeat(Math.min(s, 10))}</span> ${s}★
          <span style="margin:0 4px;">→</span>
          <span class="stars-gold">${targetStars}</span> ${target}★
        </td>
        <td class="center">#${pt.quotaFrom}–#${pt.quotaTo} (${pt.quotaTo - pt.quotaFrom + 1}家)</td>
        <td style="font-size:12px;max-width:250px;word-break:break-all;">${pt.intervalDist}</td>
        <td class="center" style="color:${pt.blockerCount > 0 ? '#ff4d4f' : '#888'};font-weight:${pt.blockerCount > 0 ? 600 : 400};">
          ${pt.blockerCount > 0 ? pt.blockerCount + ' 家' : '0'}
        </td>
        <td class="center" style="font-weight:600;">${typeof pt.thresholdRank === 'number' ? '#' + pt.thresholdRank : pt.thresholdRank}</td>
        <td class="num" style="font-weight:600;color:#1677ff;">
          ${pt.thresholdWeekly > 0 ? `≥ $${pt.thresholdWeekly.toLocaleString()}` : "—"}
        </td>
        <td class="num" style="color:#1677ff;">
          ${pt.thresholdDaily > 0 ? `≥ $${pt.thresholdDaily.toLocaleString()}` : "—"}
        </td>
      </tr>`;
    }
    html += `</tbody></table>`;
  }

  // ========== 说明 ==========
  const note = `
    <div class="note">
      <strong>📌 门槛推算逻辑：</strong><br>
      • <strong>占位者</strong>：在目标星级配额区间内，但当前星级过低、无法一步升到目标星级的公司<br>
      • 这些占位者升一星后会留出空位，由于一次只能升/降一星，空位向后顺延，导致实际门槛排名后移<br>
      • <strong>门槛</strong> = 顺延后排名位置的周收入 / 日收入<br>
      • 例如：10★ 配额前10名中有1家 8★（占位者），则 9★→10★ 门槛顺延至第 11 名的收入<br>
      • 行业总门店数：<strong>${totalCount} 家</strong>
    </div>`;

  document.getElementById("modal-body").innerHTML = html + note;
  document.getElementById("analysis-modal").classList.add("active");
}

function closeAnalysis() {
  document.getElementById("analysis-modal").classList.remove("active");
}

// 点击遮罩关闭
document.addEventListener("click", function(e) {
  if (e.target.id === "analysis-modal") {
    closeAnalysis();
  }
});
// ESC 关闭
document.addEventListener("keydown", function(e) {
  if (e.key === "Escape") {
    closeAnalysis();
    closeConfirmModal();
  }
});

// ==================== 确认对话框（替代 confirm()，移动端兼容） ====================
var _confirmCallback = null;
function showConfirm(message, onConfirm) {
  document.getElementById("confirm-message").textContent = message;
  _confirmCallback = onConfirm;
  document.getElementById("confirm-modal").classList.add("active");
}
function closeConfirmModal() {
  document.getElementById("confirm-modal").classList.remove("active");
  _confirmCallback = null;
}
document.addEventListener("click", function(e) {
  if (e.target.id === "confirm-modal") closeConfirmModal();
});
document.getElementById("confirm-ok-btn").addEventListener("click", function() {
  if (_confirmCallback) { _confirmCallback(); _confirmCallback = null; }
  closeConfirmModal();
});
document.getElementById("confirm-cancel-btn").addEventListener("click", closeConfirmModal);

// 鼠标探照灯效果
document.addEventListener("mousemove", (e) => {
  const mx = (e.clientX / window.innerWidth) * 100;
  const my = (e.clientY / window.innerHeight) * 100;
  document.body.style.setProperty("--mx", mx + "%");
  document.body.style.setProperty("--my", my + "%");
});
document.addEventListener("mouseleave", () => {
  document.body.style.setProperty("--mx", "50%");
  document.body.style.setProperty("--my", "50%");
});
document.body.style.setProperty("--mx", "50%");
document.body.style.setProperty("--my", "50%");

// Enter 键触发查询
document.addEventListener("DOMContentLoaded", () => {
  console.log("IndustryViewer v" + /*INJECT_VERSION*/);
  initIndustrySelect();
  loadSavedApiKey();
  document.getElementById("apikey-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") doQuery();
  });
});