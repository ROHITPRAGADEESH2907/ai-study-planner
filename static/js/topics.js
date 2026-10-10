/* ============================================================
   AI Study Planner — Topics Page Controller
   Connects to /api/subjects and /api/topics for management.
   ============================================================ */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('topics-tbody');
    if (!tableBody) return;

    /* DOM elements */
    const subjectFilter = document.getElementById('subject-filter');
    const subjectSummaryStats = document.getElementById('subject-summary-stats');
    const cardTitle = document.getElementById('topics-card-title');
    const countBadge = document.getElementById('topics-count-badge');

    const loadingState = document.getElementById('topics-loading');
    const noSubjectsState = document.getElementById('topics-no-subjects');
    const emptyState = document.getElementById('topics-empty');
    const errorState = document.getElementById('topics-error');
    const errorText = document.getElementById('topics-error-text');
    const tableWrapper = document.getElementById('topics-table-wrapper');
    const btnRetry = document.getElementById('btn-retry-topics');

    // Page alert
    const alertBox = document.getElementById('topic-alert');
    const alertText = document.getElementById('topic-alert-text');
    const alertClose = document.getElementById('topic-alert-close');

    // Modal elements
    const modalOverlay = document.getElementById('topic-modal-overlay');
    const modalTitle = document.getElementById('modal-topic-title');
    const modalClose = document.getElementById('modal-topic-close');
    const modalCancel = document.getElementById('modal-topic-cancel');
    const modalForm = document.getElementById('topic-form');
    const modalError = document.getElementById('modal-topic-error');
    const modalSubmit = document.getElementById('modal-topic-submit');
    const modalSubmitLabel = document.getElementById('modal-topic-submit-label');

    // Modal Form inputs
    const formId = document.getElementById('topic-form-id');
    const formSubjectSelect = document.getElementById('topic-subject-select');
    const formTitle = document.getElementById('topic-title');
    const formHours = document.getElementById('topic-estimated-hours');
    const formDifficulty = document.getElementById('topic-difficulty');
    const formStatus = document.getElementById('topic-status');

    const btnOpenAdd = document.getElementById('btn-open-add-topic');

    let subjectsCache = [];
    let topicsCache = [];
    let selectedSubjectId = null;

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

    function getDifficultyBadge(diff) {
        const d = Number(diff) || 3;
        const labels = {
            1: '1 (Very Easy)',
            2: '2 (Easy)',
            3: '3 (Moderate)',
            4: '4 (Challenging)',
            5: '5 (Very Hard)'
        };
        return escapeHtml(labels[d] || `Level ${d}`);
    }

    function getStatusBadge(status) {
        const s = String(status || 'not_started').toLowerCase();
        if (s === 'completed') {
            return `<span class="badge-status badge-status--completed">✅ Completed</span>`;
        } else if (s === 'in_progress') {
            return `<span class="badge-status badge-status--in_progress">⏳ In Progress</span>`;
        }
        return `<span class="badge-status badge-status--not_started">⚪ Not Started</span>`;
    }

    /* Modal management */
    function openModal(isEdit = false, topic = null) {
        if (!modalOverlay) return;
        hideAlert();
        if (modalError) modalError.style.display = 'none';

        // Check if there are subjects to attach to
        if (!subjectsCache.length) {
            showAlert('Please create at least one subject before adding topics.', true);
            return;
        }

        // Sync subject options in the modal form
        formSubjectSelect.innerHTML = subjectsCache.map(s => `
            <option value="${s.id}">${escapeHtml(s.name)}</option>
        `).join('');

        if (isEdit && topic) {
            modalTitle.textContent = 'Edit Topic';
            modalSubmitLabel.textContent = 'Update Topic';
            formId.value = topic.id;
            formSubjectSelect.value = String(topic.subject_id);
            formTitle.value = topic.title || '';
            formHours.value = topic.estimated_hours || 1.5;
            formDifficulty.value = String(topic.difficulty || 3);
            formStatus.value = topic.status || 'not_started';
        } else {
            modalTitle.textContent = 'Add New Topic';
            modalSubmitLabel.textContent = 'Save Topic';
            formId.value = '';
            modalForm.reset();
            if (selectedSubjectId) {
                formSubjectSelect.value = String(selectedSubjectId);
            }
            formHours.value = '1.5';
            formDifficulty.value = '3';
            formStatus.value = 'not_started';
        }

        modalOverlay.removeAttribute('hidden');
        formTitle.focus();
    }

    function closeModal() {
        if (modalOverlay) modalOverlay.setAttribute('hidden', '');
        if (modalError) modalError.style.display = 'none';
    }

    if (btnOpenAdd) btnOpenAdd.addEventListener('click', () => openModal(false));
    if (modalClose) modalClose.addEventListener('click', closeModal);
    if (modalCancel) modalCancel.addEventListener('click', closeModal);

    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) closeModal();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modalOverlay.hasAttribute('hidden')) {
            closeModal();
        }
    });

    /* Render Topics Table */
    function renderTopics(topics) {
        loadingState.style.display = 'none';
        errorState.style.display = 'none';
        noSubjectsState.style.display = 'none';

        if (!topics || topics.length === 0) {
            emptyState.style.display = 'flex';
            tableWrapper.style.display = 'none';
            if (countBadge) countBadge.textContent = '0 topics';
            return;
        }

        emptyState.style.display = 'none';
        tableWrapper.style.display = 'block';
        if (countBadge) countBadge.textContent = `${topics.length} topic${topics.length === 1 ? '' : 's'}`;

        tableBody.innerHTML = topics.map(t => {
            const isCompleted = t.status === 'completed';
            const toggleIcon = isCompleted ? '✅' : '⬜';
            const toggleTitle = isCompleted ? 'Mark as Not Completed' : 'Mark as Completed';

            return `
                <tr data-topic-id="${t.id}">
                    <td style="text-align: center;">
                        <button type="button" class="btn-toggle-status" data-id="${t.id}" data-status="${t.status}" title="${toggleTitle}">
                            ${toggleIcon}
                        </button>
                    </td>
                    <td>
                        <strong style="color:var(--color-text); font-size:0.95rem; text-decoration: ${isCompleted ? 'line-through' : 'none'}; opacity: ${isCompleted ? 0.75 : 1};">
                            ${escapeHtml(t.title)}
                        </strong>
                    </td>
                    <td>
                        <span style="color:var(--color-text-secondary);">${Number(t.estimated_hours).toFixed(1)} hrs</span>
                    </td>
                    <td>
                        <span style="font-size:0.85rem; color:var(--color-text-secondary);">${getDifficultyBadge(t.difficulty)}</span>
                    </td>
                    <td>
                        ${getStatusBadge(t.status)}
                    </td>
                    <td style="text-align: right;">
                        <div style="display:inline-flex; gap:8px;">
                            <button type="button" class="btn btn--secondary btn--sm btn-edit-topic" data-id="${t.id}" title="Edit Topic">
                                ✏️ Edit
                            </button>
                            <button type="button" class="btn btn--danger btn--sm btn-delete-topic" data-id="${t.id}" data-title="${escapeHtml(t.title)}" title="Delete Topic">
                                🗑️ Delete
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        // Action Handlers
        tableBody.querySelectorAll('.btn-toggle-status').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = Number(e.currentTarget.dataset.id);
                const currentStatus = e.currentTarget.dataset.status;
                const nextStatus = currentStatus === 'completed' ? 'not_started' : 'completed';
                await toggleTopicStatus(id, nextStatus);
            });
        });

        tableBody.querySelectorAll('.btn-edit-topic').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = Number(e.currentTarget.dataset.id);
                const topic = topicsCache.find(item => item.id === id);
                if (topic) openModal(true, topic);
            });
        });

        tableBody.querySelectorAll('.btn-delete-topic').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = Number(e.currentTarget.dataset.id);
                const title = e.currentTarget.dataset.title;
                if (confirm(`Are you sure you want to delete topic "${title}"?`)) {
                    await deleteTopic(id);
                }
            });
        });
    }

    /* Update subject overview stats bar */
    function updateSubjectStats(subject) {
        if (!subject) {
            subjectSummaryStats.innerHTML = '';
            return;
        }
        const totalHours = topicsCache.reduce((sum, t) => sum + (Number(t.estimated_hours) || 0), 0);
        const completedCount = topicsCache.filter(t => t.status === 'completed').length;
        const progress = topicsCache.length ? Math.round((completedCount / topicsCache.length) * 100) : 0;

        subjectSummaryStats.innerHTML = `
            <span><strong>Exam:</strong> ${escapeHtml(subject.exam_date || '—')}</span>
            <span><strong>Est. Total:</strong> ${totalHours.toFixed(1)} hrs</span>
            <span><strong>Progress:</strong> ${completedCount}/${topicsCache.length} (${progress}%)</span>
        `;
    }

    /* API Operations */
    async function fetchTopicsForSubject(subjectId) {
        if (!subjectId) return;
        loadingState.style.display = 'flex';
        emptyState.style.display = 'none';
        errorState.style.display = 'none';
        tableWrapper.style.display = 'none';

        try {
            const res = await fetch(`/api/subjects/${subjectId}/topics`);
            const data = await res.json();
            if (res.ok && data.success) {
                topicsCache = data.data || [];
                const currentSub = subjectsCache.find(s => s.id === Number(subjectId));
                if (currentSub && cardTitle) {
                    cardTitle.textContent = `${currentSub.name} — Topics`;
                }
                updateSubjectStats(currentSub);
                renderTopics(topicsCache);
            } else {
                throw new Error(data.error || 'Failed to load topics.');
            }
        } catch (err) {
            loadingState.style.display = 'none';
            errorState.style.display = 'flex';
            if (errorText) errorText.textContent = err.message || 'Error fetching topics.';
        }
    }

    async function loadSubjectsAndInit() {
        loadingState.style.display = 'flex';
        emptyState.style.display = 'none';
        noSubjectsState.style.display = 'none';
        errorState.style.display = 'none';
        tableWrapper.style.display = 'none';

        try {
            const res = await fetch('/api/subjects');
            const data = await res.json();
            if (res.ok && data.success) {
                subjectsCache = data.data || [];
                if (!subjectsCache.length) {
                    loadingState.style.display = 'none';
                    noSubjectsState.style.display = 'flex';
                    subjectFilter.innerHTML = '<option value="" disabled selected>No subjects available</option>';
                    if (countBadge) countBadge.textContent = '0 topics';
                    return;
                }

                // Check URL parameter for subject_id (?subject_id=123)
                const urlParams = new URLSearchParams(window.location.search);
                const paramSubjectId = Number(urlParams.get('subject_id'));

                if (paramSubjectId && subjectsCache.some(s => s.id === paramSubjectId)) {
                    selectedSubjectId = paramSubjectId;
                } else {
                    selectedSubjectId = subjectsCache[0].id;
                }

                subjectFilter.innerHTML = subjectsCache.map(s => `
                    <option value="${s.id}" ${s.id === selectedSubjectId ? 'selected' : ''}>
                        ${escapeHtml(s.name)}
                    </option>
                `).join('');

                await fetchTopicsForSubject(selectedSubjectId);
            } else {
                throw new Error(data.error || 'Failed to load subjects.');
            }
        } catch (err) {
            loadingState.style.display = 'none';
            errorState.style.display = 'flex';
            if (errorText) errorText.textContent = err.message || 'Error initializing topics page.';
        }
    }

    subjectFilter.addEventListener('change', async (e) => {
        selectedSubjectId = Number(e.target.value);
        hideAlert();
        await fetchTopicsForSubject(selectedSubjectId);
    });

    if (btnRetry) {
        btnRetry.addEventListener('click', () => {
            if (selectedSubjectId) {
                fetchTopicsForSubject(selectedSubjectId);
            } else {
                loadSubjectsAndInit();
            }
        });
    }

    /* Save (Create / Update) Topic */
    modalForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert();
        if (modalError) modalError.style.display = 'none';

        const id = formId.value ? Number(formId.value) : null;
        const targetSubjectId = Number(formSubjectSelect.value);
        const payload = {
            subject_id: targetSubjectId,
            title: formTitle.value.trim(),
            estimated_hours: parseFloat(formHours.value),
            difficulty: Number(formDifficulty.value),
            status: formStatus.value
        };

        modalSubmit.disabled = true;
        const originalLabel = modalSubmitLabel.textContent;
        modalSubmitLabel.textContent = 'Saving...';

        try {
            const endpoint = id ? `/api/topics/${id}` : '/api/topics';
            const method = id ? 'PUT' : 'POST';

            const res = await fetch(endpoint, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (res.ok && data.success) {
                closeModal();
                showAlert(id ? 'Topic updated successfully.' : 'Topic created successfully.', false);
                
                // If subject was changed or added under different subject, sync selector
                if (targetSubjectId !== selectedSubjectId) {
                    selectedSubjectId = targetSubjectId;
                    subjectFilter.value = String(selectedSubjectId);
                }
                await fetchTopicsForSubject(selectedSubjectId);
            } else {
                throw new Error(data.error || 'Failed to save topic.');
            }
        } catch (err) {
            if (modalError) {
                modalError.textContent = err.message || 'An error occurred while saving topic.';
                modalError.style.display = 'block';
            }
        } finally {
            modalSubmit.disabled = false;
            modalSubmitLabel.textContent = originalLabel;
        }
    });

    /* Toggle Status (Quick complete/incomplete) */
    async function toggleTopicStatus(id, newStatus) {
        hideAlert();
        try {
            const res = await fetch(`/api/topics/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                await fetchTopicsForSubject(selectedSubjectId);
            } else {
                throw new Error(data.error || 'Failed to update topic status.');
            }
        } catch (err) {
            showAlert(err.message || 'Error updating topic status.', true);
        }
    }

    /* Delete Topic */
    async function deleteTopic(id) {
        hideAlert();
        try {
            const res = await fetch(`/api/topics/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (res.ok && data.success) {
                showAlert('Topic deleted successfully.', false);
                await fetchTopicsForSubject(selectedSubjectId);
            } else {
                throw new Error(data.error || 'Failed to delete topic.');
            }
        } catch (err) {
            showAlert(err.message || 'Error deleting topic.', true);
        }
    }

    // Initialize page
    loadSubjectsAndInit();
});
