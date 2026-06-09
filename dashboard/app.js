// Global Chart instances to allow updates/destruction
let charts = {};
let currentTab = "page1";

// Disable animations globally for instant rendering in screenshots
Chart.defaults.animation = false;

// Active Slicer State
let filters = {
    fundHouse: "All",
    category: "All",
    plan: "All",
    state: "All",
    ageGroup: "All",
    cityTier: "All"
};

// Heatmap colors based on net inflow
function getHeatmapColor(value) {
    // Range of net inflows is roughly -500 to +1500 Crore.
    if (value > 1000) return "rgba(16, 185, 129, 0.9)"; // Strong Emerald
    if (value > 500) return "rgba(16, 185, 129, 0.7)";  // Emerald
    if (value > 100) return "rgba(16, 185, 129, 0.5)";  // Light Emerald
    if (value >= 0) return "rgba(16, 185, 129, 0.2)";   // Very light Emerald
    if (value > -100) return "rgba(239, 68, 68, 0.2)";   // Very light Red
    if (value > -500) return "rgba(239, 68, 68, 0.5)";   // Red
    return "rgba(239, 68, 68, 0.8)";                    // Strong Red
}

// Chart.js Theme configuration (Bluestock colors)
const bsThemes = {
    primary: "#414BEA",
    secondary: "#F05537",
    navy: "#012970",
    lightNavy: "rgba(1, 41, 112, 0.05)",
    gridColor: "#f1f5f9",
    success: "#10b981"
};

document.addEventListener("DOMContentLoaded", () => {
    // Populate header refresh date
    document.getElementById("refresh-date").innerText = dashboardData.latest_date;

    // Set up tab click listeners
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const tabId = item.getAttribute("data-tab");
            switchTab(tabId);
        });
    });

    // Reset button
    document.getElementById("btn-reset-filters").addEventListener("click", () => {
        resetFilters();
    });

    // Setup scorecard table sorting
    setupTableSorting();

    // Modal Close
    document.querySelector(".close-modal").addEventListener("click", () => {
        document.getElementById("drillmodal").style.display = "none";
    });
    window.addEventListener("click", (e) => {
        const modal = document.getElementById("drillmodal");
        if (e.target === modal) {
            modal.style.display = "none";
        }
    });

    // Initialize active tab from URL query parameter if present
    const urlParams = new URLSearchParams(window.location.search);
    const pageParam = urlParams.get('page');
    if (pageParam && ["page1", "page2", "page3", "page4"].includes(pageParam)) {
        switchTab(pageParam);
    } else {
        switchTab("page1");
    }
});

// Switch Tab logic
function switchTab(tabId) {
    currentTab = tabId;
    
    // Toggle active sidebar item
    document.querySelectorAll(".nav-item").forEach(btn => {
        if (btn.getAttribute("data-tab") === tabId) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // Toggle active tab content section
    document.querySelectorAll(".tab-content").forEach(sec => {
        if (sec.id === tabId) {
            sec.classList.add("active");
        } else {
            sec.classList.remove("active");
        }
    });

    // Update Header Text and Slicers panel
    const title = document.getElementById("page-title");
    const desc = document.getElementById("page-description");
    
    // Destroy all charts when switching to prevent visual glitches
    destroyAllCharts();

    if (tabId === "page1") {
        title.innerText = "Industry Overview";
        desc.innerText = "Mutual Fund assets, monthly inflows, active folios, and market share overview.";
        renderSlicers([]);
        initPage1();
    } else if (tabId === "page2") {
        title.innerText = "Fund Performance";
        desc.innerText = "Annualized returns, volatility risk scatter landscape, Nifty index benchmarking, and composite scorecard.";
        renderSlicers(["fundHouse", "category", "plan"]);
        initPage2();
    } else if (tabId === "page3") {
        title.innerText = "Investor Analytics";
        desc.innerText = "Geographic distribution of transaction inflows, demographic splits, average SIP ticket sizes, and volume lines.";
        renderSlicers(["state", "ageGroup", "cityTier"]);
        initPage3();
    } else if (tabId === "page4") {
        title.innerText = "SIP & Market Trends";
        desc.innerText = "Monthly SIP growth vs. Nifty index correlation, fund category net inflows heatmap, and top performers.";
        renderSlicers([]);
        initPage4();
    }
}

// Render Slicers dynamically in the header
function renderSlicers(slicerNames) {
    const container = document.getElementById("slicers-container");
    container.innerHTML = "";
    
    if (slicerNames.length === 0) {
        document.getElementById("btn-reset-filters").style.display = "none";
        return;
    }
    
    document.getElementById("btn-reset-filters").style.display = "inline-flex";

    slicerNames.forEach(name => {
        const group = document.createElement("div");
        group.className = "slicer-group";
        
        const label = document.createElement("span");
        label.className = "slicer-label";
        
        const select = document.createElement("select");
        select.className = "slicer-select";
        select.id = `select-${name}`;

        let options = ["All"];
        
        if (name === "fundHouse") {
            label.innerText = "Fund House";
            // Get unique fund houses from scorecard
            const fhouses = [...new Set(dashboardData.scorecard_data.map(d => d.fund_house))].sort();
            options = options.concat(fhouses);
            select.value = filters.fundHouse;
            select.addEventListener("change", (e) => {
                filters.fundHouse = e.target.value;
                updateTabVisuals();
            });
        } else if (name === "category") {
            label.innerText = "Category";
            const cats = [...new Set(dashboardData.scorecard_data.map(d => d.category))].sort();
            options = options.concat(cats);
            select.value = filters.category;
            select.addEventListener("change", (e) => {
                filters.category = e.target.value;
                updateTabVisuals();
            });
        } else if (name === "plan") {
            label.innerText = "Plan";
            const plans = [...new Set(dashboardData.scorecard_data.map(d => d.plan))].sort();
            options = options.concat(plans);
            select.value = filters.plan;
            select.addEventListener("change", (e) => {
                filters.plan = e.target.value;
                updateTabVisuals();
            });
        } else if (name === "state") {
            label.innerText = "State";
            options = options.concat(dashboardData.slicers.states);
            select.value = filters.state;
            select.addEventListener("change", (e) => {
                filters.state = e.target.value;
                updateTabVisuals();
            });
        } else if (name === "ageGroup") {
            label.innerText = "Age Group";
            options = options.concat(dashboardData.slicers.age_groups);
            select.value = filters.ageGroup;
            select.addEventListener("change", (e) => {
                filters.ageGroup = e.target.value;
                updateTabVisuals();
            });
        } else if (name === "cityTier") {
            label.innerText = "City Tier";
            options = options.concat(dashboardData.slicers.city_tiers);
            select.value = filters.cityTier;
            select.addEventListener("change", (e) => {
                filters.cityTier = e.target.value;
                updateTabVisuals();
            });
        }
        
        options.forEach(opt => {
            const o = document.createElement("option");
            o.value = opt;
            o.innerText = opt;
            select.appendChild(o);
        });

        group.appendChild(label);
        group.appendChild(select);
        container.appendChild(group);
    });
}

function resetFilters() {
    filters = {
        fundHouse: "All",
        category: "All",
        plan: "All",
        state: "All",
        ageGroup: "All",
        cityTier: "All"
    };
    
    // Update active selects
    document.querySelectorAll(".slicer-select").forEach(sel => {
        sel.value = "All";
    });
    
    updateTabVisuals();
}

function updateTabVisuals() {
    if (currentTab === "page2") {
        initPage2();
    } else if (currentTab === "page3") {
        initPage3();
    }
}

function destroyAllCharts() {
    Object.keys(charts).forEach(key => {
        if (charts[key]) {
            charts[key].destroy();
            charts[key] = null;
        }
    });
}

// ----------------------------------------------------
// Page 1: Industry Overview Initialization
// ----------------------------------------------------
function initPage1() {
    // Populate KPIs
    document.getElementById("val-aum").innerText = `₹${dashboardData.kpis.total_aum_lakh_cr}L Cr`;
    document.getElementById("val-sip").innerText = `₹${Number(dashboardData.kpis.sip_inflow_crore).toLocaleString("en-IN")} Cr`;
    document.getElementById("val-folios").innerText = `${dashboardData.kpis.folios_crore} Cr`;
    document.getElementById("val-schemes").innerText = Number(dashboardData.kpis.schemes_count).toLocaleString("en-IN");

    // Industry AUM Trend Chart
    const trendCtx = document.getElementById("chart-aum-trend").getContext("2d");
    const months = dashboardData.aum_trend.map(d => d.month);
    const aumVals = dashboardData.aum_trend.map(d => d.aum_lakh_crore);
    
    charts.aumTrend = new Chart(trendCtx, {
        type: "line",
        data: {
            labels: months,
            datasets: [{
                label: "Industry AUM (₹ Lakh Crore)",
                data: aumVals,
                borderColor: bsThemes.primary,
                backgroundColor: bsThemes.lightNavy,
                fill: true,
                tension: 0.3,
                borderWidth: 3,
                pointRadius: 4,
                pointBackgroundColor: bsThemes.primary
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: bsThemes.navy,
                    titleFont: { family: 'Inter', weight: 'bold' },
                    bodyFont: { family: 'Inter' }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: bsThemes.gridColor } }
            }
        }
    });

    // Market Share by AMC
    const amcCtx = document.getElementById("chart-aum-by-amc").getContext("2d");
    // Get top 8 and aggregate others
    let amcData = [...dashboardData.aum_by_amc];
    const topAMCs = amcData.slice(0, 7);
    const otherAUM = amcData.slice(7).reduce((acc, curr) => acc + curr.aum_lakh_crore, 0);
    
    const labels = topAMCs.map(d => d.amc.replace(" Mutual Fund", ""));
    const values = topAMCs.map(d => d.aum_lakh_crore);
    if (otherAUM > 0) {
        labels.push("Others");
        values.push(roundTo(otherAUM, 2));
    }

    charts.aumByAMC = new Chart(amcCtx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    bsThemes.primary,
                    "#585ee5",
                    "#6f74df",
                    "#8589d9",
                    "#9b9fd3",
                    "#b0b4ce",
                    "#c6c9c8",
                    "#94a3b8"
                ],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: bsThemes.navy }
            },
            scales: {
                x: { grid: { color: bsThemes.gridColor } },
                y: { grid: { display: false } }
            }
        }
    });
}

// ----------------------------------------------------
// Page 2: Fund Performance Initialization
// ----------------------------------------------------
function initPage2() {
    // Filter Scorecard and Scatter Data
    let filteredScorecard = [...dashboardData.scorecard_data];
    let filteredScatter = [...dashboardData.scatter_data];

    if (filters.fundHouse !== "All") {
        filteredScorecard = filteredScorecard.filter(d => d.fund_house === filters.fundHouse);
        filteredScatter = filteredScatter.filter(d => d.fund_house === filters.fundHouse);
    }
    if (filters.category !== "All") {
        filteredScorecard = filteredScorecard.filter(d => d.category === filters.category);
        filteredScatter = filteredScatter.filter(d => d.category === filters.category);
    }
    if (filters.plan !== "All") {
        filteredScorecard = filteredScorecard.filter(d => d.plan === filters.plan);
        filteredScatter = filteredScatter.filter(d => d.plan === filters.plan);
    }

    // Populate scorecard table
    populateScorecardTable(filteredScorecard);

    // Destroy old charts
    if (charts.riskReturn) charts.riskReturn.destroy();
    if (charts.navVsBenchmark) charts.navVsBenchmark.destroy();

    // Render Risk vs Return Scatter Landscape
    const scatterCtx = document.getElementById("chart-risk-return").getContext("2d");
    
    // Setup color mapping by category
    const catColors = {
        "Equity": bsThemes.primary,
        "Debt": bsThemes.success,
        "Hybrid": bsThemes.secondary,
        "Others": "#64748b"
    };

    const datasets = [];
    const categories = [...new Set(filteredScatter.map(d => d.category))];
    
    categories.forEach(cat => {
        const catPoints = filteredScatter.filter(d => d.category === cat);
        datasets.push({
            label: cat,
            data: catPoints.map(d => ({
                x: d.return_3yr_pct,
                y: d.std_dev_ann_pct,
                r: Math.max(3, Math.min(20, d.aum_crore / 2500)), // Scale bubble size
                name: d.scheme_name,
                aum: d.aum_crore
            })),
            backgroundColor: catColors[cat] || "#64748b",
            hoverBackgroundColor: bsThemes.navy,
            borderWidth: 1,
            borderColor: "#ffffff"
        });
    });

    charts.riskReturn = new Chart(scatterCtx, {
        type: "bubble",
        data: { datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top" },
                tooltip: {
                    backgroundColor: bsThemes.navy,
                    callbacks: {
                        label: function(context) {
                            const p = context.raw;
                            return [
                                p.name,
                                `3Y Return: ${p.x.toFixed(2)}%`,
                                `Risk (StdDev): ${p.y.toFixed(2)}%`,
                                `AUM: ₹${p.aum.toLocaleString("en-IN")} Cr`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: "3-Year Annualized Return (%)", font: { weight: "bold" } },
                    grid: { color: bsThemes.gridColor }
                },
                y: {
                    title: { display: true, text: "Annualized Risk/Standard Deviation (%)", font: { weight: "bold" } },
                    grid: { color: bsThemes.gridColor }
                }
            }
        }
    });

    // Render 3Y NAV vs Benchmark Growth (top performance)
    const benchmarkCtx = document.getElementById("chart-nav-vs-benchmark").getContext("2d");
    
    // Use datasets from data.js (nav_history contains top 5 and NIFTY50, NIFTY100)
    const benchDatasets = [];
    const colors = [
        bsThemes.primary,
        "#585ee5",
        "#6f74df",
        "#8589d9",
        "#9b9fd3"
    ];
    
    let colorIndex = 0;
    let dates = [];

    // Loop through nav_history
    Object.keys(dashboardData.nav_history).forEach(key => {
        const item = dashboardData.nav_history[key];
        
        if (key === "NIFTY50") {
            dates = item.dates;
            benchDatasets.push({
                label: "NIFTY 50",
                data: reindexSeries(item.values),
                borderColor: bsThemes.secondary,
                borderWidth: 2,
                pointRadius: 0,
                borderDash: [5, 5],
                fill: false
            });
        } else if (key === "NIFTY100") {
            benchDatasets.push({
                label: "NIFTY 100",
                data: reindexSeries(item.values),
                borderColor: "#64748b",
                borderWidth: 2,
                pointRadius: 0,
                borderDash: [3, 3],
                fill: false
            });
        } else {
            // It's a fund
            benchDatasets.push({
                label: key.replace(" - Regular Plan - Growth", "").replace(" - Direct Plan - Growth", ""),
                data: reindexSeries(item.navs),
                borderColor: colors[colorIndex++ % colors.length],
                borderWidth: 2,
                pointRadius: 0,
                fill: false
            });
        }
    });

    charts.navVsBenchmark = new Chart(benchmarkCtx, {
        type: "line",
        data: {
            labels: dates,
            datasets: benchDatasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top", labels: { boxWidth: 12, font: { size: 10 } } },
                tooltip: { backgroundColor: bsThemes.navy }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    title: { display: true, text: "Wealth Index (Base 100)" },
                    grid: { color: bsThemes.gridColor }
                }
            }
        }
    });
}

function reindexSeries(series) {
    if (series.length === 0) return [];
    const base = series[0];
    return series.map(val => (val / base) * 100);
}

function populateScorecardTable(data) {
    const tbody = document.getElementById("scorecard-tbody");
    tbody.innerHTML = "";
    
    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 24px; color: var(--text-secondary);">No funds match the selected filters.</td></tr>`;
        return;
    }

    // Sort data by composite score descending by default
    data.sort((a, b) => (b.composite_score || 0) - (a.composite_score || 0));

    data.forEach((row, idx) => {
        const tr = document.createElement("tr");
        
        // Setup row click drill-through handler
        tr.addEventListener("click", () => {
            openDrillThroughModal(row);
        });

        // Determine score class
        const score = Math.round(row.composite_score || 0);
        let scoreClass = "score-low";
        if (score >= 70) scoreClass = "score-high";
        else if (score >= 40) scoreClass = "score-med";

        tr.innerHTML = `
            <td><span class="rank-badge">${idx + 1}</span></td>
            <td class="val-bold" style="max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${row.scheme_name}">${row.scheme_name}</td>
            <td>${row.fund_house}</td>
            <td><span class="badge" style="background-color: var(--primary-light); color: var(--primary);">${row.category}</span></td>
            <td class="val-bold">${row.return_3yr_pct ? row.return_3yr_pct.toFixed(2) + '%' : 'N/A'}</td>
            <td>${row.sharpe_ratio ? row.sharpe_ratio.toFixed(2) : 'N/A'}</td>
            <td>${row.alpha ? row.alpha.toFixed(2) : 'N/A'}</td>
            <td>${row.expense_ratio_pct ? row.expense_ratio_pct.toFixed(2) + '%' : 'N/A'}</td>
            <td class="trend-down">${row.max_drawdown_pct ? row.max_drawdown_pct.toFixed(2) + '%' : 'N/A'}</td>
            <td><span class="score-badge ${scoreClass}">${score}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// Scorecard table column sorting
function setupTableSorting() {
    const headers = document.querySelectorAll("#scorecard-table th");
    headers.forEach(header => {
        header.addEventListener("click", () => {
            const sortBy = header.getAttribute("data-sort");
            let sortedData = [...dashboardData.scorecard_data];
            
            // Toggle sorting order
            const isAsc = header.classList.contains("asc");
            headers.forEach(h => h.classList.remove("asc", "desc"));
            
            if (isAsc) {
                header.classList.add("desc");
                sortedData.sort((a, b) => compareValues(a[sortBy], b[sortBy], false));
            } else {
                header.classList.add("asc");
                sortedData.sort((a, b) => compareValues(a[sortBy], b[sortBy], true));
            }

            // Re-filter before display
            if (filters.fundHouse !== "All") sortedData = sortedData.filter(d => d.fund_house === filters.fundHouse);
            if (filters.category !== "All") sortedData = sortedData.filter(d => d.category === filters.category);
            if (filters.plan !== "All") sortedData = sortedData.filter(d => d.plan === filters.plan);

            populateScorecardTable(sortedData);
        });
    });
}

function compareValues(a, b, asc) {
    if (a === undefined || a === null) return asc ? 1 : -1;
    if (b === undefined || b === null) return asc ? -1 : 1;
    if (typeof a === "string") {
        return asc ? a.localeCompare(b) : b.localeCompare(a);
    } else {
        return asc ? a - b : b - a;
    }
}

// ----------------------------------------------------
// Page 3: Investor Analytics Initialization
// ----------------------------------------------------
function initPage3() {
    // We will extract/filter transactions split, state details based on State slicer if applicable.
    // In our simplified JS data payload, we have pre-aggregated results. Let's render the charts.
    
    // Geographic Inflows State bar chart
    const stateCtx = document.getElementById("chart-state-inflows").getContext("2d");
    const states = dashboardData.state_trans.slice(0, 10).map(d => d.state);
    const stateAmounts = dashboardData.state_trans.slice(0, 10).map(d => d.amount_crore);
    
    charts.stateInflows = new Chart(stateCtx, {
        type: "bar",
        data: {
            labels: states,
            datasets: [{
                label: "Transaction Amount (₹ Crore)",
                data: stateAmounts,
                backgroundColor: bsThemes.primary,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: bsThemes.navy }
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: bsThemes.gridColor } }
            }
        }
    });

    // Donut Split (SIP vs Lumpsum vs Redemption)
    const donutCtx = document.getElementById("chart-transaction-split").getContext("2d");
    const splitTypes = Object.keys(dashboardData.type_split);
    const splitAmounts = splitTypes.map(k => dashboardData.type_split[k].amount_crore);
    
    charts.transactionSplit = new Chart(donutCtx, {
        type: "doughnut",
        data: {
            labels: splitTypes,
            datasets: [{
                data: splitAmounts,
                backgroundColor: [
                    bsThemes.primary,
                    bsThemes.secondary,
                    "#e2e8f0"
                ],
                borderWidth: 2,
                borderColor: "#ffffff"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "right" },
                tooltip: {
                    backgroundColor: bsThemes.navy,
                    callbacks: {
                        label: function(context) {
                            const val = context.raw;
                            const total = splitAmounts.reduce((a, b) => a + b, 0);
                            const pct = ((val / total) * 100).toFixed(2);
                            return `${context.label}: ₹${val.toLocaleString()} Cr (${pct}%)`;
                        }
                    }
                }
            },
            cutout: "60%"
        }
    });

    // Age group vs Average SIP Ticket Size
    const ageCtx = document.getElementById("chart-age-vs-sip").getContext("2d");
    const ageBrackets = dashboardData.age_sip.map(d => d.age_group);
    const ageAvgs = dashboardData.age_sip.map(d => d.avg_sip);

    charts.ageVsSip = new Chart(ageCtx, {
        type: "bar",
        data: {
            labels: ageBrackets,
            datasets: [{
                label: "Average Monthly SIP (₹)",
                data: ageAvgs,
                backgroundColor: bsThemes.secondary,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: bsThemes.navy }
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: bsThemes.gridColor } }
            }
        }
    });

    // Monthly Transaction Volume line
    const volCtx = document.getElementById("chart-monthly-volume").getContext("2d");
    const volMonths = dashboardData.volume_trend.map(d => d.month);
    const volCounts = dashboardData.volume_trend.map(d => d.count);

    charts.monthlyVolume = new Chart(volCtx, {
        type: "line",
        data: {
            labels: volMonths,
            datasets: [{
                label: "Number of Transactions",
                data: volCounts,
                borderColor: bsThemes.navy,
                backgroundColor: "rgba(1, 41, 112, 0.05)",
                fill: true,
                tension: 0.3,
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: bsThemes.navy
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: bsThemes.navy }
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: bsThemes.gridColor } }
            }
        }
    });
}

// ----------------------------------------------------
// Page 4: SIP & Market Trends Initialization
// ----------------------------------------------------
function initPage4() {
    // SIP Inflow (Bar) vs Nifty 50 Index (Line) Dual-Axis
    const sipNiftyCtx = document.getElementById("chart-sip-vs-nifty").getContext("2d");
    const months = dashboardData.sip_nifty.map(d => d.month);
    const sipInflows = dashboardData.sip_nifty.map(d => d.sip_inflow_crore);
    const niftyCloses = dashboardData.sip_nifty.map(d => d.nifty_close);

    charts.sipVsNifty = new Chart(sipNiftyCtx, {
        type: "bar",
        data: {
            labels: months,
            datasets: [
                {
                    label: "Monthly SIP Inflows (₹ Crore)",
                    data: sipInflows,
                    backgroundColor: "rgba(65, 75, 234, 0.65)",
                    borderColor: bsThemes.primary,
                    borderWidth: 1,
                    yAxisID: "y-sip",
                    borderRadius: 4
                },
                {
                    label: "Nifty 50 Index Close",
                    data: niftyCloses,
                    borderColor: bsThemes.secondary,
                    backgroundColor: "transparent",
                    borderWidth: 3,
                    type: "line",
                    pointRadius: 0,
                    yAxisID: "y-nifty",
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top" },
                tooltip: { backgroundColor: bsThemes.navy }
            },
            scales: {
                x: { grid: { display: false } },
                "y-sip": {
                    type: "linear",
                    position: "left",
                    title: { display: true, text: "SIP Inflows (₹ Crore)", font: { weight: "bold" } },
                    grid: { color: bsThemes.gridColor }
                },
                "y-nifty": {
                    type: "linear",
                    position: "right",
                    title: { display: true, text: "Nifty 50 Index Value", font: { weight: "bold" } },
                    grid: { display: false } // Avoid double grid lines
                }
            }
        }
    });

    // Top Categories Bar Chart
    const topCatCtx = document.getElementById("chart-top-categories").getContext("2d");
    const categories = dashboardData.top_categories_fy25.map(d => d.category);
    const netInflows = dashboardData.top_categories_fy25.map(d => d.net_inflow_crore);

    charts.topCategories = new Chart(topCatCtx, {
        type: "bar",
        data: {
            labels: categories,
            datasets: [{
                data: netInflows,
                backgroundColor: [
                    bsThemes.primary,
                    "#585ee5",
                    "#6f74df",
                    "#8589d9",
                    "#9b9fd3"
                ],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: bsThemes.navy }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    title: { display: true, text: "Net Inflow FY25 (₹ Crore)" },
                    grid: { color: bsThemes.gridColor }
                }
            }
        }
    });

    // Generate Net Inflow Heatmap
    buildHeatmap();
}

function buildHeatmap() {
    const grid = document.getElementById("heatmap-grid");
    grid.innerHTML = "";
    
    // Extact unique months and categories
    const months = [...new Set(dashboardData.heatmap_data.map(d => d.month))].sort();
    const categories = [...new Set(dashboardData.heatmap_data.map(d => d.category))].sort();
    
    // Add header row: Top-left empty label + month names
    const emptyHeader = document.createElement("div");
    emptyHeader.className = "heatmap-header-cell";
    grid.appendChild(emptyHeader);
    
    months.forEach(month => {
        const cell = document.createElement("div");
        cell.className = "heatmap-header-cell";
        // Convert '2024-05' to 'May-24' for compact display
        const dateParts = month.split("-");
        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const mName = monthNames[parseInt(dateParts[1]) - 1];
        cell.innerText = `${mName}-${dateParts[0].substring(2)}`;
        grid.appendChild(cell);
    });
    
    // Generate rows
    categories.forEach(cat => {
        // Row Label
        const rowLabel = document.createElement("div");
        rowLabel.className = "heatmap-row-label";
        rowLabel.innerText = cat;
        rowLabel.title = cat;
        grid.appendChild(rowLabel);
        
        // Heatmap Cells
        months.forEach(month => {
            const match = dashboardData.heatmap_data.find(d => d.month === month && d.category === cat);
            const val = match ? match.net_inflow_crore : 0;
            
            const cell = document.createElement("div");
            cell.className = "heatmap-cell";
            cell.style.backgroundColor = getHeatmapColor(val);
            cell.innerText = Math.round(val);
            cell.setAttribute("data-tooltip", `${cat} (${month}): ₹${Math.round(val)} Cr`);
            
            grid.appendChild(cell);
        });
    });
}

// ----------------------------------------------------
// Page 2 Drill-Through NAV Modal Logic
// ----------------------------------------------------
function openDrillThroughModal(schemeRow) {
    const modal = document.getElementById("drillmodal");
    modal.style.display = "block";
    
    document.getElementById("modal-scheme-name").innerText = schemeRow.scheme_name;
    document.getElementById("modal-scheme-meta").innerText = `Category: ${schemeRow.category} | Plan: ${schemeRow.plan} | Fund House: ${schemeRow.fund_house}`;
    
    document.getElementById("m-val-return").innerText = schemeRow.return_3yr_pct ? schemeRow.return_3yr_pct.toFixed(2) + '%' : 'N/A';
    document.getElementById("m-val-sharpe").innerText = schemeRow.sharpe_ratio ? schemeRow.sharpe_ratio.toFixed(2) : 'N/A';
    document.getElementById("m-val-alpha").innerText = schemeRow.alpha ? schemeRow.alpha.toFixed(2) + '%' : 'N/A';
    
    // Destroy old modal chart if any
    if (charts.modalNav) {
        charts.modalNav.destroy();
    }
    
    // Fetch NAV history for this scheme
    const history = dashboardData.drill_through_navs[schemeRow.amfi_code];
    if (!history) {
        // Fallback or warning if no daily history exists
        console.warn("No NAV history found for AMFI code", schemeRow.amfi_code);
        return;
    }
    
    const modalCtx = document.getElementById("chart-modal-nav").getContext("2d");
    
    // Reindex both the scheme NAV and Nifty 50 for direct comparison
    const baseNav = history.navs[0];
    const indexHistory = dashboardData.nav_history["NIFTY50"];
    
    // Align index values with the dates in history
    const alignedIndexVals = [];
    history.dates.forEach(date => {
        // Find index value on this date or closest previous
        const idx = indexHistory.dates.indexOf(date);
        if (idx !== -1) {
            alignedIndexVals.push(indexHistory.values[idx]);
        } else {
            // Find closest date in index history
            let closestVal = indexHistory.values[0];
            for (let i = 0; i < indexHistory.dates.length; i++) {
                if (indexHistory.dates[i] <= date) {
                    closestVal = indexHistory.values[i];
                } else {
                    break;
                }
            }
            alignedIndexVals.push(closestVal);
        }
    });
    
    const indexedNav = history.navs.map(v => (v / baseNav) * 100);
    const indexedIndex = alignedIndexVals.map(v => (v / alignedIndexVals[0]) * 100);

    charts.modalNav = new Chart(modalCtx, {
        type: "line",
        data: {
            labels: history.dates,
            datasets: [
                {
                    label: schemeRow.scheme_name.replace(" - Regular Plan - Growth", "").replace(" - Direct Plan - Growth", ""),
                    data: indexedNav,
                    borderColor: bsThemes.primary,
                    borderWidth: 2.5,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: "NIFTY 50 Benchmark",
                    data: indexedIndex,
                    borderColor: bsThemes.secondary,
                    borderWidth: 2,
                    pointRadius: 0,
                    borderDash: [5, 5],
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top" },
                tooltip: { backgroundColor: bsThemes.navy }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    title: { display: true, text: "Wealth Index (Base 100)" },
                    grid: { color: bsThemes.gridColor }
                }
            }
        }
    });
}

// Help utility
function roundTo(num, decimals) {
    return +(Math.round(num + "e+" + decimals) + "e-" + decimals);
}
