/* ============================================================
   AI Study Planner — Subjects Page Controller
   Connects to /api/subjects for CRUD operations.
   ============================================================ */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
    // Only run if we are on the subjects page
    const tableBody = document.getElementById('subjects-tbody');
    if (!tableBody) return;

    /* DOM elements */
    const loadingState = document.getElementById('subjects-loading');
    const emptyState = document.getElementById('subjects-empty');
    const errorState = document.getElementById('subjects-error');
    const errorText = document.getElementById('subjects-error-text');
    const tableWrapper = document.getElementById('subjects-table-wrapper');
    const countBadge = document.getElementById('subjects-count-badge');
    const btnRetry = document.getElementById('btn-retry-subjects');

    // Page alert
    const alertBox = document.getElementById('subject-alert');
    const alertText = document.getElementById('subject-alert-text');
    const alertClose = document.getElementById('subject-alert-close');

    // Modal elements
    const modalOverlay = document.getElementById('subject-modal-overlay');
    const modalTitle = document.getElementById('modal-subject-title');
    const modalClose = document.getElementById('modal-subject-close');
    const modalCancel = document.getElementById('modal-subject-cancel');
    const modalForm = document.getElementById('subject-form');
    const modalError = document.getElementById('modal-error-text');
    const modalSubmit = document.getElementById('modal-subject-submit');
    const modalSubmitLabel = document.getElementById('modal-submit-label');

    // Form inputs
    const formId = document.getElementById('subject-form-id');
    const formName = document.getElementById('subject-name');
    const formExamDate = document.getElementById('subject-exam-date');
    const formDifficulty = document.getElementById('subject-difficulty');
    const formColor = document.getElementById('subject-color');
    const formColorPreview = document.getElementById('subject-color-preview');

    const btnOpenAdd = document.getElementById('btn-open-add-modal');

    let subjectsCache = [];

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

    if (formColor) {
        formColor.addEventListener('input', (e) => {
            if (formColorPreview) formColorPreview.textContent = e.target.value.toUpperCase();
        });
    }

    function openModal(isEdit = false, subject = null) {
        if (!modalOverlay) return;
        hideAlert();
        if (modalError) modalError.style.display = 'none';

        if (isEdit && subject) {
            modalTitle.textContent = 'Edit Subject';
            modalSubmitLabel.textContent = 'Update Subject';
            formId.value = subject.id;
            formName.value = subject.name || '';
            formExamDate.value = subject.exam_date || '';
            formDifficulty.value = subject.difficulty_level || 3;
            formColor.value = subject.color_code || '#4F46E5';
            if (formColorPreview) formColorPreview.textContent = (subject.color_code || '#4F46E5').toUpperCase();
        } else {
            modalTitle.textContent = 'Add New Subject';
            modalSubmitLabel.textContent = 'Save Subject';
            formId.value = '';
            modalForm.reset();
            formDifficulty.value = '3';
            formColor.value = '#4F46E5';
            if (formColorPreview) formColorPreview.textContent = '#4F46E5';
        }

        modalOverlay.removeAttribute('hidden');
        formName.focus();
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

    function getDaysBadge(days) {
        const d = Number(days);
        if (!Number.isFinite(d)) return '<span class="list-item__badge">—</span>';
        if (d === 0) {
            return '<span class="list-item__badge list-item__badge--soon">Today</span>';
        } else if (d === 1) {
            return '<span class="list-item__badge list-item__badge--soon">Tomorrow</span>';
        } else if (d <= 3) {
            return `<span class="list-item__badge list-item__badge--soon">${d} days left</span>`;
        } else if (d <= 14) {
            return `<span class="list-item__badge list-item__badge--upcoming">${d} days left</span>`;
        }
        return `<span class="list-item__badge list-item__badge--far">${d} days left</span>`;
    }

    /* Render Subjects List */
    function renderSubjects(subjects) {
        loadingState.style.display = 'none';
        errorState.style.display = 'none';

        if (!subjects || subjects.length === 0) {
            emptyState.style.display = 'flex';
            tableWrapper.style.display = 'none';
            if (countBadge) countBadge.textContent = '0 subjects';
            return;
        }

        emptyState.style.display = 'none';
        tableWrapper.style.display = 'block';
        if (countBadge) countBadge.textContent = `${subjects.length} subject${subjects.length === 1 ? '' : 's'}`;

        tableBody.innerHTML = subjects.map(sub => {
            const color = escapeHtml(sub.color_code || '#4F46E5');
            const topicCount = sub.topic_count || 0;
            const completedCount = sub.completed_topic_count || 0;
            const progress = sub.progress_percentage || 0;

            return `
                <tr data-subject-id="${sub.id}">
                    <td>
                        <div style="display:flex; align-items:center; gap:12px;">
                            <span style="display:inline-block; width:14px; height:14px; border-radius:50%; background:${color}; flex-shrink:0;"></span>
                            <div>
                                <strong style="color:var(--color-text); font-size:0.95rem;">${escapeHtml(sub.name)}</strong>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span style="color:var(--color-text-secondary); font-variant-numeric:tabular-nums;">${escapeHtml(sub.exam_date || '—')}</span>
                    </td>
                    <td>
                        ${getDaysBadge(sub.days_until_exam)}
                    </td>
                    <td>
                        <span style="font-size:0.85rem; color:var(--color-text-secondary);">${getDifficultyBadge(sub.difficulty_level)}</span>
                    </td>
                    <td>
                        <span style="font-size:0.85rem; color:var(--color-text-secondary);">${completedCount}/${topicCount} done (${progress}%)</span>
                    </td>
                    <td style="text-align: right;">
                        <div style="display:inline-flex; gap:8px;">
                            <button type="button" class="btn btn--secondary btn--sm btn-edit-subject" data-id="${sub.id}" title="Edit Subject">
                                ✏️ Edit
                            </button>
                            <button type="button" class="btn btn--danger btn--sm btn-delete-subject" data-id="${sub.id}" data-name="${escapeHtml(sub.name)}" title="Delete Subject">
                                🗑️ Delete
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        // Attach action handlers
        tableBody.querySelectorAll('.btn-edit-subject').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = Number(e.currentTarget.dataset.id);
                const sub = subjectsCache.find(s => s.id === id);
                if (sub) openModal(true, sub);
            });
        });

        tableBody.querySelectorAll('.btn-delete-subject').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = Number(e.currentTarget.dataset.id);
                const name = e.currentTarget.dataset.name;
                if (confirm(`Are you sure you want to delete "${name}"? This will also remove all topics associated with it.`)) {
                    await deleteSubject(id);
                }
            });
        });
    }

    /* API Operations */
    async function fetchSubjects() {
        loadingState.style.display = 'flex';
        emptyState.style.display = 'none';
        errorState.style.display = 'none';
        tableWrapper.style.display = 'none';

        try {
            const res = await fetch('/api/subjects');
            const data = await res.json();
            if (res.ok && data.success) {
                subjectsCache = data.data || [];
                renderSubjects(subjectsCache);
            } else {
                throw new Error(data.error || 'Failed to load subjects.');
            }
        } catch (err) {
            loadingState.style.display = 'none';
            errorState.style.display = 'flex';
            if (errorText) errorText.textContent = err.message || 'Network error fetching subjects.';
        }
    }

    if (btnRetry) {
        btnRetry.addEventListener('click', fetchSubjects);
    }

    /* Create or Update Subject */
    modalForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert();
        if (modalError) modalError.style.display = 'none';

        const id = formId.value ? Number(formId.value) : null;
        const payload = {
            name: formName.value.trim(),
            exam_date: formExamDate.value,
            difficulty_level: Number(formDifficulty.value),
            color_code: formColor.value.trim()
        };

        modalSubmit.disabled = true;
        const originalLabel = modalSubmitLabel.textContent;
        modalSubmitLabel.textContent = 'Saving...';

        try {
            const endpoint = id ? `/api/subjects/${id}` : '/api/subjects';
            const method = id ? 'PUT' : 'POST';

            const res = await fetch(endpoint, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (res.ok && data.success) {
                closeModal();
                showAlert(id ? 'Subject updated successfully.' : 'Subject created successfully.', false);
                await fetchSubjects();
            } else {
                throw new Error(data.error || 'Failed to save subject.');
            }
        } catch (err) {
            if (modalError) {
                modalError.textContent = err.message || 'An error occurred while saving.';
                modalError.style.display = 'block';
            }
        } finally {
            modalSubmit.disabled = false;
            modalSubmitLabel.textContent = originalLabel;
        }
    });

    /* Delete Subject */
    async function deleteSubject(id) {
        hideAlert();
        try {
            const res = await fetch(`/api/subjects/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (res.ok && data.success) {
                showAlert('Subject deleted successfully.', false);
                await fetchSubjects();
            } else {
                throw new Error(data.error || 'Failed to delete subject.');
            }
        } catch (err) {
            showAlert(err.message || 'Error deleting subject.', true);
        }
    }

    // Initial load
    fetchSubjects();
});
