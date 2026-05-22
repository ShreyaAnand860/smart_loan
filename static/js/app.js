function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
}

function calculateEmi() {
  const principal = Number(document.getElementById("principal")?.value || 0);
  const rate = Number(document.getElementById("rate")?.value || 0) / 1200;
  const months = Number(document.getElementById("months")?.value || 1);
  const emi = rate === 0 ? principal / months : principal * rate * ((1 + rate) ** months) / (((1 + rate) ** months) - 1);
  const total = emi * months;
  const interest = total - principal;
  document.getElementById("emiResult").textContent = formatCurrency(emi);
  document.getElementById("totalResult").textContent = `Total payment: ${formatCurrency(total)} | Interest: ${formatCurrency(interest)}`;
  renderEmiChart(principal, interest);
}

function renderEmiChart(principal = 1200000, interest = 347700) {
  const canvas = document.getElementById("emiChart");
  if (!canvas || !window.Chart) return;
  if (window.emiChart) window.emiChart.destroy();
  window.emiChart = new Chart(canvas, {
    type: "doughnut",
    data: { labels: ["Principal", "Interest"], datasets: [{ data: [principal, interest], backgroundColor: ["#0ea5a4", "#f5b84b"] }] },
    options: { plugins: { legend: { position: "bottom" } } }
  });
}

function renderDashboardCharts() {
  const statusEl = document.getElementById("status-data");
  const typeEl = document.getElementById("type-data");
  if (!statusEl || !window.Chart) return;
  const statuses = JSON.parse(statusEl.textContent);
  const types = JSON.parse(typeEl.textContent);
  new Chart(document.getElementById("statusChart"), {
    type: "bar",
    data: { labels: statuses.map(x => x.status), datasets: [{ label: "Applications", data: statuses.map(x => x.count), backgroundColor: "#0ea5a4" }] },
    options: { responsive: true, plugins: { legend: { display: false } } }
  });
  new Chart(document.getElementById("typeChart"), {
    type: "pie",
    data: { labels: types.map(x => x.loan_type__name || "Unknown"), datasets: [{ data: types.map(x => x.count), backgroundColor: ["#0ea5a4", "#f5b84b", "#5577d1", "#ef6f6c", "#334155"] }] }
  });
}


function bindSubmitOnceForms() {
  document.querySelectorAll("form.js-submit-once").forEach((form) => {
    form.addEventListener("submit", () => {
      const button = form.querySelector("button[type='submit']");
      if (!button || button.disabled) return;
      button.dataset.originalText = button.textContent;
      button.textContent = button.dataset.loadingText || "Submitting...";
      button.disabled = true;
    });
  });
}
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.dataset.bsTheme = theme;
  localStorage.setItem("smartloan-theme", theme);
  const toggle = document.getElementById("themeToggle");
  if (toggle) toggle.textContent = theme === "dark" ? "Light" : "Dark";
}

document.addEventListener("DOMContentLoaded", () => {
  renderEmiChart();
  bindSubmitOnceForms();
  const saved = localStorage.getItem("smartloan-theme") || "light";
  applyTheme(saved);
  document.getElementById("themeToggle")?.addEventListener("click", () => {
    applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  });
});
