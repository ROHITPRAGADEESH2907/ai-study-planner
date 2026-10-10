/* ============================================================
   AI Study Planner — Study Planner Page Controller
   Connects to /api/plan, /api/plan/generate, /api/plan/rebalance.
   ============================================================ */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
    const daysContainer = document.getElementById('planner-days-container');
    if (!daysContainer) return;

    /* DOM elements */
    const loadingState = document.getElementById('planner-loading');
    const loadingText = document.getElementById('planner-loading-text');
    const emptyState = document.getElementById('planner-empty');
    const errorState = document.getElementById('planner-error');
    const errorText = document.getElementById('planner-error-text');

    const summaryStats = document.getElementById('planner-summary-stats');
    const statTotalSessions = document.getElementById('summary-total-sessions');
    const statTotalHours = document.getElementById('summary-total-hours');
    const statDateRange = document.getElementById('summary-date-range');
    const statLearningSessions = document.getElementById('summary-learning-sessions');
    const statRevisionSessions = document.getElementById('summary-revision-sessions');

    const alertBox = document.getElementById('planner-alert');
    const alertText = document.getElementById('planner-alert-text');
    const alertClose = document.getElementById('planner-alert-close');

    const btnGenerate = document.getElementById('btn-generate-plan');
    const btnRebalance = document.getElementById('btn-rebalance-plan');
    const btnEmptyGenerate = document.getElementById('btn-empty-generate');
    const btnRetry = document.getElementById('btn-retry-planner');

    /* Helpers */
    function escapeHtml(str) {
        return String(str == null ? '' : str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function showAlert(msg, isError = true) {
        if (!alertBox || !alertText) return;
        alertText.textContent = msg;
        alertBox.className = `alert ${isError ? 'alert--error' : 'alert--success'}`;
        alertBox.style.display = 'flex';
    }

    function hideAlert() {
        if (alertBox) alertBox.style.display = 'none';
    }

    if (alertClose) {
        alertClose.addEventListener('click', hideAlert);
    }

    function todayISO() {
        const d = new Date();
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
    }

    function formatDateHeading(isoDate) {
        if (!isoDate) return 'Unscheduled Date';
        const parts = isoDate.split('-');
        if (parts.length === 3) {
            const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
            return d.toLocaleDateString(undefined, {
                weekday: 'long',
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        }
        return isoDate;
    }

    function getDayBadge(isoDate) {
        const today = todayISO();
        if (isoDate === today) {
            return '<span class="planner-day-badge planner-day-badge--today">Today</span>';
        }
        const parts = isoDate.split('-');
        if (parts.length === 3) {
            const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
            const dayOfWeek = d.getDay(); // 0 is Sun, 6 is Sat
            if (dayOfWeek === 0 || dayOfWeek === 6) {
                return '<span class="planner-day-badge planner-day-badge--weekend">Weekend</span>';
            }
        }
        return '<span class="planner-day-badge planner-day-badge--weekday">Weekday</span>';
    }

    /* Render Sessions Grouped by Date */
    function renderPlan(sessions, summary = null) {
        loadingState.style.display = 'none';
        errorState.style.display = 'none';

        if (!sessions || sessions.length === 0) {
            emptyState.style.display = 'flex';
            daysContainer.style.display = 'none';
            summaryStats.style.display = 'none';
            return;
        }

        emptyState.style.display = 'none';
        daysContainer.style.display = 'block';

        // Group sessions by date
        const grouped = {};
        sessions.forEach(sess => {
            const d = sess.scheduled_date || 'Unscheduled';
            if (!grouped[d]) grouped[d] = [];
            grouped[d].push(sess);
        });

        // Compute or apply summary stats
        const totalHours = summary && summary.total_hours !== undefined
            ? Number(summary.total_hours)
            : sessions.reduce((acc, s) => acc + (Number(s.allocated_hours) || 0), 0);
        const learningCount = summary && summary.learning_sessions !== undefined
            ? Number(summary.learning_sessions)
            : sessions.filter(s => !s.is_revision).length;
        const revisionCount = summary && summary.revision_sessions !== undefined
            ? Number(summary.revision_sessions)
            : sessions.filter(s => s.is_revision).length;

        const dateKeys = Object.keys(grouped).sort();
        const firstDate = dateKeys[0];
        const lastDate = dateKeys[dateKeys.length - 1];

        statTotalSessions.textContent = String(sessions.length);
        statTotalHours.textContent = `${totalHours.toFixed(1)}h`;
        statLearningSessions.textContent = String(learningCount);
        statRevisionSessions.textContent = String(revisionCount);
        statDateRange.textContent = firstDate === lastDate ? firstDate : `${firstDate} to ${lastDate}`;
        summaryStats.style.display = 'grid';

        // Build HTML for each day card
        daysContainer.innerHTML = dateKeys.map(dStr => {
            const daySessions = grouped[dStr];
            const dayTotalHours = daySessions.reduce((acc, s) => acc + (Number(s.allocated_hours) || 0), 0);
            const dateTitle = formatDateHeading(dStr);
            const dayBadge = getDayBadge(dStr);

            const sessionsHtml = daySessions.map(s => {
                const color = escapeHtml(s.color_code || '#4F46E5');
                const hours = Number(s.allocated_hours || 0).toFixed(1);
                const isRev = s.is_revision;
                const typeLabel = s.session_type || (isRev ? 'revision' : 'learning');
                const badgeClass = isRev ? 'badge-type--revision' : 'badge-type--learning';

                return `
                    <div class="session-item">
                        <div class="session-info">
                            <span class="session-dot" style="background:${color};"></span>
                            <div class="session-details">
                                <div class="session-title">${escapeHtml(s.topic_title || 'Untitled Topic')}</div>
                                <div class="session-subtitle">${escapeHtml(s.subject_name || 'Subject')}</div>
                            </div>
                        </div>
                        <div class="session-meta">
                            <span class="badge-type ${badgeClass}">${escapeHtml(typeLabel)}</span>
                            <span class="session-duration">${hours} hrs</span>
                        </div>
                    </div>
                `;
            }).join('');

            return `
                <div class="planner-day-card">
                    <div class="planner-day-header">
                        <div class="planner-day-date">
                            <strong style="color:var(--color-text); font-size:0.95rem;">${escapeHtml(dateTitle)}</strong>
                            ${dayBadge}
                        </div>
                        <div class="planner-day-total">
                            ${daySessions.length} session${daySessions.length === 1 ? '' : 's'} &middot; ${dayTotalHours.toFixed(1)} hrs
                        </div>
                    </div>
                    <div>
                        ${sessionsHtml}
                    </div>
                </div>
            `;
        }).join('');
    }

    /* API Operations */
    async function loadPlan() {
        loadingState.style.display = 'flex';
        if (loadingText) loadingText.textContent = 'Loading study schedule...';
        emptyState.style.display = 'none';
        errorState.style.display = 'none';
        daysContainer.style.display = 'none';

        try {
            const res = await fetch('/api/plan');
            const data = await res.json();
            if (res.ok && data.success) {
                renderPlan(data.data || [], data.summary);
            } else {
                throw new Error(data.error || 'Failed to load study plan.');
            }
        } catch (err) {
            loadingState.style.display = 'none';
            errorState.style.display = 'flex';
            if (errorText) errorText.textContent = err.message || 'Error fetching study plan.';
        }
    }

    async function generatePlan() {
        hideAlert();
        loadingState.style.display = 'flex';
        if (loadingText) loadingText.textContent = 'Generating intelligent study schedule...';
        emptyState.style.display = 'none';
        errorState.style.display = 'none';
        daysContainer.style.display = 'none';

        btnGenerate.disabled = true;
        btnRebalance.disabled = true;

        try {
            const res = await fetch('/api/plan/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            const data = await res.json();
            if (res.ok && data.success) {
                showAlert(data.message || 'Study plan generated successfully!', false);
                renderPlan(data.data || [], data.summary);
                if (data.warnings && data.warnings.length) {
                    showAlert(data.warnings.join(' | '), true);
                }
            } else {
                throw new Error(data.error || 'Failed to generate study plan.');
            }
        } catch (err) {
            loadingState.style.display = 'none';
            showAlert(err.message || 'Network error generating plan.', true);
            await loadPlan();
        } finally {
            btnGenerate.disabled = false;
            btnRebalance.disabled = false;
        }
    }

    async function rebalancePlan() {
        hideAlert();
        loadingState.style.display = 'flex';
        if (loadingText) loadingText.textContent = 'Recalibrating schedule with completed progress...';
        emptyState.style.display = 'none';
        errorState.style.display = 'none';
        daysContainer.style.display = 'none';

        btnGenerate.disabled = true;
        btnRebalance.disabled = true;

        try {
            const res = await fetch('/api/plan/rebalance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await res.json();
            if (res.ok && data.success) {
                showAlert(data.message || 'Study plan rebalanced successfully!', false);
                renderPlan(data.data || [], data.summary);
                if (data.warnings && data.warnings.length) {
                    showAlert(data.warnings.join(' | '), true);
                }
            } else {
                throw new Error(data.error || 'Failed to rebalance study plan.');
            }
        } catch (err) {
            loadingState.style.display = 'none';
            showAlert(err.message || 'Network error rebalancing plan.', true);
            await loadPlan();
        } finally {
            btnGenerate.disabled = false;
            btnRebalance.disabled = false;
        }
    }

    /* Event Listeners */
    if (btnGenerate) btnGenerate.addEventListener('click', generatePlan);
    if (btnRebalance) btnRebalance.addEventListener('click', rebalancePlan);
    if (btnEmptyGenerate) btnEmptyGenerate.addEventListener('click', generatePlan);
    if (btnRetry) btnRetry.addEventListener('click', loadPlan);

    // Initial load
    loadPlan();
});
