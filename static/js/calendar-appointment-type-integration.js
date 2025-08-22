/**
 * Calendar Appointment Type Integration
 * 
 * Updates calendar slot click handlers to show appointment type selection modal
 * before proceeding to booking creation.
 */

// Store original openModal function
let originalOpenModal = null;

/**
 * Initialize appointment type modal integration with calendar
 */
function initializeCalendarAppointmentTypeIntegration() {
    console.log('🔄 Attempting to initialize calendar appointment type integration...');
    
    // Wait for both calendar and appointment type modal to be ready
    if (typeof openModal !== 'function') {
        console.log('⏳ Waiting for openModal function...');
        // Retry after a short delay if openModal is not available yet
        setTimeout(initializeCalendarAppointmentTypeIntegration, 100);
        return;
    }

    if (!window.appointmentTypeModal) {
        console.log('⏳ Waiting for appointmentTypeModal...');
        // Retry if appointment type modal is not ready
        setTimeout(initializeCalendarAppointmentTypeIntegration, 100);
        return;
    }

    // Store original function
    originalOpenModal = window.openModal;

    // Override openModal function
    window.openModal = enhancedOpenModal;

    console.log('✅ Calendar appointment type integration initialized successfully');
}

/**
 * Enhanced openModal that shows appointment type selection first for new appointments
 * 
 * @param {HTMLElement} cell - Calendar cell that was clicked
 * @param {Object} appt - Existing appointment data (null for new appointments)  
 * @param {string} dayOverride - Day override
 */
function enhancedOpenModal(cell, appt = null, dayOverride = null) {
    console.log('🎯 Enhanced modal called:', { cell, appt, dayOverride });
    
    // If editing existing appointment, go directly to booking modal
    if (appt) {
        console.log('📝 Editing existing appointment, using original modal');
        originalOpenModal(cell, appt, dayOverride);
        return;
    }

    console.log('🆕 New appointment, showing appointment type selection');
    
    // For new appointments, try to show appointment type selection modal first
    try {
        const slotData = {
            cell: cell,
            date: getSlotDate(cell, dayOverride),
            time: cell.dataset.time,
            day: cell.dataset.day || dayOverride,
            duration: getDefaultSlotDuration()
        };

        // Get practice ID (you may need to adjust this based on your implementation)
        const practiceId = getCurrentPracticeId();

        // Show appointment type modal with fallback
        window.appointmentTypeModal.open({
            practiceId: practiceId,
            slotData: slotData,
            onSelection: (data) => {
                // When appointment type is selected, proceed to booking modal with pre-filled data
                proceedToBookingWithAppointmentType(data);
            },
            onCancel: () => {
                // User cancelled appointment type selection
                console.log('Appointment type selection cancelled');
            },
            onError: () => {
                // If appointment type modal fails, fall back to original modal
                console.log('Appointment type modal failed, falling back to original booking modal');
                originalOpenModal(cell, appt, dayOverride);
            }
        });
    } catch (error) {
        // If anything goes wrong, fall back to original modal
        console.error('Error in enhanced modal, falling back to original:', error);
        originalOpenModal(cell, appt, dayOverride);
    }
}

/**
 * Proceed to booking modal with selected appointment type
 * 
 * @param {Object} data - Selection data from appointment type modal
 */
function proceedToBookingWithAppointmentType(data) {
    const { appointmentType, slotData } = data;
    const { cell, dayOverride } = slotData;

    // Call original openModal to show booking form
    originalOpenModal(cell, null, dayOverride);

    // Pre-fill appointment type data in booking form
    fillBookingFormWithAppointmentType(appointmentType, slotData);
}

/**
 * Fill booking form with appointment type data
 * 
 * @param {Object} appointmentType - Selected appointment type
 * @param {Object} slotData - Slot data
 */
function fillBookingFormWithAppointmentType(appointmentType, slotData) {
    // Set appointment type ID (add hidden field if needed)
    let appointmentTypeField = document.getElementById('appointment-type-id');
    if (!appointmentTypeField) {
        appointmentTypeField = document.createElement('input');
        appointmentTypeField.type = 'hidden';
        appointmentTypeField.id = 'appointment-type-id';
        appointmentTypeField.name = 'appointment_type_id';
        document.getElementById('booking-form') ? 
            document.getElementById('booking-form').appendChild(appointmentTypeField) :
            document.querySelector('#booking-modal form').appendChild(appointmentTypeField);
    }
    appointmentTypeField.value = appointmentType.id;

    // Set duration from appointment type
    const durationField = document.getElementById('booking-duration') || document.getElementById('duration');
    if (durationField) {
        durationField.value = appointmentType.effective_duration || appointmentType.duration;
        
        // Trigger duration change to update end time
        if (typeof updateEndTime === 'function') {
            updateEndTime();
        }
    }

    // Set color based on appointment type
    const colorField = document.getElementById('booking-colour') || document.getElementById('colour');
    if (colorField && appointmentType.color) {
        // Map hex color to dropdown value if needed
        const colorValue = mapHexColorToDropdownValue(appointmentType.color);
        if (colorValue) {
            colorField.value = colorValue;
        }
    }

    // Pre-fill billing code if available
    if (appointmentType.default_billing_code) {
        const billingCodeField = document.getElementById('billing-code');
        if (billingCodeField) {
            billingCodeField.value = appointmentType.default_billing_code;
        }
    }

    // Pre-fill notes if available
    if (appointmentType.default_notes) {
        const notesField = document.getElementById('booking-notes') || document.getElementById('notes');
        if (notesField && !notesField.value.trim()) {
            notesField.value = appointmentType.default_notes;
        }
    }

    // Add appointment type info display
    displayAppointmentTypeInfo(appointmentType);
}

/**
 * Display appointment type information in the booking modal
 * 
 * @param {Object} appointmentType - Selected appointment type
 */
function displayAppointmentTypeInfo(appointmentType) {
    // Check if appointment type info display already exists
    let infoDisplay = document.getElementById('appointment-type-info');
    
    if (!infoDisplay) {
        infoDisplay = document.createElement('div');
        infoDisplay.id = 'appointment-type-info';
        infoDisplay.className = 'appointment-type-info';
        
        // Insert at the top of the modal form
        const modal = document.getElementById('booking-modal');
        const form = modal.querySelector('form') || modal;
        const firstLabel = form.querySelector('label');
        
        if (firstLabel) {
            form.insertBefore(infoDisplay, firstLabel);
        } else {
            form.insertBefore(infoDisplay, form.firstChild);
        }
    }

    infoDisplay.innerHTML = `
        <div class="selected-appointment-type">
            <div class="appointment-type-header">
                <span class="appointment-type-indicator" style="background-color: ${appointmentType.color}"></span>
                <strong>${escapeHtml(appointmentType.name)}</strong>
                <span class="appointment-type-duration">${appointmentType.effective_duration || appointmentType.duration}min</span>
            </div>
            ${appointmentType.default_billing_code ? `<div class="appointment-type-billing-code">Billing: ${escapeHtml(appointmentType.default_billing_code)}</div>` : ''}
            <button type="button" class="change-appointment-type-btn" onclick="changeAppointmentType()">
                Change Type
            </button>
        </div>
    `;
}

/**
 * Allow user to change appointment type from booking modal
 */
function changeAppointmentType() {
    const modal = document.getElementById('booking-modal');
    const slotData = {
        cell: window.selectedCell,
        date: document.getElementById('booking-date').value,
        time: document.getElementById('start-time').value,
        day: window.selectedDayOverride || window.selectedCell?.dataset?.day
    };

    const practiceId = getCurrentPracticeId();

    // Close current booking modal temporarily  
    modal.style.display = 'none';

    // Show appointment type modal again
    window.appointmentTypeModal.open({
        practiceId: practiceId,
        slotData: slotData,
        onSelection: (data) => {
            // Re-show booking modal and update with new appointment type
            modal.style.display = 'block';
            fillBookingFormWithAppointmentType(data.appointmentType, data.slotData);
        },
        onCancel: () => {
            // User cancelled, re-show booking modal with current selection
            modal.style.display = 'block';
        }
    });
}

// Make changeAppointmentType globally available
window.changeAppointmentType = changeAppointmentType;

/**
 * Get slot date from cell and day override
 * 
 * @param {HTMLElement} cell - Calendar cell
 * @param {string} dayOverride - Day override
 * @returns {string} - Date in YYYY-MM-DD format
 */
function getSlotDate(cell, dayOverride) {
    const day = cell.dataset.day || dayOverride;
    const currentDate = window.currentStartDate || new Date();
    const days = window.days || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    
    const dayIndex = days.findIndex(d => d === day);
    if (dayIndex === -1) return new Date().toISOString().split('T')[0];

    const slotDate = new Date(currentDate.getTime() + (dayIndex * 24 * 60 * 60 * 1000));
    return slotDate.toISOString().split('T')[0];
}

/**
 * Get default slot duration
 * 
 * @returns {number} - Default duration in minutes
 */
function getDefaultSlotDuration() {
    return window.slotDuration || 30;
}

/**
 * Get current practice ID
 * This may need to be adjusted based on your session/auth implementation
 * 
 * @returns {number} - Practice ID
 */
function getCurrentPracticeId() {
    // You may need to implement this based on your session management
    // For now, default to practice ID 1
    return 1;
}

/**
 * Map hex color to dropdown value
 * 
 * @param {string} hexColor - Hex color code
 * @returns {string|null} - Dropdown value or null if no match
 */
function mapHexColorToDropdownValue(hexColor) {
    const colorMapping = {
        '#ff0000': 'red',
        '#ffa500': 'orange', 
        '#ffff00': 'yellow',
        '#008000': 'green',
        '#0000ff': 'blue',
        '#800080': 'purple',
        '#808080': 'grey',
        '#2D6356': 'green', // Default theme color maps to green
        '#EA580C': 'orange', // Admin color
        '#1E40AF': 'blue', // Meeting color
        '#7C3AED': 'purple' // Travel color
    };

    return colorMapping[hexColor.toLowerCase()] || null;
}

/**
 * Escape HTML for safe display
 * 
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for other scripts to load
    setTimeout(initializeCalendarAppointmentTypeIntegration, 250);
});

// Also try to initialize if called after DOM is already loaded
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initializeCalendarAppointmentTypeIntegration, 250);
}