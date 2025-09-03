/**
 * Calendar Appointment Type Integration
 * 
 * Updates calendar slot click handlers to show appointment type selection modal
 * before proceeding to booking creation.
 */

console.log('🔄 Calendar Appointment Type Integration Script Loaded - Version 20250827d');

// Store original openModal function
let originalOpenModal = null;

/**
 * Initialize unified booking modal integration with calendar
 */
function initializeCalendarAppointmentTypeIntegration() {
    console.log('🔄 Attempting to initialize unified booking modal integration...');
    
    // Wait for both calendar and unified booking modal to be ready
    if (typeof openModal !== 'function') {
        console.log('⏳ Waiting for openModal function...');
        // Retry after a short delay if openModal is not available yet
        setTimeout(initializeCalendarAppointmentTypeIntegration, 100);
        return;
    }

    if (!window.unifiedBookingModal) {
        console.log('⏳ Waiting for unifiedBookingModal...');
        // Retry if unified booking modal is not ready
        setTimeout(initializeCalendarAppointmentTypeIntegration, 100);
        return;
    }

    // Store original function
    originalOpenModal = window.openModal;

    // Override openModal function to use unified modal
    window.openModal = enhancedOpenModalWithUnified;

    console.log('✅ Unified booking modal integration initialized successfully');
}

/**
 * Enhanced openModal that uses the unified booking modal for all appointments
 * 
 * @param {HTMLElement} cell - Calendar cell that was clicked
 * @param {Object} appt - Existing appointment data (null for new appointments)  
 * @param {string} dayOverride - Day override
 */
function enhancedOpenModalWithUnified(cell, appt = null, dayOverride = null) {
    console.log('🎯 Enhanced unified modal called:', { cell, appt, dayOverride });
    
    try {
        // Extract date and time from cell
        const date = getSlotDate(cell, dayOverride);
        const time = cell.dataset.time;
        
        console.log('📅 Calendar integration - slot data:', {
            cellDataDay: cell.dataset.day,
            dayOverride: dayOverride,
            calculatedDate: date,
            time: time,
            cellElement: cell,
            currentStartDate: window.currentStartDate
        });
        
        if (appt) {
            // Editing existing appointment - go to Step 2 with appointment data
            console.log('📝 Editing existing appointment with unified modal');
            window.unifiedBookingModal.openForEditBooking(appt.id, {
                appointmentType: appt.appointmentType,
                patientId: appt.patient_id,
                date: appt.date,
                time: appt.start_time,
                duration: appt.duration,
                notes: appt.notes,
                color: appt.color,
                billingCodes: appt.billing_codes || []
            });
        } else {
            // New appointment - start at Step 1 (appointment type selection)
            console.log('🆕 New appointment with unified modal');
            window.unifiedBookingModal.openForNewBooking(date, time);
        }
        
    } catch (error) {
        // If unified modal fails, fall back to original modal
        console.error('Error with unified modal, falling back to original:', error);
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

    // Wait a moment for the modal to be fully rendered, then pre-fill
    setTimeout(() => {
        fillBookingFormWithAppointmentType(appointmentType, slotData);
    }, 100);
}

/**
 * Fill booking form with appointment type data
 * 
 * @param {Object} appointmentType - Selected appointment type
 * @param {Object} slotData - Slot data
 */
function fillBookingFormWithAppointmentType(appointmentType, slotData) {
    console.log('🔧 Filling booking form with appointment type:', appointmentType.name);
    console.log('📋 Full appointment type data:', appointmentType);
    
    // Verify booking modal is visible
    const bookingModal = document.getElementById('booking-modal');
    if (!bookingModal || bookingModal.style.display === 'none') {
        console.error('❌ Booking modal not found or not visible');
        return;
    }
    
    // Set appointment type ID (add hidden field if needed)
    let appointmentTypeField = document.getElementById('appointment-type-id');
    if (!appointmentTypeField) {
        appointmentTypeField = document.createElement('input');
        appointmentTypeField.type = 'hidden';
        appointmentTypeField.id = 'appointment-type-id';
        appointmentTypeField.name = 'appointment_type_id';
        bookingModal.appendChild(appointmentTypeField);
        console.log('✅ Created appointment type hidden field');
    }
    appointmentTypeField.value = appointmentType.id;
    console.log(`✅ Set appointment type ID to ${appointmentType.id}`);

    // Set appointment type hex color (add hidden field if needed)
    let appointmentTypeColorField = document.getElementById('appointment-type-color');
    if (!appointmentTypeColorField) {
        appointmentTypeColorField = document.createElement('input');
        appointmentTypeColorField.type = 'hidden';
        appointmentTypeColorField.id = 'appointment-type-color';
        appointmentTypeColorField.name = 'appointment_type_color';
        bookingModal.appendChild(appointmentTypeColorField);
        console.log('✅ Created appointment type color hidden field');
    }
    if (appointmentType.color) {
        appointmentTypeColorField.value = appointmentType.color;
        console.log(`✅ Set appointment type hex color to ${appointmentType.color}`);
    }

    // Set duration from appointment type
    const durationField = document.getElementById('booking-duration') || document.getElementById('duration');
    if (durationField) {
        const duration = appointmentType.effective_duration || appointmentType.duration;
        durationField.value = duration;
        console.log(`✅ Set booking duration to ${duration} minutes`);
        
        // Trigger duration change to update end time
        if (typeof updateEndTime === 'function') {
            updateEndTime();
        } else if (typeof window.updateEndTime === 'function') {
            window.updateEndTime();
        }
    } else {
        console.warn('⚠️  Duration field not found');
    }

    // Set color based on appointment type
    const colorField = document.getElementById('booking-colour') || document.getElementById('colour');
    const colorHexDisplay = document.getElementById('booking-colour-hex');
    console.log('🔍 Color field found:', colorField ? colorField.type : 'NOT FOUND');
    console.log('🎨 Appointment type color:', appointmentType.color);
    
    if (colorField && appointmentType.color) {
        console.log(`🎨 Setting appointment type color directly: ${appointmentType.color}`);
        
        // Set hex color directly to color picker
        colorField.value = appointmentType.color;
        console.log(`✅ Set color picker to: ${appointmentType.color}`);
        
        // Update hex display if available
        if (colorHexDisplay) {
            colorHexDisplay.textContent = appointmentType.color.toUpperCase();
            console.log(`✅ Updated hex display to: ${appointmentType.color.toUpperCase()}`);
        }
        
        console.log('🔍 Color field value after setting:', colorField.value);
    } else if (!appointmentType.color) {
        console.warn('⚠️  Appointment type has no color specified');
    } else {
        console.warn('⚠️  Color field not found in booking form');
    }

    // Pre-fill billing codes if available (handle both old single code and new multiple codes)
    if (appointmentType.default_billing_codes || appointmentType.default_billing_code) {
        const billingCodeField = document.getElementById('billing-code');
        if (billingCodeField) {
            let primaryBillingCode = '';
            
            // Handle new multiple billing codes format
            if (appointmentType.default_billing_codes) {
                try {
                    const billingCodes = typeof appointmentType.default_billing_codes === 'string' 
                        ? JSON.parse(appointmentType.default_billing_codes)
                        : appointmentType.default_billing_codes;
                    
                    if (billingCodes && billingCodes.length > 0) {
                        // Use the first billing code as primary for the dropdown
                        primaryBillingCode = billingCodes[0].code;
                        console.log(`✅ Set primary billing code to: ${primaryBillingCode} (from ${billingCodes.length} codes)`);
                    }
                } catch (e) {
                    console.warn('⚠️  Could not parse default_billing_codes:', e);
                }
            } 
            // Handle legacy single billing code format
            else if (appointmentType.default_billing_code) {
                primaryBillingCode = appointmentType.default_billing_code;
                console.log(`✅ Set billing code to: ${primaryBillingCode} (legacy format)`);
            }
            
            if (primaryBillingCode) {
                billingCodeField.value = primaryBillingCode;
                
                // Update billing info display if the function exists
                if (typeof updateBookingBillingInfo === 'function') {
                    updateBookingBillingInfo(primaryBillingCode);
                } else if (typeof window.updateBookingBillingInfo === 'function') {
                    window.updateBookingBillingInfo(primaryBillingCode);
                }
            }
        }
    } else {
        console.log('ℹ️  No default billing codes for appointment type');
    }

    // Pre-fill notes if available
    const notesField = document.getElementById('booking-notes') || document.getElementById('notes');
    if (notesField) {
        if (appointmentType.default_notes && !notesField.value.trim()) {
            notesField.value = appointmentType.default_notes;
            console.log(`✅ Set booking notes: ${appointmentType.default_notes}`);
        } else if (!appointmentType.default_notes) {
            console.log('ℹ️  No default notes for appointment type');
        }
    } else {
        console.warn('⚠️  Notes field not found');
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
            ${getBillingCodesDisplay(appointmentType)}
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
    
    console.log('🗓️ getSlotDate calculation:', {
        requestedDay: day,
        currentStartDate: currentDate,
        daysArray: days,
        dayOverride: dayOverride,
        cellDataDay: cell.dataset.day
    });
    
    const dayIndex = days.findIndex(d => d === day);
    console.log('📅 Day index calculation:', {
        dayRequested: day,
        dayIndex: dayIndex,
        daysArray: days
    });
    
    if (dayIndex === -1) {
        console.warn('⚠️ Day not found, returning today:', day);
        return new Date().toISOString().split('T')[0];
    }

    // FIX: Calculate what day of the week currentDate actually is
    const currentDayOfWeek = currentDate.getDay(); // 0=Sunday, 1=Monday, etc.
    const currentDayIndex = currentDayOfWeek === 0 ? 6 : currentDayOfWeek - 1; // Convert to our Mon=0 system
    
    // Calculate the difference between requested day and current day
    const dayOffset = dayIndex - currentDayIndex;
    
    const slotDate = new Date(currentDate.getTime() + (dayOffset * 24 * 60 * 60 * 1000));
    
    console.log('📅 FIXED date calculation:', {
        baseDate: currentDate,
        baseDayOfWeek: currentDate.toLocaleDateString('en-US', { weekday: 'short' }),
        currentDayIndex: currentDayIndex,
        requestedDayIndex: dayIndex,
        dayOffset: dayOffset,
        calculatedDate: slotDate,
        finalDateString: slotDate.toISOString().split('T')[0],
        calculatedDayName: slotDate.toLocaleDateString('en-US', { weekday: 'long' })
    });
    
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
 * Get the calendar color that will be displayed for a dropdown value
 * 
 * @param {string} dropdownValue - The dropdown value (e.g., 'red', 'green') 
 * @returns {string} - The hex color that will be displayed in calendar
 */
function getCalendarColorForDropdown(dropdownValue) {
    // This should match the colourMap in week-calendar.html
    const calendarColourMap = {
        red: "#EF4444",       // Equipment/Emergency red (matches appointment types)
        orange: "#EA580C",    // Admin orange (matches appointment types)
        yellow: "#F59E0B",    // Documentation yellow (matches appointment types)
        green: "#2D6356",     // Patient green (matches appointment types)
        blue: "#1E40AF",      // Meeting blue (matches appointment types)
        purple: "#7C3AED",    // Travel purple (matches appointment types)
        grey: "#6B7280"       // Neutral grey
    };
    
    return calendarColourMap[dropdownValue] || "#2D6356"; // Default to green
}

/**
 * Map hex color to dropdown value
 * 
 * @param {string} hexColor - Hex color code
 * @returns {string|null} - Dropdown value or null if no match
 */
function mapHexColorToDropdownValue(hexColor) {
    const colorMapping = {
        // Exact matches for calendar colourMap
        '#EF4444': 'red',     // Equipment/Emergency red 
        '#EA580C': 'orange',  // Admin orange
        '#F59E0B': 'yellow',  // Documentation yellow
        '#2D6356': 'green',   // Patient green
        '#1E40AF': 'blue',    // Meeting blue
        '#7C3AED': 'purple',  // Travel purple
        '#6B7280': 'grey',    // Neutral grey
        
        // Additional appointment type colors mapped to closest dropdown option
        '#16A34A': 'green',   // New Assessment (closer to green)
        '#8B5CF6': 'purple',  // Consultation (close to purple)
        '#3B82F6': 'blue',    // Family Meeting (close to blue)
        '#0891B2': 'blue',    // Group Therapy (close to blue)
        '#0D9488': 'green',   // Neurological (teal/cyan, closest to green)
        '#A855F7': 'purple',  // Home Visit (close to purple)
        '#6366F1': 'blue',    // Academic (close to blue)
        '#2563EB': 'blue',    // MDT Meeting (close to blue)
        
        // Fallback basic colors
        '#ff0000': 'red',
        '#ffa500': 'orange', 
        '#ffff00': 'yellow',
        '#008000': 'green',
        '#0000ff': 'blue',
        '#800080': 'purple',
        '#808080': 'grey'
    };

    const normalizedColor = hexColor.toLowerCase();
    const mappedColor = colorMapping[normalizedColor];
    
    if (mappedColor) {
        console.log(`🎯 Color mapping: ${hexColor} → '${mappedColor}' → ${getCalendarColorForDropdown(mappedColor)}`);
        return mappedColor;
    } else {
        console.warn(`⚠️  No mapping found for color ${hexColor}, defaulting to 'green'`);
        return 'green'; // Default to green if no match
    }
}

/**
 * Get billing codes display for appointment type info
 * 
 * @param {Object} appointmentType - Appointment type object
 * @returns {string} - HTML string for billing codes display
 */
function getBillingCodesDisplay(appointmentType) {
    let billingCodesHtml = '';
    
    // Handle new multiple billing codes format
    if (appointmentType.default_billing_codes) {
        try {
            const billingCodes = typeof appointmentType.default_billing_codes === 'string' 
                ? JSON.parse(appointmentType.default_billing_codes)
                : appointmentType.default_billing_codes;
            
            if (billingCodes && billingCodes.length > 0) {
                const codesText = billingCodes.map(code => {
                    let display = code.code;
                    if (code.quantity && code.quantity > 1) display += ` (x${code.quantity})`;
                    if (code.modifier) display += ` +${code.modifier}`;
                    return display;
                }).join(', ');
                
                billingCodesHtml = `<div class="appointment-type-billing-code">Billing: ${escapeHtml(codesText)}</div>`;
            }
        } catch (e) {
            console.warn('⚠️  Could not parse billing codes for display:', e);
        }
    } 
    // Handle legacy single billing code format
    else if (appointmentType.default_billing_code) {
        billingCodesHtml = `<div class="appointment-type-billing-code">Billing: ${escapeHtml(appointmentType.default_billing_code)}</div>`;
    }
    
    return billingCodesHtml;
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