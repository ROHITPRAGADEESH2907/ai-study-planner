/* ============================================================
   AI Study Planner — Analytics Page Controller
   Connects to /api/subjects, /api/subjects/<id>/topics, and /api/plan
   to calculate comprehensive metrics and visual progress bars.
   ============================================================ */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
    const analyticsContent = document.getElementById('analytics-content');
    if (!analyticsContent) return;

    /* DOM elements */
    const loadingState = document.getElementById('analytics-loading');
    const errorState = document.getElementById('analytics-error');
    const errorText = document.getElementById('analytics-error-text');
    const btnRetry = document.getElementById('btn-retry-analytics');

    const alertBox = document.getElementById('analytics-alert');
    const alertText = document.getElementById('analytics-alert-text');
    const alertClose = document.getElementById('analytics-alert-close');

    // Metrics elements
    const metricSubjects = document.getElementById('metric-subjects');
    const metricSubjectsSub = document.getElementById('metric-subjects-sub');
    const metricTopics = document.getElementById('metric-topics');
    const metricCompletedTopicsSub = document.getElementById('metric-completed-topics-sub');
    const metricCompletionRate = document.getElementById('metric-completion-rate');
    const metricPlannedHours = document.getElementById('metric-planned-hours');
    const metricSessionsSub = document.getElementById('metric-sessions-sub');

    // Progress card elements
    const completionBadge = document.getElementById('completion-badge');
    const completionRatioText = document.getElementById('completion-ratio-text');
    const overallProgressBar = document.getElementById('overall-progress-bar');

    const segmentCompleted = document.getElementById('segment-completed');
    const segmentInProgress = document.getElementById('segment-in-progress');
    const segmentNotStarted = document.getElementById('segment-not-started');
    const legendCompletedCount = document.getElementById('legend-completed-count');
    const legendInProgressCount = document.getElementById('legend-in-progress-count');
    const legendNotStartedCount = document.getElementById('legend-not-started-count');

    // Session breakdown elements
    const sessionCountBadge = document.getElementById('session-count-badge');
    const sessionLearningCount = document.getElementById('session-learning-count');
    const sessionLearningHours = document.getElementById('session-learning-hours');
    const sessionRevisionCount = document.getElementById('session-revision-count');
    const sessionRevisionHours = document.getElementById('session-revision-hours');
    const sessionCompletedCount = document.getElementById('session-completed-count');
    const sessionCompletedRate = document.getElementById('session-completed-rate');
    const sessionPendingCount = document.getElementById('session-pending-count');
    const sessionPendingHours = document.getElementById('session-pending-hours');

    // Subject readiness list elements
    const subjectBreakdownBadge = document.getElementById('subject-breakdown-badge');
    const subjectReadinessList = document.getElementById('subject-readiness-list');
    const subjectReadinessEmpty = document.getElementById('subject-readiness-empty');

    /* Helpers */
    function escapeHtml(str) {
        return String(str == null ? '' : str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function showAlert(msg) {
        if (!alertBox || !alertText) return;
        alertText.textContent = msg;
        alertBox.style.display = 'flex';
    }

    function hideAlert() {
        if (alertBox) alertBox.style.display = 'none';
    }

    if (alertClose) {
        alertClose.addEventListener('click', hideAlert);
    }

    function getDaysBadge(days) {
        const d = Number(days);
        if (!Number.isFinite(d)) return '<span class="list-item__badge">—</span>';
        if (d === 0) {
            return '<span class="list-item__badge list-item__badge--soon">Exam Today</span>';
        } else if (d === 1) {
            return '<span class="list-item__badge list-item__badge--soon">Tomorrow</span>';
        } else if (d <= 3) {
            return `<span class="list-item__badge list-item__badge--soon">${d} days left</span>`;
        } else if (d <= 14) {
            return `<span class="list-item__badge list-item__badge--upcoming">${d} days left</span>`;
        }
        return `<span class="list-item__badge list-item__badge--far">${d} days left</span>`;
    }

    /* Core Analytics Rendering */
    function renderAnalytics(subjects, topics, sessions) {
        loadingState.style.display = 'none';
        errorState.style.display = 'none';
        analyticsContent.style.display = 'block';

        const totalSubjects = subjects.length;
        const totalTopics = topics.length;

        // Topic Status Breakdown
        const completedTopics = topics.filter(t => t.status === 'completed').length;
        const inProgressTopics = topics.filter(t => t.status === 'in_progress').length;
        const notStartedTopics = topics.filter(t => t.status !== 'completed' && t.status !== 'in_progress').length;

        const topicCompletionRate = totalTopics === 0 ? 0 : Math.round((completedTopics / totalTopics) * 100);

        // Study Sessions Stats
        const totalSessions = sessions.length;
        const learningSessions = sessions.filter(s => !s.is_revision);
        const revisionSessions = sessions.filter(s => s.is_revision);
        const completedSessions = sessions.filter(s => s.status === 'completed');
        const pendingSessions = sessions.filter(s => s.status === 'pending');

        const totalPlannedHours = sessions.reduce((sum, s) => sum + (Number(s.allocated_hours) || 0), 0);
        const learningHours = learningSessions.reduce((sum, s) => sum + (Number(s.allocated_hours) || 0), 0);
        const revisionHours = revisionSessions.reduce((sum, s) => sum + (Number(s.allocated_hours) || 0), 0);
        const pendingHours = pendingSessions.reduce((sum, s) => sum + (Number(s.allocated_hours) || 0), 0);

        const sessionCompletionRate = totalSessions === 0 ? 0 : Math.round((completedSessions.length / totalSessions) * 100);

        // Top Metrics
        metricSubjects.textContent = String(totalSubjects);
        metricSubjectsSub.textContent = totalSubjects === 1 ? '1 active course' : `${totalSubjects} active courses`;

        metricTopics.textContent = String(totalTopics);
        metricCompletedTopicsSub.textContent = `${completedTopics} completed (${topicCompletionRate}%)`;

        metricCompletionRate.textContent = `${topicCompletionRate}%`;
        metricPlannedHours.textContent = `${totalPlannedHours.toFixed(1)}h`;
        metricSessionsSub.textContent = `${totalSessions} scheduled sessions`;

        // Topic Progress Card
        completionBadge.textContent = `${topicCompletionRate}%`;
        completionRatioText.textContent = `${completedTopics} / ${totalTopics} topics completed`;
        overallProgressBar.style.width = `${topicCompletionRate}%`;

        const completedPct = totalTopics ? ((completedTopics / totalTopics) * 100).toFixed(1) : '0';
        const inProgressPct = totalTopics ? ((inProgressTopics / totalTopics) * 100).toFixed(1) : '0';
        const notStartedPct = totalTopics ? ((notStartedTopics / totalTopics) * 100).toFixed(1) : '100';

        segmentCompleted.style.width = `${completedPct}%`;
        segmentInProgress.style.width = `${inProgressPct}%`;
        segmentNotStarted.style.width = `${notStartedPct}%`;

        legendCompletedCount.textContent = `${completedTopics} (${completedPct}%)`;
        legendInProgressCount.textContent = `${inProgressTopics} (${inProgressPct}%)`;
        legendNotStartedCount.textContent = `${notStartedTopics} (${notStartedPct}%)`;

        // Session Distribution Card
        sessionCountBadge.textContent = `${totalSessions} sessions`;
        sessionLearningCount.textContent = String(learningSessions.length);
        sessionLearningHours.textContent = `${learningHours.toFixed(1)} hrs`;

        sessionRevisionCount.textContent = String(revisionSessions.length);
        sessionRevisionHours.textContent = `${revisionHours.toFixed(1)} hrs`;

        sessionCompletedCount.textContent = String(completedSessions.length);
        sessionCompletedRate.textContent = `${sessionCompletionRate}% completed`;

        sessionPendingCount.textContent = String(pendingSessions.length);
        sessionPendingHours.textContent = `${pendingHours.toFixed(1)} hrs`;

        // Subject Readiness & Exam Timeline List
        subjectBreakdownBadge.textContent = `${totalSubjects} subject${totalSubjects === 1 ? '' : 's'}`;

        if (!totalSubjects) {
            subjectReadinessEmpty.style.display = 'flex';
            subjectReadinessList.innerHTML = '';
            return;
        }

        subjectReadinessEmpty.style.display = 'none';

        // Sort subjects by exam date ascending
        const sortedSubjects = [...subjects].sort((a, b) => {
            const dateA = a.exam_date || '9999-99-99';
            const dateB = b.exam_date || '9999-99-99';
            return dateA.localeCompare(dateB);
        });

        subjectReadinessList.innerHTML = sortedSubjects.map(sub => {
            const color = escapeHtml(sub.color_code || '#4F46E5');
            const totalSubTopics = sub.topic_count || 0;
            const completedSubTopics = sub.completed_topic_count || 0;
            const progress = sub.progress_percentage !== undefined ? sub.progress_percentage : (
                totalSubTopics ? Math.round((completedSubTopics / totalSubTopics) * 100) : 0
            );

            // Calculate total planned session hours for this subject
            const subSessions = sessions.filter(s => s.subject_id === sub.id || s.subject_name === sub.name);
            const subPlannedHours = subSessions.reduce((sum, s) => sum + (Number(s.allocated_hours) || 0), 0);

            return `
                <div class="list-item" style="padding: 16px 24px; flex-direction: column; align-items: stretch; gap: 10px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;">
                        <div style="display: flex; align-items: center; gap: 12px; min-width: 0;">
                            <span style="display:inline-block; width:12px; height:12px; border-radius:50%; background:${color}; flex-shrink:0;"></span>
                            <div>
                                <strong style="color:var(--color-text); font-size:0.95rem;">${escapeHtml(sub.name)}</strong>
                                <div style="font-size:0.8rem; color:var(--color-text-secondary); margin-top:2px;">
                                    Exam: ${escapeHtml(sub.exam_date || 'No date set')} &middot; Difficulty: ${sub.difficulty_level || 3}/5 &middot; ${subPlannedHours.toFixed(1)}h planned
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            ${getDaysBadge(sub.days_until_exam)}
                            <strong style="font-size:0.95rem; color:var(--color-text); min-width:44px; text-align:right;">${progress}%</strong>
                        </div>
                    </div>
                    <div class="progress-bar-container" style="height: 6px;">
                        <div class="progress-bar-fill" style="width: ${progress}%; background: ${color};"></div>
                    </div>
                </div>
            `;
        }).join('');
    }

    /* Data Fetching from Existing APIs */
    async function loadAnalyticsData() {
        loadingState.style.display = 'flex';
        errorState.style.display = 'none';
        analyticsContent.style.display = 'none';
        hideAlert();

        try {
            // 1. Fetch Subjects and Study Sessions concurrently
            const [subjectsRes, planRes] = await Promise.all([
                fetch('/api/subjects'),
                fetch('/api/plan')
            ]);

            const subjectsData = await subjectsRes.json();
            const planData = await planRes.json();

            if (!subjectsRes.ok || !subjectsData.success) {
                throw new Error(subjectsData.error || 'Failed to fetch subjects data.');
            }
            if (!planRes.ok || !planData.success) {
                throw new Error(planData.error || 'Failed to fetch plan sessions.');
            }

            const subjects = subjectsData.data || [];
            const sessions = planData.data || [];

            // 2. Fetch granular topics for each subject to obtain complete topic status
            const topicPromises = subjects.map(s => 
                fetch(`/api/subjects/${s.id}/topics`)
                    .then(res => res.json())
                    .then(data => (data.success && Array.isArray(data.data)) ? data.data : [])
                    .catch(() => [])
            );

            const topicArrays = await Promise.all(topicPromises);
            const allTopics = topicArrays.flat();

            renderAnalytics(subjects, allTopics, sessions);
        } catch (err) {
            loadingState.style.display = 'none';
            errorState.style.display = 'flex';
            if (errorText) errorText.textContent = err.message || 'Error fetching analytics data.';
        }
    }

    if (btnRetry) {
        btnRetry.addEventListener('click', loadAnalyticsData);
    }

    // Initial Load
    loadAnalyticsData();
});
