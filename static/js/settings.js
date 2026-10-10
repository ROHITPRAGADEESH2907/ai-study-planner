/* ============================================================
   AI Study Planner — Settings Page Controller
   Connects to GET and PUT /api/settings.
   ============================================================ */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
    const settingsCard = document.getElementById('settings-card');
    if (!settingsCard) return;

    /* DOM elements */
    const loadingState = document.getElementById('settings-loading');
    const errorState = document.getElementById('settings-error');
    const errorText = document.getElementById('settings-error-text');
    const btnRetry = document.getElementById('btn-retry-settings');

    const alertBox = document.getElementById('settings-alert');
    const alertText = document.getElementById('settings-alert-text');
    const alertClose = document.getElementById('settings-alert-close');

    const form = document.getElementById('settings-form');
    const weekdayInput = document.getElementById('setting-weekday-hours');
    const weekendInput = document.getElementById('setting-weekend-hours');
    const bufferInput = document.getElementById('setting-buffer-days');
    const updatedBadge = document.getElementById('settings-updated-badge');

    const btnSave = document.getElementById('btn-save-settings');
    const btnSaveLabel = document.getElementById('btn-save-label');
    const btnReset = document.getElementById('btn-reset-settings');

    let currentSettings = null;

    /* Helpers */
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

    function populateForm(settings) {
        if (!settings) return;
        weekdayInput.value = settings.weekday_hours !== undefined ? settings.weekday_hours : 3.0;
        weekendInput.value = settings.weekend_hours !== undefined ? settings.weekend_hours : 6.0;
        bufferInput.value = settings.exam_buffer_days !== undefined ? settings.exam_buffer_days : 2;

        if (updatedBadge) {
            if (settings.updated_at) {
                const d = new Date(settings.updated_at);
                updatedBadge.textContent = Number.isNaN(d.getTime())
                    ? 'Configured'
                    : `Saved ${d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}`;
            } else {
                updatedBadge.textContent = 'Default';
            }
        }
    }

    /* API Operations */
    async function loadSettings() {
        loadingState.style.display = 'flex';
        errorState.style.display = 'none';
        settingsCard.style.display = 'none';
        hideAlert();

        try {
            const res = await fetch('/api/settings');
            const data = await res.json();

            if (res.ok && data.success && data.data) {
                currentSettings = data.data;
                populateForm(currentSettings);
                loadingState.style.display = 'none';
                settingsCard.style.display = 'block';
            } else {
                throw new Error(data.error || 'Failed to retrieve user settings.');
            }
        } catch (err) {
            loadingState.style.display = 'none';
            errorState.style.display = 'flex';
            if (errorText) errorText.textContent = err.message || 'Error fetching user settings.';
        }
    }

    if (btnRetry) {
        btnRetry.addEventListener('click', loadSettings);
    }

    if (btnReset) {
        btnReset.addEventListener('click', () => {
            hideAlert();
            if (currentSettings) {
                populateForm(currentSettings);
            }
        });
    }

    /* Save Settings */
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert();

        const weekdayHours = parseFloat(weekdayInput.value);
        const weekendHours = parseFloat(weekendInput.value);
        const bufferDays = parseInt(bufferInput.value, 10);

        // Client-side validations matching backend constraints
        if (Number.isNaN(weekdayHours) || weekdayHours < 0.5 || weekdayHours > 24.0) {
            showAlert('Weekday study hours must be a number between 0.5 and 24.0.', true);
            weekdayInput.focus();
            return;
        }

        if (Number.isNaN(weekendHours) || weekendHours < 0.5 || weekendHours > 24.0) {
            showAlert('Weekend study hours must be a number between 0.5 and 24.0.', true);
            weekendInput.focus();
            return;
        }

        if (Number.isNaN(bufferDays) || bufferDays < 0 || bufferDays > 30) {
            showAlert('Exam buffer days must be an integer between 0 and 30.', true);
            bufferInput.focus();
            return;
        }

        const payload = {
            weekday_hours: weekdayHours,
            weekend_hours: weekendHours,
            exam_buffer_days: bufferDays
        };

        btnSave.disabled = true;
        const originalLabel = btnSaveLabel.textContent;
        btnSaveLabel.textContent = 'Saving...';

        try {
            const res = await fetch('/api/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (res.ok && data.success && data.data) {
                currentSettings = data.data;
                populateForm(currentSettings);
                showAlert(data.message || 'Settings updated successfully.', false);
            } else {
                throw new Error(data.error || 'Failed to update settings.');
            }
        } catch (err) {
            showAlert(err.message || 'Error saving settings.', true);
        } finally {
            btnSave.disabled = false;
            btnSaveLabel.textContent = originalLabel;
        }
    });

    // Initial Load
    loadSettings();
});
