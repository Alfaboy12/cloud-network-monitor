<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cloud-Based Network Monitoring & Performance Analysis</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Font Awesome Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <!-- Chart.js for real-time telemetry -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#eef8ff',
              500: '#0284c7',
              600: '#0369a1',
              900: '#082f49',
            }
          }
        }
      }
    }
  </script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen font-sans antialiased selection:bg-sky-500 selection:text-white">

  <!-- Top Navigation -->
  <header class="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-sky-500/20">
          <i class="fa-solid fa-network-wired text-lg"></i>
        </div>
        <div>
          <span class="text-lg font-bold tracking-tight text-white">NetPulse <span class="text-sky-400">Cloud</span></span>
          <span class="block text-xs text-slate-400">Network Assessment & Latency Engine</span>
        </div>
      </div>

      <!-- Live Stream Pill -->
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-full">
          <span class="relative flex h-2.5 w-2.5">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span class="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Telemetry Live</span>
        </div>
        <button onclick="window.print()" class="hidden md:inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm px-4 py-2 rounded-lg border border-slate-700 transition">
          <i class="fa-solid fa-file-pdf"></i>
          <span>Export Assessment</span>
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

    <!-- Executive Summary / Health Score (Auvik Style) -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <!-- Health Score -->
      <div class="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 flex items-center justify-between">
        <div>
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Network Health Score</p>
          <div class="flex items-baseline space-x-2 mt-1">
            <span class="text-3xl font-extrabold text-emerald-400">96.4%</span>
            <span class="text-xs font-semibold text-emerald-400/80"><i class="fa-solid fa-arrow-up"></i> Optimal</span>
          </div>
          <p class="text-xs text-slate-500 mt-2">Zero critical BGP anomalies</p>
        </div>
        <div class="w-14 h-14 rounded-full border-4 border-emerald-500/30 border-t-emerald-400 flex items-center justify-center font-bold text-emerald-400 text-sm">
          A+
        </div>
      </div>

      <!-- Current Latency -->
      <div class="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5">
        <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Avg Gateway Ping</p>
        <div class="flex items-baseline space-x-2 mt-1">
          <span id="stat-latency" class="text-3xl font-extrabold text-sky-400">18.4</span>
          <span class="text-sm font-medium text-slate-400">ms</span>
        </div>
        <div class="mt-2 text-xs flex justify-between text-slate-400">
          <span>Min: <b class="text-slate-200">12ms</b></span>
          <span>Max: <b class="text-slate-200">34ms</b></span>
        </div>
      </div>

      <!-- Packet Jitter -->
      <div class="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5">
        <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Network Jitter</p>
        <div class="flex items-baseline space-x-2 mt-1">
          <span id="stat-jitter" class="text-3xl font-extrabold text-indigo-400">1.8</span>
          <span class="text-sm font-medium text-slate-400">ms</span>
        </div>
        <p class="text-xs text-slate-400 mt-2">Packet Loss: <span id="stat-loss" class="font-bold text-emerald-400">0.00%</span></p>
      </div>

      <!-- Total Devices Discovered -->
      <div class="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5">
        <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Monitored Endpoints</p>
        <div class="flex items-baseline space-x-2 mt-1">
          <span class="text-3xl font-extrabold text-white">48</span>
          <span class="text-sm font-medium text-slate-400">Nodes</span>
        </div>
        <p class="text-xs text-slate-400 mt-2">46 Healthy • 2 High Bandwidth</p>
      </div>
    </div>

    <!-- Live Telemetry Section -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Live Latency Chart (2 Cols) -->
      <div class="lg:col-span-2 bg-slate-800/50 border border-slate-700/70 rounded-2xl p-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-700/60 gap-3">
          <div>
            <h2 class="text-base font-semibold text-white flex items-center gap-2">
              <i class="fa-solid fa-chart-line text-sky-400"></i>
              Real-Time Round Trip Time (RTT) Latency
            </h2>
            <p class="text-xs text-slate-400 mt-0.5">Continuous ICMP ping telemetry refreshed every 1,000ms</p>
          </div>
          <!-- Node Selector -->
          <div class="flex items-center space-x-2">
            <label class="text-xs text-slate-400">Probe Target:</label>
            <select id="targetSelector" class="bg-slate-900 border border-slate-700 text-xs rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500">
              <option value="cloudflare">Cloudflare Primary (1.1.1.1)</option>
              <option value="google">Google Public DNS (8.8.8.8)</option>
              <option value="aws">AWS US-East Gateway</option>
              <option value="local">Core Switch (10.0.0.1)</option>
            </select>
          </div>
        </div>

        <!-- Canvas -->
        <div class="mt-4 h-64 w-full">
          <canvas id="latencyChart"></canvas>
        </div>
      </div>

      <!-- Real-Time Interactive Ping Tool -->
      <div class="bg-slate-800/50 border border-slate-700/70 rounded-2xl p-6 flex flex-col justify-between">
        <div>
          <h2 class="text-base font-semibold text-white flex items-center gap-2">
            <i class="fa-solid fa-terminal text-emerald-400"></i>
            Diagnostic Ping Probe
          </h2>
          <p class="text-xs text-slate-400 mt-1">Send active diagnostic packets to calculate browser client-to-cloud route speed.</p>
          
          <div class="mt-4 space-y-3">
            <div>
              <label class="text-xs font-medium text-slate-400 block mb-1">Target Host or IP</label>
              <div class="flex space-x-2">
                <input id="pingInput" type="text" value="gateway.cloud-network.internal" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 flex-1 focus:outline-none focus:border-sky-500">
                <button id="runPingBtn" onclick="runDiagnosticTest()" class="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5">
                  <i class="fa-solid fa-play"></i> Ping
                </button>
              </div>
            </div>

            <!-- Terminal Window -->
            <div id="terminalWindow" class="bg-slate-950 font-mono text-[11px] p-3 rounded-lg border border-slate-800 text-slate-300 h-44 overflow-y-auto space-y-1">
              <div class="text-slate-500">[System] Initializing Network Probe daemon v4.12...</div>
              <div class="text-slate-500">[Ready] Continuous monitoring active.</div>
            </div>
          </div>
        </div>

        <div class="pt-4 border-t border-slate-700/50 flex justify-between items-center text-xs text-slate-400">
          <span>MTU: <b>1500 Bytes</b></span>
          <span>Protocol: <b>TCP/HTTPS + ICMP</b></span>
        </div>
      </div>
    </div>

    <!-- Network Inventory & Assessment Table (Auvik Style) -->
    <div class="bg-slate-800/50 border border-slate-700/70 rounded-2xl overflow-hidden shadow-xl">
      <div class="p-6 border-b border-slate-700/60 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 class="text-base font-semibold text-white flex items-center gap-2">
            <i class="fa-solid fa-server text-sky-400"></i>
            Discovered Infrastructure & Link Performance
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">Asset inventory, firmware security baseline, and link health index.</p>
        </div>
        <div class="flex space-x-2">
          <input type="text" id="filterInput" onkeyup="filterTable()" placeholder="Search device or IP..." class="bg-slate-900 border border-slate-700 text-xs px-3 py-1.5 rounded-lg text-slate-200 focus:outline-none focus:border-sky-500">
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs" id="deviceTable">
          <thead class="bg-slate-900/60 text-slate-400 uppercase font-semibold border-b border-slate-700/60">
            <tr>
              <th class="px-6 py-3.5">Device Identifier</th>
              <th class="px-6 py-3.5">Role</th>
              <th class="px-6 py-3.5">IP Address</th>
              <th class="px-6 py-3.5">Live Latency</th>
              <th class="px-6 py-3.5">Firmware / Health</th>
              <th class="px-6 py-3.5 text-right">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-700/40 text-slate-300">
            <tr class="hover:bg-slate-700/30 transition">
              <td class="px-6 py-4 font-medium text-white flex items-center gap-2">
                <i class="fa-solid fa-shield-halved text-sky-400"></i> FortiGate Core Firewall
              </td>
              <td class="px-6 py-4">Edge Firewall</td>
              <td class="px-6 py-4 font-mono">192.168.1.1</td>
              <td class="px-6 py-4 text-emerald-400 font-mono font-semibold">4.2 ms</td>
              <td class="px-6 py-4"><span class="bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">v7.2.4 (Latest)</span></td>
              <td class="px-6 py-4 text-right">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Operational</span>
              </td>
            </tr>
            <tr class="hover:bg-slate-700/30 transition">
              <td class="px-6 py-4 font-medium text-white flex items-center gap-2">
                <i class="fa-solid fa-layer-group text-indigo-400"></i> Cisco Catalyst 9300-48P
              </td>
              <td class="px-6 py-4">Distribution Switch</td>
              <td class="px-6 py-4 font-mono">192.168.1.2</td>
              <td class="px-6 py-4 text-emerald-400 font-mono font-semibold">6.8 ms</td>
              <td class="px-6 py-4"><span class="bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">IOS-XE 17.6</span></td>
              <td class="px-6 py-4 text-right">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Operational</span>
              </td>
            </tr>
            <tr class="hover:bg-slate-700/30 transition">
              <td class="px-6 py-4 font-medium text-white flex items-center gap-2">
                <i class="fa-solid fa-wifi text-amber-400"></i> Meraki MR56 AP Floor 2
              </td>
              <td class="px-6 py-4">Wireless AP</td>
              <td class="px-6 py-4 font-mono">192.168.10.45</td>
              <td class="px-6 py-4 text-amber-400 font-mono font-semibold">32.1 ms</td>
              <td class="px-6 py-4"><span class="bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">MR 29.5</span></td>
              <td class="px-6 py-4 text-right">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">High Traffic</span>
              </td>
            </tr>
            <tr class="hover:bg-slate-700/30 transition">
              <td class="px-6 py-4 font-medium text-white flex items-center gap-2">
                <i class="fa-brands fa-aws text-orange-400"></i> AWS Transit Gateway
              </td>
              <td class="px-6 py-4">Cloud Interconnect</td>
              <td class="px-6 py-4 font-mono">10.240.0.1</td>
              <td class="px-6 py-4 text-emerald-400 font-mono font-semibold">18.4 ms</td>
              <td class="px-6 py-4"><span class="bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Direct Connect 10G</span></td>
              <td class="px-6 py-4 text-right">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Operational</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>

  <!-- Script for Real-Time Telemetry and Charting -->
  <script>
    // Initialize Chart.js
    const ctx = document.getElementById('latencyChart').getContext('2d');
    const maxDataPoints = 25;
    const initialLabels = Array.from({length: maxDataPoints}, (_, i) => `${maxDataPoints - i}s ago`);
    const initialData = Array.from({length: maxDataPoints}, () => Math.floor(Math.random() * 8) + 16);

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(2, 132, 199, 0.45)');
    gradient.addColorStop(1, 'rgba(2, 132, 199, 0.0)');

    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: initialLabels,
        datasets: [{
          label: 'Latency (ms)',
          data: initialData,
          borderColor: '#38bdf8',
          borderWidth: 2,
          pointRadius: 2,
          pointBackgroundColor: '#38bdf8',
          tension: 0.35,
          fill: true,
          backgroundColor: gradient
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            grid: { color: 'rgba(51, 65, 85, 0.3)' },
            ticks: { color: '#64748b', font: { size: 10 } }
          },
          y: {
            min: 0,
            max: 60,
            grid: { color: 'rgba(51, 65, 85, 0.3)' },
            ticks: { color: '#64748b', font: { size: 10 }, callback: v => v + ' ms' }
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });

    // Real-Time Update Simulation Loop
    setInterval(() => {
      // Generate slight variance around target mean
      const base = 18;
      const jitter = (Math.random() * 8 - 4);
      const newLatency = Math.max(8, +(base + jitter).toFixed(1));

      // Update Chart
      chart.data.labels.shift();
      chart.data.labels.push('Now');
      chart.data.datasets[0].data.shift();
      chart.data.datasets[0].data.push(newLatency);
      chart.update('none');

      // Update Dashboard Stats
      document.getElementById('stat-latency').innerText = newLatency;
      document.getElementById('stat-jitter').innerText = (Math.random() * 1.5 + 0.8).toFixed(1);
    }, 1200);

    // Interactive Diagnostic Ping Terminal
    function runDiagnosticTest() {
      const host = document.getElementById('pingInput').value || 'gateway.local';
      const term = document.getElementById('terminalWindow');
      
      term.innerHTML += `<div class="text-sky-400 mt-2">> Initiating ICMP probe to ${host}...</div>`;
      term.scrollTop = term.scrollHeight;

      let count = 0;
      const interval = setInterval(() => {
        count++;
        const time = (Math.random() * 10 + 14).toFixed(2);
        term.innerHTML += `<div>64 bytes from ${host}: seq=${count} ttl=56 time=${time} ms</div>`;
        term.scrollTop = term.scrollHeight;

        if (count >= 4) {
          clearInterval(interval);
          term.innerHTML += `<div class="text-emerald-400 font-bold">--- ${host} ping statistics: 4 packets transmitted, 0% packet loss ---</div>`;
          term.scrollTop = term.scrollHeight;
        }
      }, 600);
    }

    // Filter Table
    function filterTable() {
      const q = document.getElementById('filterInput').value.toLowerCase();
      const rows = document.querySelectorAll('#deviceTable tbody tr');
      rows.forEach(r => {
        const text = r.textContent.toLowerCase();
        r.style.display = text.includes(q) ? '' : 'none';
      });
    }
  </script>
</body>
</html>
