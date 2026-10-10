/* ═══════════════════════════════════════════════════════════
   SmartTrip AI — Frontend Application Logic
   ═══════════════════════════════════════════════════════════ */

const API_BASE = '';  // Same origin

// ─── State ───
let tripDestinations = [];
let knownPlaces = [];

// ─── Initialization ───
document.addEventListener('DOMContentLoaded', () => {
    setDefaultDate();
    loadPlaces();
    loadModelStats();
});

function setDefaultDate() {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateStr = tomorrow.toISOString().split('T')[0];
    const predictDate = document.getElementById('predict-date');
    const tripDate = document.getElementById('trip-date');
    if (predictDate) predictDate.value = dateStr;
    if (tripDate) tripDate.value = dateStr;
}

async function loadPlaces() {
    try {
        const resp = await fetch(`${API_BASE}/api/places`);
        if (!resp.ok) {
            // Model might not be trained yet — try training
            showToast('Training ML model for first use...', 'info');
            await trainModel();
            const resp2 = await fetch(`${API_BASE}/api/places`);
            if (!resp2.ok) throw new Error('Could not load places');
            const data = await resp2.json();
            knownPlaces = data.places;
        } else {
            const data = await resp.json();
            knownPlaces = data.places;
        }
        populatePlaceSelects();
    } catch (err) {
        showToast('Error loading destinations: ' + err.message, 'error');
    }
}

async function trainModel() {
    try {
        const resp = await fetch(`${API_BASE}/api/train`, { method: 'POST' });
        const data = await resp.json();
        if (data.success) {
            showToast('ML model trained successfully!', 'success');
        }
        return data;
    } catch (err) {
        showToast('Error training model: ' + err.message, 'error');
    }
}

async function loadModelStats() {
    try {
        const resp = await fetch(`${API_BASE}/api/metadata`);
        if (resp.ok) {
            const data = await resp.json();
            const r2El = document.getElementById('stat-r2');
            const modelEl = document.getElementById('stat-model');
            if (r2El && data.best_model_metrics) {
                r2El.textContent = (data.best_model_metrics.r2 * 100).toFixed(1) + '%';
            }
            if (modelEl && data.model_name) {
                modelEl.textContent = data.model_name.replace(' Regressor', '').replace('Regression', 'Reg.');
            }
        }
    } catch (err) {
        // Silently fail
    }
}

function populatePlaceSelects() {
    const selects = ['predict-place', 'trip-dest-select'];
    selects.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        // Keep first option
        while (el.options.length > 1) el.remove(1);
        knownPlaces.forEach(place => {
            const opt = document.createElement('option');
            opt.value = place;
            opt.textContent = `📍 ${place}`;
            el.appendChild(opt);
        });
    });
}


// ─── Page Navigation ───
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

    const page = document.getElementById(`page-${pageId}`);
    if (page) page.classList.add('active');

    const link = document.querySelector(`.nav-link[data-page="${pageId}"]`);
    if (link) link.classList.add('active');

    window.scrollTo({ top: 0, behavior: 'smooth' });
}


// ─── Prediction Flow ───
async function handlePredict(e) {
    e.preventDefault();

    const place = document.getElementById('predict-place').value;
    const date = document.getElementById('predict-date').value;
    const time = document.getElementById('predict-time').value;
    const transport = document.getElementById('predict-transport').value;
    const maxCrowd = document.getElementById('predict-max-crowd').value;
    const holiday = document.getElementById('predict-holiday').value;
    const event = document.getElementById('predict-event').value;

    if (!place || !date) {
        showToast('Please select a destination and date.', 'error');
        return;
    }

    // Show loading
    document.getElementById('predict-empty').style.display = 'none';
    document.getElementById('predict-result').style.display = 'none';
    document.getElementById('predict-loading').style.display = 'block';
    document.getElementById('predict-submit-btn').disabled = true;

    // Animate loading steps
    animateLoadingSteps(['ls-1', 'ls-2', 'ls-3', 'ls-4', 'ls-5']);

    try {
        const resp = await fetch(`${API_BASE}/api/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                place, date, time,
                max_crowd: maxCrowd,
                transportation_type: transport,
                holiday, event
            })
        });

        const data = await resp.json();

        if (data.error && typeof data.error === 'string') {
            throw new Error(data.error);
        }
        if (data.error === true && data.message) {
            throw new Error(data.message);
        }

        renderPredictionResult(data);

    } catch (err) {
        showToast('Prediction failed: ' + err.message, 'error');
        document.getElementById('predict-loading').style.display = 'none';
        document.getElementById('predict-empty').style.display = 'block';
    } finally {
        document.getElementById('predict-submit-btn').disabled = false;
    }
}

function renderPredictionResult(data) {
    document.getElementById('predict-loading').style.display = 'none';

    const resultArea = document.getElementById('predict-result');
    resultArea.style.display = 'block';

    const level = data.crowd_level || 'MEDIUM';
    const levelClass = level.toLowerCase();
    const crowdEmoji = level === 'LOW' ? '🟢' : level === 'MEDIUM' ? '🟡' : '🔴';

    // Weather HTML
    let weatherHTML = '';
    if (data.weather && data.weather.available) {
        const w = data.weather;
        const weatherEmoji = getWeatherEmoji(w.condition);
        weatherHTML = `
            <div class="weather-card">
                <span class="weather-icon">${weatherEmoji}</span>
                <div>
                    <div class="weather-temp">${w.temperature_max ?? '—'}°C</div>
                    <div class="weather-condition">${w.condition || 'Unknown'} • Rain: ${w.rain_probability ?? '—'}%</div>
                </div>
                <div class="confidence-badge" style="margin-left: auto;">
                    📡 Live forecast via ${w.source || 'API'}
                </div>
            </div>
        `;
    } else {
        weatherHTML = `
            <div class="weather-card">
                <span class="weather-icon">🌐</span>
                <div>
                    <div class="weather-condition" style="color: var(--gray-400);">
                        ${data.weather?.message || 'Live weather forecast unavailable. Prediction uses historical data.'}
                    </div>
                </div>
            </div>
        `;
    }

    // Hourly chart HTML
    let chartHTML = '';
    if (data.hourly_predictions && data.hourly_predictions.length > 0) {
        const maxCrowd = Math.max(...data.hourly_predictions.map(h => h.predicted_crowd));
        const recTime = data.recommended_time || data.requested_time;
        chartHTML = `
            <div style="margin-top: var(--space-xl);">
                <h4 style="font-family: var(--font-display); font-weight: 600; margin-bottom: var(--space-md); color: var(--gray-300);">
                    📊 Crowd Throughout the Day
                </h4>
                <div class="hourly-chart">
                    ${data.hourly_predictions.map(h => {
                        const pct = maxCrowd > 0 ? (h.predicted_crowd / maxCrowd * 100) : 10;
                        const cls = h.crowd_level.toLowerCase();
                        const isRec = h.time === recTime;
                        const timeLabel = formatTimeShort(h.time);
                        return `
                            <div class="hourly-bar-wrapper ${isRec ? 'recommended' : ''} tooltip">
                                <div class="hourly-bar-spacer"></div>
                                <div class="hourly-bar ${cls}" style="height: ${Math.max(pct, 5)}%;"></div>
                                <div class="hourly-label">${timeLabel}</div>
                                <div class="tooltip-content">${h.time} • ${h.predicted_crowd.toLocaleString()} • ${h.crowd_level}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    // Recommendation box
    let recHTML = '';
    const action = data.recommended_action;
    if (action === 'CHANGE_TIME') {
        recHTML = `
            <div class="recommendation-box">
                <div class="recommendation-title">💡 Smart Recommendation</div>
                <p class="recommendation-text">${data.explanation}</p>
                ${data.recommended_time ? `
                    <div style="margin-top: var(--space-md);">
                        <button class="btn btn-primary btn-sm" onclick="document.getElementById('predict-time').value='${data.recommended_time}'; showToast('Time updated to ${data.recommended_time}', 'success');">
                            ⏰ Use ${data.recommended_time} instead
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    } else if (action === 'CHANGE_DESTINATION') {
        recHTML = `
            <div class="recommendation-box danger">
                <div class="recommendation-title">⚠️ Destination is Crowded</div>
                <p class="recommendation-text">${data.explanation}</p>
                ${data.alternative_destinations && data.alternative_destinations.length > 0 ? `
                    <div class="alt-destinations-grid">
                        ${data.alternative_destinations.map(alt => `
                            <div class="alt-destination-card" onclick="document.getElementById('predict-place').value='${alt.place}'; showToast('Switched to ${alt.place}', 'success');">
                                <div class="alt-destination-name">📍 ${alt.place}</div>
                                <div style="display: flex; align-items: center; gap: var(--space-sm);">
                                    <span class="crowd-badge ${alt.crowd_level.toLowerCase()}">
                                        <span class="crowd-dot ${alt.crowd_level.toLowerCase()}"></span>
                                        ${alt.crowd_level}
                                    </span>
                                    <span style="color: var(--gray-500); font-size: 0.85rem;">${alt.predicted_crowd.toLocaleString()} visitors</span>
                                </div>
                                <div style="color: var(--gray-500); font-size: 0.8rem; margin-top: 6px;">at ${alt.time}</div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    } else if (action === 'NO_ALTERNATIVE') {
        recHTML = `
            <div class="recommendation-box warning">
                <div class="recommendation-title">⚠️ Limited Options</div>
                <p class="recommendation-text">${data.explanation}</p>
            </div>
        `;
    } else if (action === 'KEEP') {
        recHTML = `
            <div class="recommendation-box">
                <div class="recommendation-title">✅ Great Choice!</div>
                <p class="recommendation-text">${data.explanation}</p>
            </div>
        `;
    }

    resultArea.innerHTML = `
        <div class="result-card">
            <div class="result-hero">
                <div class="result-place-name">📍 ${data.selected_destination}</div>
                <span class="crowd-badge ${levelClass}" style="font-size: 0.9rem; padding: 0.5rem 1.2rem;">
                    <span class="crowd-dot ${levelClass}"></span>
                    ${level} CROWD
                </span>
                <div class="result-crowd-count ${levelClass}">
                    ${(data.predicted_crowd || 0).toLocaleString()}
                </div>
                <div class="result-crowd-label">Estimated visitors (in thousands)</div>
                <div class="confidence-badge" style="margin-top: var(--space-sm);">
                    🎯 Prediction confidence: ${data.confidence || 'Medium'}
                </div>
            </div>

            ${weatherHTML}
            ${chartHTML}
            ${recHTML}
        </div>
    `;
}


// ─── Trip Planner Flow ───
function addTripDestination() {
    const select = document.getElementById('trip-dest-select');
    const place = select.value;
    if (!place) return;
    if (tripDestinations.includes(place)) {
        showToast('Destination already added.', 'error');
        return;
    }

    tripDestinations.push(place);
    renderTripTags();
    select.value = '';
}

function removeTripDestination(place) {
    tripDestinations = tripDestinations.filter(d => d !== place);
    renderTripTags();
}

function renderTripTags() {
    const container = document.getElementById('trip-dest-tags');
    if (tripDestinations.length === 0) {
        container.innerHTML = '<span style="color: var(--gray-500); font-size: 0.85rem; padding: 0.3rem;">Add destinations below...</span>';
        return;
    }
    container.innerHTML = tripDestinations.map(d => `
        <span class="destination-tag">
            📍 ${d.split(',')[0]}
            <span class="remove-tag" onclick="removeTripDestination('${d}')">×</span>
        </span>
    `).join('');
}

async function handleTripPlan(e) {
    e.preventDefault();

    if (tripDestinations.length < 2) {
        showToast('Please add at least 2 destinations.', 'error');
        return;
    }

    const date = document.getElementById('trip-date').value;
    const startTime = document.getElementById('trip-start').value;
    const endTime = document.getElementById('trip-end').value;
    const transport = document.getElementById('trip-transport').value;
    const maxCrowd = document.getElementById('trip-max-crowd').value;

    if (!date) {
        showToast('Please select a date.', 'error');
        return;
    }

    // Show loading
    document.getElementById('trip-empty').style.display = 'none';
    document.getElementById('trip-result').style.display = 'none';
    document.getElementById('trip-loading').style.display = 'block';
    document.getElementById('trip-submit-btn').disabled = true;

    try {
        const resp = await fetch(`${API_BASE}/api/plan-trip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                destinations: tripDestinations,
                date,
                start_time: startTime,
                end_time: endTime,
                transportation_type: transport,
                max_crowd: maxCrowd
            })
        });

        const data = await resp.json();

        if (data.error && typeof data.error === 'string') {
            throw new Error(data.error);
        }
        if (data.error === true && data.message) {
            throw new Error(data.message);
        }

        renderTripResult(data);

    } catch (err) {
        showToast('Trip planning failed: ' + err.message, 'error');
        document.getElementById('trip-loading').style.display = 'none';
        document.getElementById('trip-empty').style.display = 'block';
    } finally {
        document.getElementById('trip-submit-btn').disabled = false;
    }
}

function renderTripResult(data) {
    document.getElementById('trip-loading').style.display = 'none';

    const resultArea = document.getElementById('trip-result');
    resultArea.style.display = 'block';

    if (!data.itinerary || data.itinerary.length === 0) {
        resultArea.innerHTML = `
            <div class="result-card">
                <div class="empty-state">
                    <div class="empty-state-icon">😔</div>
                    <h3 class="empty-state-title">Could not create itinerary</h3>
                    <p class="empty-state-desc">The time window may be too narrow or destinations conflict. Try adjusting your times.</p>
                </div>
            </div>
        `;
        return;
    }

    // Summary stats
    const summaryHTML = `
        <div class="stats-row" style="margin-bottom: var(--space-xl);">
            <div class="stat-item">
                <div class="stat-value">${data.total_destinations}</div>
                <div class="stat-label">Stops</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${data.average_crowd?.toLocaleString() || '—'}</div>
                <div class="stat-label">Avg. Crowd</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" style="color: var(--crowd-low);">${data.crowd_summary?.LOW || 0}</div>
                <div class="stat-label">Low Crowd</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" style="color: var(--crowd-high);">${data.crowd_summary?.HIGH || 0}</div>
                <div class="stat-label">High Crowd</div>
            </div>
        </div>
    `;

    // Timeline
    const timelineHTML = data.itinerary.map((item, i) => {
        const levelClass = (item.crowd_level || 'MEDIUM').toLowerCase();
        const crowdEmoji = item.crowd_level === 'LOW' ? '🟢' : item.crowd_level === 'MEDIUM' ? '🟡' : '🔴';
        const weatherEmoji = item.weather?.available ? getWeatherEmoji(item.weather.condition) : '🌐';
        const weatherText = item.weather?.available ? item.weather.condition : 'N/A';
        const rainText = item.weather?.available && item.weather.rain_probability != null
            ? `Rain: ${item.weather.rain_probability}%` : '';
        const tempText = item.weather?.available && item.weather.temperature_max != null
            ? `${item.weather.temperature_max}°C` : '';

        return `
            <div class="itinerary-item">
                <div class="itinerary-dot" style="border-color: var(--crowd-${levelClass});"></div>
                <div class="itinerary-item-card">
                    <div class="itinerary-time">${formatTimeDisplay(item.time)}</div>
                    <div class="itinerary-place">📍 ${item.place}</div>
                    <div class="itinerary-meta">
                        <div class="itinerary-meta-item">
                            <span class="crowd-badge ${levelClass}">
                                <span class="crowd-dot ${levelClass}"></span>
                                ${item.crowd_level}
                            </span>
                        </div>
                        <div class="itinerary-meta-item">
                            👥 ${item.predicted_crowd?.toLocaleString()} visitors
                        </div>
                        <div class="itinerary-meta-item">
                            ${weatherEmoji} ${weatherText}
                        </div>
                        ${tempText ? `<div class="itinerary-meta-item">🌡️ ${tempText}</div>` : ''}
                        ${rainText ? `<div class="itinerary-meta-item">☔ ${rainText}</div>` : ''}
                        <div class="itinerary-meta-item">
                            ⏱️ ~${item.visit_duration || 2}h visit
                        </div>
                    </div>
                    ${item.weather?.available && item.weather.rain_probability > 60 ? `
                        <div style="margin-top: var(--space-sm); padding: 0.4rem 0.8rem; background: rgba(255,193,7,0.1); border-radius: var(--radius-sm); font-size: 0.8rem; color: var(--crowd-medium);">
                            ☔ Rain likely — carry an umbrella
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');

    // Notes
    let notesHTML = '';
    if (data.optimization_notes && data.optimization_notes.length > 0) {
        notesHTML = `
            <div class="recommendation-box warning" style="margin-top: var(--space-xl);">
                <div class="recommendation-title">📝 Notes</div>
                ${data.optimization_notes.map(n => `<p class="recommendation-text">${n}</p>`).join('')}
            </div>
        `;
    }

    resultArea.innerHTML = `
        <div class="result-card">
            <div style="text-align: center; margin-bottom: var(--space-xl);">
                <h3 style="font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; color: white;">
                    ✨ Your Optimized Trip
                </h3>
                <p style="color: var(--gray-400); font-size: 0.9rem; margin-top: var(--space-xs);">
                    ${data.date} • ${data.start_time} – ${data.end_time}
                </p>
            </div>

            ${summaryHTML}

            <div class="itinerary-timeline">
                ${timelineHTML}
            </div>

            ${notesHTML}
        </div>
    `;
}


// ─── Utility Functions ───

function formatTimeShort(timeStr) {
    if (!timeStr) return '';
    const parts = timeStr.split(':');
    const hour = parseInt(parts[0]);
    if (hour === 0) return '12A';
    if (hour < 12) return hour + 'A';
    if (hour === 12) return '12P';
    return (hour - 12) + 'P';
}

function formatTimeDisplay(timeStr) {
    if (!timeStr) return '';
    const parts = timeStr.split(':');
    let hour = parseInt(parts[0]);
    const min = parts[1] || '00';
    const ampm = hour >= 12 ? 'PM' : 'AM';
    if (hour > 12) hour -= 12;
    if (hour === 0) hour = 12;
    return `${hour}:${min} ${ampm}`;
}

function getWeatherEmoji(condition) {
    if (!condition) return '🌐';
    const c = condition.toLowerCase();
    if (c.includes('clear') || c.includes('sunny')) return '☀️';
    if (c.includes('cloud')) return '☁️';
    if (c.includes('rain')) return '🌧️';
    if (c.includes('storm')) return '⛈️';
    if (c.includes('snow')) return '❄️';
    if (c.includes('fog')) return '🌫️';
    return '🌤️';
}

function animateLoadingSteps(stepIds) {
    stepIds.forEach((id, i) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.className = 'loading-step';
        setTimeout(() => {
            el.className = 'loading-step active';
            if (i > 0) {
                const prev = document.getElementById(stepIds[i-1]);
                if (prev) prev.className = 'loading-step done';
            }
        }, i * 400);
    });
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => {
        toast.className = 'toast';
    }, 4000);
}
