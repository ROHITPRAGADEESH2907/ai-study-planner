/* ============================================================
   AI Study Planner — Application JavaScript
   Foundation module with sidebar control, navigation state,
   and API helper stubs for future integration.
   ============================================================ */

'use strict';

const App = (() => {

    /* ---------- Configuration ---------- */
    const CONFIG = {
        API_BASE: '/api',
        ENDPOINTS: {
            health:     '/api/health',
            settings:   '/api/settings',
            subjects:   '/api/subjects',
            topics:     '/api/topics',
            planGen:    '/api/plan/generate',
            plan:       '/api/plan',
            rebalance:  '/api/plan/rebalance',
        },
    };

    /* ---------- State ---------- */
    const state = {
        currentPage: 'dashboard',
        sidebarOpen: false,
    };

    /* ---------- DOM References ---------- */
    let els = {};

    function cacheDom() {
        els = {
            sidebar:        document.getElementById('sidebar'),
            sidebarOverlay: document.getElementById('sidebar-overlay'),
            mobileToggle:   document.getElementById('mobile-toggle'),
            pageTitle:       document.getElementById('page-title'),
            navLinks:       document.querySelectorAll('.nav__link[data-page]'),
        };
    }

    /* ---------- Sidebar Toggle ---------- */
    function openSidebar() {
        if (!els.sidebar) return;
        els.sidebar.classList.add('open');
        els.sidebarOverlay.classList.add('visible');
        state.sidebarOpen = true;
    }

    function closeSidebar() {
        if (!els.sidebar) return;
        els.sidebar.classList.remove('open');
        els.sidebarOverlay.classList.remove('visible');
        state.sidebarOpen = false;
    }

    function toggleSidebar() {
        state.sidebarOpen ? closeSidebar() : openSidebar();
    }

    /* ---------- Navigation ---------- */
    function setActivePage(pageName) {
        state.currentPage = pageName;

        els.navLinks.forEach(link => {
            link.classList.toggle('active', link.dataset.page === pageName);
        });

        /* Update topbar page title to match the nav label */
        const activeLink = document.querySelector(`.nav__link[data-page="${pageName}"]`);
        if (activeLink && els.pageTitle) {
            const label = activeLink.querySelector('.nav__link-label');
            els.pageTitle.textContent = label ? label.textContent : pageName;
        }
    }

    function handleNavClick(e) {
        const link = e.currentTarget;
        const page = link.dataset.page;
        if (!page) return;

        const href = link.getAttribute('href');
        if (href && href !== '#' && href !== window.location.pathname) {
            // Allow native navigation between different HTML page routes
            return;
        }

        e.preventDefault();
        setActivePage(page);
        closeSidebar();
    }

    /* ---------- API Helpers (stubs) ---------- */

    /**
     * Generic fetch wrapper for future API integration.
     * @param {string} endpoint - URL path
     * @param {object} options  - fetch options (method, body, etc.)
     * @returns {Promise<object>} parsed JSON response
     */
    async function apiRequest(endpoint, options = {}) {
        const defaults = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
        };
        const config = { ...defaults, ...options };
        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(endpoint, config);
            const data = await response.json();
            return { ok: response.ok, status: response.status, data };
        } catch (err) {
            console.error(`[API] Request failed: ${endpoint}`, err);
            return { ok: false, status: 0, data: null, error: err.message };
        }
    }

    /** Convenience GET */
    function apiGet(endpoint) {
        return apiRequest(endpoint, { method: 'GET' });
    }

    /** Convenience POST */
    function apiPost(endpoint, body) {
        return apiRequest(endpoint, { method: 'POST', body });
    }

    /** Convenience PUT */
    function apiPut(endpoint, body) {
        return apiRequest(endpoint, { method: 'PUT', body });
    }

    /** Convenience DELETE */
    function apiDelete(endpoint) {
        return apiRequest(endpoint, { method: 'DELETE' });
    }

    /* ---------- Health Check ---------- */
    async function checkHealth() {
        const result = await apiGet(CONFIG.ENDPOINTS.health);
        const badge = document.getElementById('health-badge');
        if (!badge) return;

        if (result.ok && result.data && result.data.database === 'connected') {
            badge.innerHTML = '<span class="topbar__status-dot"></span> API Connected';
            badge.classList.remove('health--error');
        } else {
            badge.innerHTML = '<span class="topbar__status-dot" style="background:var(--color-danger)"></span> API Error';
            badge.classList.add('health--error');
        }
    }

    /* ---------- Dashboard Data Loading ---------- */
    const EMPTY_EXAMS_HTML =
        '<div class="placeholder-block">' +
            '<div class="placeholder-block__icon">📅</div>' +
            '<p class="placeholder-block__text">Upcoming exams will appear here once subjects are added.</p>' +
        '</div>';

    const EMPTY_TODAY_HTML =
        '<div class="placeholder-block">' +
            '<div class="placeholder-block__icon">📖</div>' +
            '<p class="placeholder-block__text">Today\'s study sessions will appear here after generating a plan.</p>' +
        '</div>';

    function escapeHtml(value) {
        return String(value == null ? '' : value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function todayISO() {
        const d = new Date();
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
    }

    function formatExamDate(isoDate) {
        if (!isoDate) return 'No exam date';
        const d = new Date(`${isoDate}T00:00:00`);
        if (Number.isNaN(d.getTime())) return isoDate;
        return d.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    }

    function daysLabel(days) {
        const n = Number(days);
        if (!Number.isFinite(n)) return '—';
        if (n <= 0) return 'Today';
        if (n === 1) return '1 day left';
        return `${n} days left`;
    }

    function examBadgeClass(days) {
        const n = Number(days);
        if (n <= 3) return 'list-item__badge--soon';
        if (n <= 14) return 'list-item__badge--upcoming';
        return 'list-item__badge--far';
    }

    function formatHours(hours) {
        const n = Number(hours);
        if (!Number.isFinite(n)) return '0';
        return Number.isInteger(n) ? String(n) : n.toFixed(1);
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function renderUpcomingExams(subjects) {
        const list = document.getElementById('upcoming-exams-list');
        if (!list) return;

        const today = todayISO();
        const upcoming = (subjects || [])
            .filter(s => s && s.exam_date && s.exam_date >= today)
            .sort((a, b) => String(a.exam_date).localeCompare(String(b.exam_date)));

        setText('exam-count-badge', String(upcoming.length));

        if (!upcoming.length) {
            list.innerHTML = EMPTY_EXAMS_HTML;
            return;
        }

        list.innerHTML = upcoming.map(subject => {
            const days = subject.days_until_exam;
            const color = escapeHtml(subject.color_code || '#4F46E5');
            return (
                `<div class="list-item">` +
                    `<div class="list-item__dot" style="background:${color}"></div>` +
                    `<div class="list-item__content">` +
                        `<div class="list-item__title">${escapeHtml(subject.name)}</div>` +
                        `<div class="list-item__meta">${escapeHtml(formatExamDate(subject.exam_date))}</div>` +
                    `</div>` +
                    `<span class="list-item__badge ${examBadgeClass(days)}">${escapeHtml(daysLabel(days))}</span>` +
                `</div>`
            );
        }).join('');
    }

    function renderTodayPlan(sessions) {
        const list = document.getElementById('today-plan-list');
        if (!list) return;

        const todaySessions = sessions || [];
        setText('today-session-badge', String(todaySessions.length));

        if (!todaySessions.length) {
            list.innerHTML = EMPTY_TODAY_HTML;
            return;
        }

        list.innerHTML = todaySessions.map(session => {
            const color = escapeHtml(session.color_code || '#4F46E5');
            const hours = formatHours(session.allocated_hours);
            const type = session.session_type || (session.is_revision ? 'revision' : 'learning');
            return (
                `<div class="list-item">` +
                    `<div class="list-item__dot" style="background:${color}"></div>` +
                    `<div class="list-item__content">` +
                        `<div class="list-item__title">${escapeHtml(session.topic_title || 'Untitled topic')}</div>` +
                        `<div class="list-item__meta">${escapeHtml(session.subject_name || 'Unknown subject')} · ${escapeHtml(hours)} h</div>` +
                    `</div>` +
                    `<span class="list-item__badge">${escapeHtml(type)}</span>` +
                `</div>`
            );
        }).join('');
    }

    function renderProgress(totalTopics, completedTopics) {
        const container = document.getElementById('progress-overview');
        if (!container) return;

        const total = Number(totalTopics) || 0;
        const completed = Number(completedTopics) || 0;
        const percent = total === 0 ? 0 : Math.round((completed / total) * 100);

        container.innerHTML =
            `<div class="stat-card__label">Overall completion</div>` +
            `<div class="stat-card__value">${percent}%</div>` +
            `<div class="stat-card__sub">${completed} of ${total} topics completed</div>`;
    }

    async function loadDashboard() {
        const examsList = document.getElementById('upcoming-exams-list');
        const todayList = document.getElementById('today-plan-list');
        if (!document.getElementById('stat-subjects')) return;

        const today = todayISO();
        const [subjectsRes, planRes, todayRes] = await Promise.all([
            apiGet(CONFIG.ENDPOINTS.subjects),
            apiGet(CONFIG.ENDPOINTS.plan),
            apiGet(`${CONFIG.ENDPOINTS.plan}?start_date=${today}&end_date=${today}`),
        ]);

        const subjects = (subjectsRes.ok && subjectsRes.data && Array.isArray(subjectsRes.data.data))
            ? subjectsRes.data.data
            : [];

        const subjectCount = subjectsRes.ok && subjectsRes.data && Number.isFinite(subjectsRes.data.count)
            ? subjectsRes.data.count
            : subjects.length;
        const topicCount = subjects.reduce((sum, s) => sum + (Number(s.topic_count) || 0), 0);
        const completedCount = subjects.reduce((sum, s) => sum + (Number(s.completed_topic_count) || 0), 0);

        const planSummary = planRes.ok && planRes.data && planRes.data.summary
            ? planRes.data.summary
            : null;
        const plannedHours = planSummary && Number.isFinite(Number(planSummary.total_hours))
            ? Number(planSummary.total_hours)
            : 0;

        const todaySessions = (todayRes.ok && todayRes.data && Array.isArray(todayRes.data.data))
            ? todayRes.data.data
            : [];

        setText('stat-subjects', String(subjectCount));
        setText('stat-topics', String(topicCount));
        setText('stat-completed', String(completedCount));
        setText('stat-hours', formatHours(plannedHours));

        if (examsList) renderUpcomingExams(subjects);
        if (todayList) renderTodayPlan(todaySessions);
        renderProgress(topicCount, completedCount);
    }

    /* ---------- Initialisation ---------- */
    function bindEvents() {
        /* Mobile sidebar toggle */
        if (els.mobileToggle) {
            els.mobileToggle.addEventListener('click', toggleSidebar);
        }

        /* Sidebar overlay click-to-close */
        if (els.sidebarOverlay) {
            els.sidebarOverlay.addEventListener('click', closeSidebar);
        }

        /* Navigation clicks */
        els.navLinks.forEach(link => {
            link.addEventListener('click', handleNavClick);
        });

        /* Close sidebar on Escape */
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && state.sidebarOpen) closeSidebar();
        });
    }

    function init() {
        cacheDom();
        bindEvents();
        const path = window.location.pathname;
        if (path === '/subjects') {
            setActivePage('subjects');
        } else if (path === '/topics') {
            setActivePage('topics');
        } else if (path === '/planner') {
            setActivePage('planner');
        } else if (path === '/analytics') {
            setActivePage('analytics');
        } else if (path === '/settings') {
            setActivePage('settings');
        } else {
            setActivePage('dashboard');
        }
        checkHealth();
        loadDashboard();
    }

    /* ---------- Public API ---------- */
    return {
        init,
        state,
        CONFIG,
        api: { get: apiGet, post: apiPost, put: apiPut, del: apiDelete },
    };

})();

/* Bootstrap on DOM ready */
document.addEventListener('DOMContentLoaded', App.init);
