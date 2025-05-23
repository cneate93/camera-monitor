let chart = null;
let currentGroup = "All";
let camera_groups = {};
let previousStatus = {};
let silencedCameras = new Set(JSON.parse(localStorage.getItem("silencedCameras") || "[]"));

// Helper: fetch API with error handling
async function fetchAPI(path) {
    const res = await fetch(path);
    const json = await res.json();
    if (!json.success) throw new Error(json.error || "API error");
    return json.data;
}

// Load camera groups dynamically from API
async function loadCameraGroups() {
    try {
        camera_groups = await fetchAPI("/api/camera-groups");

        const dropdown = document.getElementById("camera-group-filter");
        dropdown.innerHTML = '<option value="All">All Cameras</option>';
        const groupSet = new Set(Object.values(camera_groups));
        groupSet.forEach(group => {
            dropdown.innerHTML += `<option value="${group}">${group} Cameras</option>`;
        });

        updateDashboard();
        requestNotificationPermission();
        applySavedTheme();
        dropdown.value = currentGroup;
    } catch (error) {
        console.error("Error fetching camera groups:", error);
        showStatusMessage('Failed to load camera groups. Please try again later.', true);
    }
}

// Request notification permissions
function requestNotificationPermission() {
    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }
}

function sendNotification(title, body) {
    if ("Notification" in window && Notification.permission === "granted") {
        new Notification(title, { body });
    }
}

// Silence Logic
function toggleSilence(camera) {
    if (silencedCameras.has(camera)) {
        silencedCameras.delete(camera);
    } else {
        silencedCameras.add(camera);
    }
    localStorage.setItem("silencedCameras", JSON.stringify([...silencedCameras]));
    updateDashboard();
}

function isSilenced(camera) {
    return silencedCameras.has(camera);
}

// Theme Toggle
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute("data-theme") || "dark";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    html.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
}

function applySavedTheme() {
    const savedTheme = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);
}

// Snapshot Modal
function showSnapshot(ip) {
    const modal = document.createElement("div");
    modal.id = "snapshot-modal";
    modal.style = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.85); display: flex; align-items: center; justify-content: center;
        z-index: 9999;
    `;
    const img = document.createElement("img");
    img.src = `http://${ip}/snapshot.jpg`; // Replace with your real snapshot URL
    img.alt = "Snapshot";
    img.style = "max-width: 90%; max-height: 90%; border: 4px solid white;";

    const close = document.createElement("div");
    close.innerText = "✖";
    close.style = `
        position: absolute; top: 20px; right: 30px; color: white;
        font-size: 24px; cursor: pointer;
    `;
    close.onclick = () => modal.remove();

    modal.appendChild(img);
    modal.appendChild(close);
    document.body.appendChild(modal);
}

// Dashboard Update
async function updateDashboard() {
    try {
        const [statusDataRaw, historyData, logData] = await Promise.all([
            fetchAPI("/api/status"),
            fetchAPI("/api/history"),
            fetchAPI("/api/events")
        ]);

        const statusData = filterByGroup(statusDataRaw);
        let tableHTML = "";

        for (let cam in statusData) {
            const info = statusData[cam];
            const rowClass = info.online ? "online" : "offline";
            const lastSeen = info.last_seen || "-";
            const duration = info.online_since ? formatDuration(info.online_since) : "-";
            const latency = info.latency !== undefined ? `${info.latency} ms` : "-";
            const uptime = info.uptime !== undefined ? `${info.uptime.toFixed(1)}%` : "-";

            if (previousStatus[cam] !== undefined && previousStatus[cam] !== info.online && !isSilenced(cam)) {
                const statusText = info.online ? "came ONLINE" : "went OFFLINE";
                sendNotification(`Camera ${cam}`, `Status Change: ${statusText}`);
            }
            previousStatus[cam] = info.online;

            const bellIcon = isSilenced(cam) ? "🔕" : "🔔";

            tableHTML += `
                <tr class="${rowClass}">
                    <td>${cam}</td>
                    <td>${info.ip}</td>
                    <td>${info.online ? "Online" : "Offline"}</td>
                    <td>${lastSeen}</td>
                    <td>${duration}</td>
                    <td>${latency}</td>
                    <td>${uptime}</td>
                    <td>
                        <button class="bell-toggle" onclick="toggleSilence('${cam}')">${bellIcon}</button>
                        <button class="snapshot-btn" onclick="showSnapshot('${info.ip}')">📷 View</button>
                    </td>
                </tr>
            `;
        }
        document.getElementById("camera-table").innerHTML = tableHTML;

        // Chart
        const labels = Object.values(historyData)[0]?.map(x => x.timestamp) || [];
        const datasets = [];
        const colors = ["#4caf50", "#f44336", "#2196f3", "#ff9800", "#9c27b0", "#00bcd4", "#ffc107"];
        let colorIndex = 0;

        for (let cam in historyData) {
            if (!statusData[cam]) continue;
            const data = historyData[cam].map(x => x.status === "online" ? 1 : 0);
            datasets.push({
                label: cam,
                data,
                fill: false,
                borderColor: colors[colorIndex % colors.length],
                pointBackgroundColor: colors[colorIndex % colors.length],
                tension: 0.3,
                borderWidth: 2
            });
            colorIndex++;
        }

        if (chart) {
            chart.data.labels = labels;
            chart.data.datasets = datasets;
            chart.update();
        } else {
            const ctx = document.getElementById("pingChart").getContext("2d");
            chart = new Chart(ctx, {
                type: 'line',
                data: { labels, datasets },
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            ticks: { autoSkip: true, maxTicksLimit: 10, color: '#ccc' },
                            title: { display: true, text: "Time", color: '#aaa' }
                        },
                        y: {
                            min: 0, max: 1,
                            ticks: { stepSize: 1, color: '#ccc' },
                            title: { display: true, text: "Status (1 = Online, 0 = Offline)", color: '#aaa' }
                        }
                    },
                    plugins: {
                        legend: { labels: { color: '#ddd', font: { size: 12 } } }
                    }
                }
            });
        }

        // Event Log
        const logContainer = document.getElementById("event-log");
        logContainer.innerHTML = "";
        logData.forEach(event => {
            const className = event.status === "online" ? "online" : "offline";
            logContainer.innerHTML += `<div class="log-line ${className}">[${event.timestamp}] ${event.camera} went ${event.status.toUpperCase()}</div>`;
        });

    } catch (err) {
        console.error("Dashboard update failed:", err);
        showStatusMessage('Failed to load dashboard data. Please try again later.', true);
    }
}

function filterByGroup(statusData) {
    if (currentGroup === "All") return statusData;
    const filtered = {};
    for (let cam in statusData) {
        if (camera_groups[cam] === currentGroup) {
            filtered[cam] = statusData[cam];
        }
    }
    return filtered;
}

function filterCamerasByGroup() {
    currentGroup = document.getElementById("camera-group-filter").value;
    updateDashboard();
}

function formatDuration(sinceEpoch) {
    const delta = Math.floor((Date.now() / 1000) - sinceEpoch);
    const hrs = Math.floor(delta / 3600);
    const mins = Math.floor((delta % 3600) / 60);
    const secs = delta % 60;
    return `${hrs}h ${mins}m ${secs}s`;
}

function showStatusMessage(message, isError = false) {
    const statusMessage = document.getElementById("status-message");
    statusMessage.textContent = message;
    statusMessage.style.display = 'block';
    statusMessage.classList.toggle('error', isError);
    setTimeout(() => {
        statusMessage.style.display = 'none';
    }, 5000);
}

// Init
loadCameraGroups();
setInterval(updateDashboard, 10000);