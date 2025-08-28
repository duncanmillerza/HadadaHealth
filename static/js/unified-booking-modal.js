/**
 * UNIFIED BOOKING MODAL JAVASCRIPT
 * Handles the two-step booking process: Appointment Type Selection + Booking Details
 * Follows the specification in APPOINTMENT_BOOKING_MODAL_MIGRATION_SPEC.md
 */

class UnifiedBookingModal {
    constructor() {
        this.currentStep = 1;
        this.selectedAppointmentType = null;
        this.editingAppointmentId = null;
        this.userContext = null;
        this.billingCodes = [];
        this.billingModifiers = [];
        this.allBillingCodes = [];
        this.patients = [];
        this.therapists = [];
        
        // Initialize modal when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * Initialize the modal and set up event listeners
     */
    init() {
        try {
            console.log('🔄 Starting unified booking modal initialization...');
            
            // Check if required elements exist
            const modal = document.getElementById('unified-booking-modal');
            if (!modal) {
                console.error('❌ Unified booking modal element not found in DOM');
                return;
            }
            
            this.bindEventListeners();
            this.loadInitialData();
            console.log('✅ Unified Booking Modal initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing unified booking modal:', error);
        }
    }

    /**
     * Bind all event listeners for the modal
     */
    bindEventListeners() {
        // Modal controls
        const modal = document.getElementById('unified-booking-modal');
        const backdrop = document.getElementById('unified-booking-modal-backdrop');
        const closeButton = document.getElementById('close-unified-modal');
        const cancelButton = document.getElementById('unified-cancel-button');

        // Step navigation buttons
        const continueButton = document.getElementById('unified-continue-to-step2-button');
        const backButton = document.getElementById('unified-back-to-step1-button');
        const saveButton = document.getElementById('unified-save-booking-button');
        const changeTypeButton = document.querySelector('.change-type-btn');

        // Close modal events
        if (closeButton) closeButton.addEventListener('click', () => this.closeModal());
        if (cancelButton) cancelButton.addEventListener('click', () => this.closeModal());
        if (backdrop) backdrop.addEventListener('click', () => this.closeModal());

        // Step navigation
        if (continueButton) continueButton.addEventListener('click', () => this.goToStep2());
        if (backButton) backButton.addEventListener('click', () => this.goToStep1());
        if (saveButton) saveButton.addEventListener('click', () => this.saveBooking());
        if (changeTypeButton) changeTypeButton.addEventListener('click', () => this.goToStep1());

        // Form field events
        this.bindFormEvents();
        
        // Billing table events
        this.bindBillingTableEvents();
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        console.log('✅ Event listeners bound');
    }

    /**
     * Bind form field events
     */
    bindFormEvents() {
        // Duration change updates end time
        const durationInput = document.getElementById('unified-booking-duration');
        const startTimeInput = document.getElementById('unified-start-time');
        
        if (durationInput) {
            durationInput.addEventListener('input', () => this.updateEndTime());
        }
        
        if (startTimeInput) {
            startTimeInput.addEventListener('input', () => this.updateEndTime());
        }

        // Color picker updates hex display
        const colorPicker = document.getElementById('unified-booking-colour-picker');
        const colorHex = document.getElementById('unified-booking-colour-hex');
        
        if (colorPicker && colorHex) {
            colorPicker.addEventListener('input', (e) => {
                colorHex.textContent = e.target.value;
                document.getElementById('unified-booking-colour').value = e.target.value;
            });
        }

        // Profession change filters therapists
        const professionSelect = document.getElementById('unified-therapist-profession');
        if (professionSelect) {
            professionSelect.addEventListener('change', () => this.filterTherapistByProfession());
        }

        // Patient dropdown change updates selectedPatient
        const patientSelect = document.getElementById('unified-patient-name');
        if (patientSelect) {
            patientSelect.addEventListener('change', () => this.onPatientDropdownChange());
        }
    }

    /**
     * Bind billing table events
     */
    bindBillingTableEvents() {
        // Add billing code button
        const addButton = document.querySelector('.add-billing-row-btn');
        if (addButton) {
            addButton.addEventListener('click', () => this.addBillingCodeRow());
        }
        
        console.log('💳 Billing table events bound');
    }

    /**
     * Load initial data needed for the modal
     */
    async loadInitialData() {
        try {
            // Load therapists first (needed for user context)
            await this.loadTherapistsData();
            
            // Load user context (depends on therapists data)
            await this.loadUserContext();
            
            // Load other data
            await this.loadBillingModifiers();
            await this.loadBillingCodes();
            await this.loadPatientsData();
            
            console.log('✅ Initial data loaded');
        } catch (error) {
            console.error('❌ Error loading initial data:', error);
        }
    }

    /**
     * Load current user context for auto-population
     */
    async loadUserContext() {
        try {
            const response = await fetch('/session-info');
            if (response.ok) {
                const sessionData = await response.json();
                
                // Find the user's therapist record to get profession
                const userTherapist = this.therapists?.find(t => t.id === sessionData.linked_therapist_id);
                
                this.userContext = {
                    id: sessionData.linked_therapist_id,
                    name: sessionData.username || "Current User",
                    profession: userTherapist?.profession || "Physiotherapy",
                    isAdmin: sessionData.role === "Admin",
                    role: sessionData.role
                };
                
                console.log('✅ User context loaded:', this.userContext);
            } else {
                // Fallback user context
                this.userContext = {
                    id: 1,
                    name: "Current User",
                    profession: "Physiotherapy",
                    isAdmin: false,
                    role: "Therapist"
                };
                console.log('⚠️ Using fallback user context');
            }
        } catch (error) {
            console.error('❌ Error loading user context:', error);
            // Fallback user context
            this.userContext = {
                id: 1,
                name: "Current User", 
                profession: "Physiotherapy",
                isAdmin: false,
                role: "Therapist"
            };
        }
    }

    /**
     * Load billing modifiers from database
     */
    async loadBillingModifiers() {
        try {
            // Load billing modifiers from the existing API endpoint
            const profession = this.userContext?.profession || 'Physiotherapy';
            
            try {
                const response = await fetch(`/api/billing_modifiers?profession=${profession}`);
                if (response.ok) {
                    this.billingModifiers = await response.json();
                    console.log('✅ Billing modifiers loaded from API:', this.billingModifiers.length);
                    return;
                }
            } catch (apiError) {
                console.log('⚠️ API endpoint error, using fallback data:', apiError);
            }

            // Fallback: Load all modifiers with correct multipliers from the database
            this.billingModifiers = [
                { modifier_code: "", modifier_name: "No Modifier", modifier_multiplier: 1 },
                { modifier_code: "0001", modifier_name: "Late Cancellation Fee", modifier_multiplier: 1, profession: "Physiotherapy" },
                { modifier_code: "0003", modifier_name: "External Equipment Use Discount", modifier_multiplier: 0.85, profession: "Physiotherapy" },
                { modifier_code: "0008", modifier_name: "Additional Procedure Discount", modifier_multiplier: 0.5, profession: "Physiotherapy" },
                { modifier_code: "0009", modifier_name: "Full Fee for Separate Conditions", modifier_multiplier: 1.0, profession: "Physiotherapy" },
                { modifier_code: "0010", modifier_name: "Overlapping Condition Discount", modifier_multiplier: 0.5, profession: "Physiotherapy" },
                { modifier_code: "0013", modifier_name: "Travel Fee (AA Rates)", modifier_multiplier: 1.0, profession: "Physiotherapy" },
                { modifier_code: "0014", modifier_name: "In-Facility Treatment Indicator", modifier_multiplier: 1.0, profession: "Physiotherapy" },
                { modifier_code: "0006", modifier_name: "Emergency Treatment Surcharge", modifier_multiplier: 1.5, profession: "Occupational Therapy" },
                { modifier_code: "0008", modifier_name: "Assistive Device at Cost", modifier_multiplier: 1.0, profession: "Occupational Therapy" },
                { modifier_code: "0009", modifier_name: "Orthoses/Pressure Garment Materials", modifier_multiplier: 1.0, profession: "Occupational Therapy" }
            ];
            
            console.log('✅ Billing modifiers loaded (hardcoded with real data):', this.billingModifiers.length);
        } catch (error) {
            console.error('❌ Error loading billing modifiers:', error);
            this.billingModifiers = [
                { modifier_code: "", modifier_name: "No Modifier", modifier_multiplier: 1 }
            ];
        }
    }

    /**
     * Load available billing codes
     */
    async loadBillingCodes() {
        try {
            const response = await fetch('/api/billing-codes');
            if (response.ok) {
                this.allBillingCodes = await response.json();
                console.log('✅ Billing codes loaded:', this.allBillingCodes.length);
            } else {
                // Fallback billing codes
                this.allBillingCodes = [
                    { code: "72501", description: "Rehabilitation requiring undivided attention", rate: 336.40 },
                    { code: "72502", description: "Group rehabilitation", rate: 199.10 },
                    { code: "72503", description: "Rehabilitation for Central Nervous System", rate: 420.50 }
                ];
                console.log('⚠️ Using fallback billing codes');
            }
        } catch (error) {
            console.error('❌ Error loading billing codes:', error);
            this.allBillingCodes = [];
        }
    }

    /**
     * Load patients data for dropdown
     */
    async loadPatientsData() {
        try {
            const response = await fetch('/patients');
            if (response.ok) {
                this.patients = await response.json();
                this.populatePatientDropdown();
                console.log('✅ Patients loaded:', this.patients.length);
            } else {
                console.error('❌ Failed to load patients');
                this.patients = [];
            }
        } catch (error) {
            console.error('❌ Error loading patients:', error);
            this.patients = [];
        }
    }

    /**
     * Load therapists and professions data
     */
    async loadTherapistsData() {
        try {
            const response = await fetch('/therapists');
            if (response.ok) {
                this.therapists = await response.json();
                this.populateProfessionDropdown();
                this.populateTherapistDropdown();
                console.log('✅ Therapists loaded:', this.therapists.length);
            } else {
                console.error('❌ Failed to load therapists');
                this.therapists = [];
            }
        } catch (error) {
            console.error('❌ Error loading therapists:', error);
            this.therapists = [];
        }
    }

    /**
     * Populate patient dropdown
     */
    populatePatientDropdown() {
        const patientSelect = document.getElementById('unified-patient-name');
        if (!patientSelect || !this.patients) return;

        patientSelect.innerHTML = '<option value="">Select a patient...</option>';
        
        this.patients.forEach(patient => {
            const option = document.createElement('option');
            option.value = patient.id;
            option.textContent = patient.preferred_name && patient.preferred_name.trim() !== ""
                ? `${patient.preferred_name} (${patient.first_name} ${patient.surname})`
                : `${patient.first_name} ${patient.surname}`;
            patientSelect.appendChild(option);
        });
    }

    /**
     * Populate profession dropdown
     */
    populateProfessionDropdown() {
        const professionSelect = document.getElementById('unified-therapist-profession');
        if (!professionSelect || !this.therapists) return;

        // Get unique professions
        const professions = [...new Set(this.therapists.map(t => t.profession).filter(Boolean))];
        
        professionSelect.innerHTML = '<option value="">Select profession...</option>';
        professions.forEach(profession => {
            const option = document.createElement('option');
            option.value = profession;
            option.textContent = profession;
            professionSelect.appendChild(option);
        });
    }

    /**
     * Populate therapist dropdown (initially all therapists)
     */
    populateTherapistDropdown() {
        const therapistSelect = document.getElementById('unified-therapist-name');
        if (!therapistSelect || !this.therapists) return;

        therapistSelect.innerHTML = '<option value="">Select therapist...</option>';
        this.therapists.forEach(therapist => {
            const option = document.createElement('option');
            option.value = therapist.id;
            option.textContent = therapist.preferred_name || `${therapist.name} ${therapist.surname}`;
            therapistSelect.appendChild(option);
        });
    }

    /**
     * Open the modal for new booking
     */
    openForNewBooking(date = null, time = null) {
        console.log('📅 Opening modal for new booking with date:', date, 'time:', time);
        
        this.isEditing = false;
        this.editingAppointmentId = null;
        this.selectedAppointmentType = null;
        this.currentStep = 1;
        
        // Pre-populate date/time if provided
        if (date) {
            const dateInput = document.getElementById('unified-booking-date');
            if (dateInput) {
                const beforeValue = dateInput.value;
                dateInput.value = date;
                console.log('📅 Date input update:', {
                    providedDate: date,
                    providedDayOfWeek: new Date(date).toLocaleDateString('en-US', { weekday: 'long' }),
                    beforeValue: beforeValue,
                    afterValue: dateInput.value,
                    successfully_set: dateInput.value === date
                });
            } else {
                console.error('❌ Could not find unified-booking-date input field!');
            }
        } else {
            console.log('⚠️ No date provided to openForNewBooking');
            const dateInput = document.getElementById('unified-booking-date');
            if (dateInput) {
                console.log('📅 Date field current value (no date provided):', dateInput.value);
            }
        }
        
        if (time) {
            const timeInput = document.getElementById('unified-start-time');
            if (timeInput) {
                timeInput.value = time;
                console.log('⏰ Set time input to:', time);
            }
        }
        
        this.showModal();
        this.updateStepDisplay();
        this.loadAppointmentTypes();
        
        console.log('📅 Modal opened for new booking');
    }

    /**
     * Open the modal for editing existing appointment
     */
    openForEditBooking(appointmentId, appointmentData) {
        this.editingAppointmentId = appointmentId;
        this.selectedAppointmentType = appointmentData.appointmentType || null;
        this.currentStep = 2; // Jump to Step 2 per specification
        
        this.showModal();
        this.updateStepDisplay();
        this.populateFormWithAppointment(appointmentData);
        
        console.log('✏️ Modal opened for editing appointment:', appointmentId);
    }

    /**
     * Show the modal
     */
    showModal() {
        const modal = document.getElementById('unified-booking-modal');
        const backdrop = document.getElementById('unified-booking-modal-backdrop');
        
        if (modal && backdrop) {
            modal.style.display = 'flex';
            modal.classList.add('show');
            backdrop.style.display = 'block';
            document.body.classList.add('modal-open');
            
            console.log('✅ Modal should now be visible');
            
            // Focus first input in current step
            this.focusFirstInput();
        } else {
            console.error('❌ Modal or backdrop element not found:', { modal: !!modal, backdrop: !!backdrop });
        }
    }

    /**
     * Close the modal
     */
    closeModal() {
        const modal = document.getElementById('unified-booking-modal');
        const backdrop = document.getElementById('unified-booking-modal-backdrop');
        
        if (modal && backdrop) {
            modal.classList.remove('show');
            backdrop.style.display = 'none';
            document.body.classList.remove('modal-open');
        }
        
        // Reset state
        this.currentStep = 1;
        this.selectedAppointmentType = null;
        this.editingAppointmentId = null;
        this.clearForm();
        
        console.log('❌ Modal closed');
    }

    /**
     * Navigate to Step 1 (Appointment Type Selection)
     */
    goToStep1() {
        this.currentStep = 1;
        this.updateStepDisplay();
        this.loadAppointmentTypes();
        console.log('➡️ Navigated to Step 1');
    }

    /**
     * Navigate to Step 2 (Booking Details)
     */
    goToStep2() {
        // Validate appointment type selection
        if (!this.selectedAppointmentType) {
            this.showValidationError('Please select an appointment type before continuing.');
            return;
        }
        
        console.log('✅ Validation passed, proceeding to Step 2');
        this.currentStep = 2;
        this.updateStepDisplay();
        this.populateFormFromAppointmentType();
        this.populateUserContext();
        console.log('➡️ Navigated to Step 2');
    }

    /**
     * Show validation error message
     */
    showValidationError(message) {
        // Remove any existing error messages
        const existingError = document.querySelector('.validation-error');
        if (existingError) {
            existingError.remove();
        }

        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'validation-error';
        errorDiv.style.cssText = `
            background: #fee;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 10px 15px;
            border-radius: 6px;
            margin: 15px 0;
            font-size: 0.9rem;
        `;
        errorDiv.textContent = message;

        // Insert error message before the modal footer
        const modalFooter = document.querySelector('.unified-modal .modal-footer');
        if (modalFooter) {
            modalFooter.parentNode.insertBefore(errorDiv, modalFooter);
        }

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }

    /**
     * Update the step display and navigation buttons
     */
    updateStepDisplay() {
        // Update progress indicator
        const steps = document.querySelectorAll('.step');
        steps.forEach((step, index) => {
            const stepNumber = index + 1;
            step.classList.remove('active', 'completed');
            
            if (stepNumber === this.currentStep) {
                step.classList.add('active');
            } else if (stepNumber < this.currentStep) {
                step.classList.add('completed');
            }
        });

        // Update step visibility
        const step1 = document.getElementById('appointment-type-step');
        const step2 = document.getElementById('booking-details-step');
        
        if (step1 && step2) {
            step1.classList.toggle('active', this.currentStep === 1);
            step2.classList.toggle('active', this.currentStep === 2);
        }

        // Update button visibility
        this.updateNavigationButtons();
        
        // Update modal title
        const title = document.getElementById('unified-modal-title');
        if (title) {
            title.textContent = this.currentStep === 1 ? 'Select Appointment Type' : 'Booking Details';
        }
    }

    /**
     * Update navigation button visibility and state
     */
    updateNavigationButtons() {
        const continueButton = document.getElementById('unified-continue-to-step2-button');
        const backButton = document.getElementById('unified-back-to-step1-button');
        const saveButton = document.getElementById('unified-save-booking-button');

        if (continueButton && backButton && saveButton) {
            if (this.currentStep === 1) {
                continueButton.style.display = 'inline-flex';
                backButton.style.display = 'none';
                saveButton.style.display = 'none';
                
                // Enable/disable continue button based on appointment type selection
                const hasSelection = !!this.selectedAppointmentType;
                continueButton.disabled = !hasSelection;
                
                // Visual feedback
                if (hasSelection) {
                    continueButton.classList.remove('btn-disabled');
                    continueButton.title = 'Continue to booking details';
                } else {
                    continueButton.classList.add('btn-disabled');
                    continueButton.title = 'Please select an appointment type first';
                }
                
                console.log('🔄 Continue button state:', hasSelection ? 'enabled' : 'disabled');
            } else if (this.currentStep === 2) {
                continueButton.style.display = 'none';
                backButton.style.display = 'inline-flex';
                saveButton.style.display = 'inline-flex';
            }
        }
    }

    /**
     * Load appointment types for Step 1
     */
    async loadAppointmentTypes() {
        const container = document.getElementById('unified-appointment-type-tree');
        const loading = document.getElementById('unified-appointment-type-loading');
        
        if (!container) return;

        try {
            loading.style.display = 'flex';
            
            // Load real appointment types from the API (using the correct endpoint format)
            const practiceId = 1; // TODO: Get from user session/context
            const response = await fetch(`/api/practices/${practiceId}/appointment-types/effective?enabled_only=true`);
            
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status}`);
            }
            
            const effectiveTypes = await response.json();
            console.log('✅ Loaded effective appointment types:', effectiveTypes.length);
            
            // Group types by category (parent_id)
            const { categories, childTypes } = this.groupAppointmentTypes(effectiveTypes);
            
            this.renderAppointmentTypesHierarchy(categories, childTypes);
            loading.style.display = 'none';
            
        } catch (error) {
            console.error('❌ Error loading appointment types:', error);
            loading.innerHTML = '<div style="text-align: center; padding: 20px;"><p>Error loading appointment types</p><button onclick="window.unifiedBookingModal.loadAppointmentTypes()" class="btn btn-secondary">Retry</button></div>';
        }
    }

    /**
     * Group appointment types into categories and child types
     */
    groupAppointmentTypes(effectiveTypes) {
        const categories = new Map();
        const childTypes = [];
        
        // First pass: collect all categories (parent_id = null)
        effectiveTypes.forEach(type => {
            if (type.parent_id === null) {
                categories.set(type.id, {
                    category: type,
                    children: []
                });
            }
        });
        
        // Second pass: collect child types and assign to categories
        effectiveTypes.forEach(type => {
            if (type.parent_id !== null) {
                const parentCategory = categories.get(type.parent_id);
                if (parentCategory) {
                    parentCategory.children.push(type);
                } else {
                    // Orphaned child type - add to general list
                    childTypes.push(type);
                }
            }
        });
        
        return { categories: Array.from(categories.values()), childTypes };
    }

    /**
     * Render appointment types in hierarchical tree structure
     */
    renderAppointmentTypesHierarchy(categories, orphanedTypes = []) {
        const container = document.getElementById('unified-appointment-type-tree');
        if (!container) return;

        let html = '<div class="appointment-type-hierarchy">';
        
        // Render categories with their children
        categories.forEach(({ category, children }) => {
            if (children.length > 0) {
                // Category with children - render as expandable group
                html += `
                    <div class="appointment-type-category">
                        <div class="category-header" onclick="this.parentElement.classList.toggle('expanded')">
                            <span class="category-name">${category.name}</span>
                            <span class="category-count">${children.length}</span>
                            <span class="expand-icon">▼</span>
                        </div>
                        <div class="category-children">
                `;
                
                children.forEach(type => {
                    html += this.renderAppointmentTypeItem(type);
                });
                
                html += `
                        </div>
                    </div>
                `;
            } else {
                // Category with no children - render as selectable item
                html += this.renderAppointmentTypeItem(category);
            }
        });
        
        // Render orphaned types (if any)
        if (orphanedTypes.length > 0) {
            html += '<div class="appointment-type-category orphaned"><div class="category-header">Other Types</div><div class="category-children">';
            orphanedTypes.forEach(type => {
                html += this.renderAppointmentTypeItem(type);
            });
            html += '</div></div>';
        }
        
        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Render individual appointment type item
     */
    renderAppointmentTypeItem(type) {
        // Handle effective duration and color
        const duration = type.effective_duration || type.duration || 30;
        const color = type.colour || type.color || '#2D6356';
        const description = type.description || '';
        
        // Safely stringify the type object for the onclick handler
        const typeDataAttr = JSON.stringify({
            id: type.id,
            name: type.name,
            color: color,
            duration: duration,
            description: description,
            default_billing_codes: type.default_billing_codes || [],
            default_notes: type.default_notes || ''
        }).replace(/"/g, '&quot;');
        
        return `
            <div class="appointment-type-item" data-type-id="${type.id}" onclick="window.unifiedBookingModal.selectAppointmentType(${typeDataAttr})">
                <div class="type-color" style="background-color: ${color}"></div>
                <div class="type-info">
                    <div class="type-name">${type.name}</div>
                    <div class="type-details">
                        <span class="type-duration">${duration} min</span>
                        ${description ? `<span class="type-description">${description}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Select an appointment type
     */
    selectAppointmentType(appointmentType) {
        this.selectedAppointmentType = appointmentType;
        
        // Update selection visual
        document.querySelectorAll('.appointment-type-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        const selectedItem = document.querySelector(`[data-type-id="${appointmentType.id}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
        }
        
        // Show preview
        this.showAppointmentTypePreview();
        
        // Enable continue button
        this.updateNavigationButtons();
        
        console.log('✅ Appointment type selected:', appointmentType.name);
    }

    /**
     * Show appointment type preview
     */
    showAppointmentTypePreview() {
        const preview = document.getElementById('unified-selected-type-preview');
        if (!preview || !this.selectedAppointmentType) return;

        const colorSpan = preview.querySelector('.preview-color');
        const nameSpan = preview.querySelector('.preview-name');
        const durationSpan = preview.querySelector('.preview-duration');
        const descriptionSpan = preview.querySelector('.preview-description');

        if (colorSpan) colorSpan.style.backgroundColor = this.selectedAppointmentType.color;
        if (nameSpan) nameSpan.textContent = this.selectedAppointmentType.name;
        if (durationSpan) durationSpan.textContent = `${this.selectedAppointmentType.duration} min`;
        if (descriptionSpan) descriptionSpan.textContent = this.selectedAppointmentType.description || '';

        preview.style.display = 'block';
    }

    /**
     * Populate form fields from selected appointment type
     */
    populateFormFromAppointmentType() {
        if (!this.selectedAppointmentType) return;

        // Duration
        const durationInput = document.getElementById('unified-booking-duration');
        if (durationInput) {
            durationInput.value = this.selectedAppointmentType.duration;
            this.showFieldIndicator(durationInput, 'auto-populated');
        }

        // Color
        const colorPicker = document.getElementById('unified-booking-colour-picker');
        const colorHex = document.getElementById('unified-booking-colour-hex');
        const colorHidden = document.getElementById('unified-booking-colour');
        
        if (colorPicker && this.selectedAppointmentType.color) {
            colorPicker.value = this.selectedAppointmentType.color;
            if (colorHex) colorHex.textContent = this.selectedAppointmentType.color;
            if (colorHidden) colorHidden.value = this.selectedAppointmentType.color;
            this.showFieldIndicator(colorPicker, 'auto-populated');
        }

        // Notes (if template available)
        if (this.selectedAppointmentType.default_notes) {
            const notesInput = document.getElementById('unified-booking-notes');
            if (notesInput) {
                notesInput.value = this.selectedAppointmentType.default_notes;
                this.showFieldIndicator(notesInput, 'auto-populated');
            }
        }

        // Billing codes
        if (this.selectedAppointmentType.default_billing_codes && this.selectedAppointmentType.default_billing_codes.length > 0) {
            this.populateBillingCodes(this.selectedAppointmentType.default_billing_codes);
            console.log('💳 Populated billing codes from appointment type:', this.selectedAppointmentType.default_billing_codes.length);
        } else {
            // Add empty row if no default codes
            this.populateBillingCodes([]);
            console.log('💳 No default billing codes, added empty row');
        }

        // Update selected type display
        this.updateSelectedTypeDisplay();

        // Update end time
        this.updateEndTime();
    }

    /**
     * Populate user context fields (profession/therapist)
     */
    populateUserContext() {
        if (!this.userContext) return;

        console.log('👤 Auto-populating user context:', this.userContext);

        // Profession
        const professionSelect = document.getElementById('unified-therapist-profession');
        if (professionSelect && this.userContext.profession) {
            professionSelect.value = this.userContext.profession;
            this.showFieldIndicator(professionSelect, 'auto-populated');
            
            // Trigger profession change to filter therapists
            this.filterTherapistByProfession();
        }

        // Therapist - set after profession filter
        setTimeout(() => {
            const therapistSelect = document.getElementById('unified-therapist-name');
            if (therapistSelect && this.userContext.id) {
                therapistSelect.value = this.userContext.id;
                
                // Show appropriate indicator and handle locking
                if (this.userContext.isAdmin) {
                    this.showFieldIndicator(therapistSelect, 'auto-populated');
                    // Add "(You)" indicator to current user's option
                    const currentUserOption = therapistSelect.querySelector(`option[value="${this.userContext.id}"]`);
                    if (currentUserOption && !currentUserOption.textContent.includes('(You)')) {
                        currentUserOption.textContent += ' (You)';
                    }
                } else {
                    this.showFieldIndicator(therapistSelect, 'locked');
                    therapistSelect.disabled = true;
                    therapistSelect.title = 'Regular users can only book for themselves';
                }
            }
        }, 100);
    }

    /**
     * Filter therapist by profession
     */
    filterTherapistByProfession() {
        const selectedProfession = document.getElementById('unified-therapist-profession')?.value;
        const therapistSelect = document.getElementById('unified-therapist-name');
        
        if (!therapistSelect || !this.therapists) return;

        therapistSelect.innerHTML = '<option value="">Select therapist...</option>';
        
        const filteredTherapists = selectedProfession 
            ? this.therapists.filter(t => t.profession === selectedProfession)
            : this.therapists;

        filteredTherapists.forEach(therapist => {
            const option = document.createElement('option');
            option.value = therapist.id;
            option.textContent = therapist.preferred_name || `${therapist.name} ${therapist.surname}`;
            therapistSelect.appendChild(option);
        });

        console.log('👥 Filtered therapists by profession:', selectedProfession, filteredTherapists.length);
    }

    /**
     * Show field indicator with enhanced visual cues
     */
    showFieldIndicator(fieldElement, type) {
        const indicator = fieldElement.parentElement.querySelector('.field-indicator');
        if (indicator) {
            indicator.style.display = 'inline';
            indicator.className = `field-indicator ${type}`;
            
            // Add visual enhancement based on type
            if (type === 'auto-populated') {
                fieldElement.style.backgroundColor = 'rgba(3, 105, 161, 0.05)';
                fieldElement.style.borderLeftColor = '#0369a1';
                fieldElement.style.borderLeftWidth = '3px';
                fieldElement.style.borderLeftStyle = 'solid';
            } else if (type === 'locked') {
                fieldElement.style.backgroundColor = 'rgba(220, 38, 38, 0.05)';
                fieldElement.style.borderLeftColor = '#dc2626';
                fieldElement.style.borderLeftWidth = '3px';
                fieldElement.style.borderLeftStyle = 'solid';
            }
        }
        
        console.log(`🎨 Field indicator set: ${fieldElement.id} -> ${type}`);
    }

    /**
     * Open patient search modal
     */
    openPatientSearch() {
        console.log('🔍 openPatientSearch method called');
        
        const searchModal = document.getElementById('unified-patient-search-modal');
        const searchInput = document.getElementById('unified-patient-search-input');
        const resultsDiv = document.getElementById('unified-patient-search-results');
        
        console.log('Modal elements found:', {
            searchModal: !!searchModal,
            searchInput: !!searchInput, 
            resultsDiv: !!resultsDiv
        });
        
        if (searchModal) {
            searchModal.style.display = 'block';
            
            // Clear previous search
            if (searchInput) {
                searchInput.value = '';
            }
            if (resultsDiv) {
                resultsDiv.innerHTML = '<div class="search-placeholder">Start typing to search patients...</div>';
            }
            
            // Focus on search input
            setTimeout(() => {
                if (searchInput) {
                    searchInput.focus();
                }
            }, 100);
            
            console.log('✅ Patient search modal opened successfully');
        } else {
            console.error('❌ Patient search modal not found in DOM');
            alert('Patient search modal not found. Please refresh the page.');
        }
    }

    /**
     * Close patient search modal
     */
    closePatientSearch() {
        const searchModal = document.getElementById('unified-patient-search-modal');
        if (searchModal) {
            searchModal.style.display = 'none';
        }
    }

    /**
     * Search patients based on query
     */
    searchPatients(query) {
        const resultsDiv = document.getElementById('unified-patient-search-results');
        if (!resultsDiv) return;
        
        const searchQuery = query.toLowerCase().trim();
        
        if (!searchQuery) {
            resultsDiv.innerHTML = '<div class="search-placeholder">Start typing to search patients...</div>';
            return;
        }
        
        if (!this.patients || this.patients.length === 0) {
            resultsDiv.innerHTML = '<div class="no-results">No patients available. Please add patients first.</div>';
            return;
        }
        
        // Filter patients based on search query
        const filteredPatients = this.patients.filter(patient => {
            const searchFields = [
                patient.first_name || '',
                patient.surname || '',
                patient.preferred_name || '',
                patient.contact_number || '',
                patient.id_number || ''
            ].map(field => field.toLowerCase());
            
            return searchFields.some(field => field.includes(searchQuery));
        });
        
        if (filteredPatients.length === 0) {
            resultsDiv.innerHTML = '<div class="no-results">No patients found matching your search.</div>';
            return;
        }
        
        // Display search results
        resultsDiv.innerHTML = filteredPatients.map(patient => `
            <div class="patient-search-result" onclick="window.unifiedBookingModal.selectPatientFromSearch(${patient.id})">
                <div class="patient-name">${patient.preferred_name || patient.first_name} ${patient.surname}</div>
                <div class="patient-details">ID: ${patient.id_number || 'N/A'} | Phone: ${patient.contact_number || 'N/A'}</div>
            </div>
        `).join('');
        
        console.log(`🔍 Patient search results: ${filteredPatients.length} found for "${query}"`);
    }

    /**
     * Select patient from search results
     */
    selectPatientFromSearch(patientId) {
        console.log(`🎯 selectPatientFromSearch called with ID: ${patientId} (type: ${typeof patientId})`);
        
        // Handle both string and number IDs by converting to string for comparison
        const patient = this.patients.find(p => String(p.id) === String(patientId));
        if (!patient) {
            console.error(`❌ Patient not found with ID: ${patientId}`);
            console.log('Available patient IDs:', this.patients.map(p => ({ id: p.id, type: typeof p.id })));
            return;
        }
        
        console.log(`📋 Patient found:`, patient);
        
        // Store the selected patient
        this.selectedPatient = patient;
        console.log(`✅ Selected patient stored:`, this.selectedPatient);
        
        // Set the patient in the dropdown
        const patientSelect = document.getElementById('unified-patient-name');
        if (patientSelect) {
            patientSelect.value = patientId;
            console.log(`✅ Patient selected: ${patient.preferred_name || patient.first_name} ${patient.surname}`);
        } else {
            console.error(`❌ Patient dropdown not found`);
        }
        
        // Close the search modal
        this.closePatientSearch();
        console.log(`✅ Patient search modal closed`);
    }

    /**
     * Handle patient dropdown change
     */
    onPatientDropdownChange() {
        const patientSelect = document.getElementById('unified-patient-name');
        if (!patientSelect) return;

        const selectedPatientId = patientSelect.value;
        if (!selectedPatientId) {
            this.selectedPatient = null;
            console.log('🧹 Patient selection cleared');
            return;
        }

        // Find the patient in the loaded patients array
        const patient = this.patients.find(p => String(p.id) === String(selectedPatientId));
        if (patient) {
            this.selectedPatient = patient;
            console.log(`✅ Patient selected from dropdown:`, this.selectedPatient);
        } else {
            console.warn(`⚠️ Patient not found in loaded patients for ID: ${selectedPatientId}`);
            this.selectedPatient = null;
        }
    }

    /**
     * Update selected appointment type display in Step 2
     */
    updateSelectedTypeDisplay() {
        if (!this.selectedAppointmentType) return;

        const colorSpan = document.querySelector('.selected-type-color');
        const nameSpan = document.querySelector('.selected-type-name');
        const durationSpan = document.querySelector('.selected-type-duration');

        if (colorSpan) colorSpan.style.backgroundColor = this.selectedAppointmentType.color;
        if (nameSpan) nameSpan.textContent = this.selectedAppointmentType.name;
        if (durationSpan) durationSpan.textContent = `${this.selectedAppointmentType.duration} min`;
    }

    /**
     * Update end time based on start time and duration
     */
    updateEndTime() {
        const startTimeInput = document.getElementById('unified-start-time');
        const durationInput = document.getElementById('unified-booking-duration');
        const endTimeInput = document.getElementById('unified-end-time');

        if (!startTimeInput || !durationInput || !endTimeInput) return;

        const startTime = startTimeInput.value;
        const duration = parseInt(durationInput.value) || 0;

        if (startTime && duration) {
            const [hours, minutes] = startTime.split(':').map(Number);
            const startDate = new Date();
            startDate.setHours(hours, minutes, 0);

            const endDate = new Date(startDate.getTime() + duration * 60000);
            const endTimeString = endDate.toTimeString().slice(0, 5);
            endTimeInput.value = endTimeString;
        }
    }

    /**
     * Handle keyboard navigation
     */
    handleKeyboard(event) {
        if (!document.getElementById('unified-booking-modal').classList.contains('show')) {
            return;
        }

        switch (event.key) {
            case 'Escape':
                this.closeModal();
                break;
            case 'Enter':
                if (event.ctrlKey || event.metaKey) {
                    if (this.currentStep === 1 && this.selectedAppointmentType) {
                        this.goToStep2();
                    } else if (this.currentStep === 2) {
                        this.saveBooking();
                    }
                }
                break;
        }
    }

    /**
     * Focus first input in current step
     */
    focusFirstInput() {
        setTimeout(() => {
            const currentStepElement = document.querySelector('.modal-step.active');
            if (currentStepElement) {
                const firstInput = currentStepElement.querySelector('input, select, textarea');
                if (firstInput) {
                    firstInput.focus();
                }
            }
        }, 100);
    }

    /**
     * Clear form fields
     */
    clearForm() {
        const form = document.getElementById('unified-booking-form');
        if (form) {
            form.reset();
        }
        
        // Clear billing table
        const billingTableBody = document.getElementById('unified-booking-billing-table-body');
        if (billingTableBody) {
            billingTableBody.innerHTML = '';
        }
        
        // Hide field indicators
        document.querySelectorAll('.field-indicator').forEach(indicator => {
            indicator.style.display = 'none';
        });
    }

    /**
     * Save booking (placeholder)
     */
    async saveBooking() {
        console.log('💾 Saving booking...');
        
        try {
            // Validate form data
            const formData = this.collectFormData();
            if (!this.validateFormData(formData)) {
                return; // Validation errors will be shown to user
            }

            // Prepare booking data for API
            const bookingData = this.prepareBookingData(formData);
            console.log('📤 Submitting booking data:', bookingData);

            // Submit to API
            const apiEndpoint = this.isEditing ? `/api/bookings/${this.editingAppointmentId}` : '/api/bookings';
            const method = this.isEditing ? 'PATCH' : 'POST';
            
            const response = await fetch(apiEndpoint, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(bookingData)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Failed to ${this.isEditing ? 'update' : 'create'} booking`);
            }

            const savedBooking = await response.json();
            console.log('✅ Booking saved successfully:', savedBooking);

            // Close modal and refresh calendar
            this.closeModal();
            
            // Trigger calendar refresh if available
            if (window.loadWeekView) {
                window.loadWeekView();
            } else if (window.refreshCalendar) {
                window.refreshCalendar();
            }

            // Show success message
            this.showSuccessMessage(this.isEditing ? 'Appointment updated successfully!' : 'Appointment created successfully!');

        } catch (error) {
            console.error('❌ Error saving booking:', error);
            this.showErrorMessage('Failed to save appointment: ' + error.message);
        }
    }

    /**
     * Populate billing codes table with codes (from appointment type or editing)
     */
    populateBillingCodes(codes) {
        console.log('📋 Populating billing codes:', codes);
        
        const tableBody = document.getElementById('unified-booking-billing-table-body');
        if (!tableBody) return;

        // Clear existing rows
        tableBody.innerHTML = '';

        if (!codes || codes.length === 0) {
            // Add empty row if no codes provided
            this.addBillingCodeRow();
            return;
        }

        // Add rows for each billing code
        codes.forEach(code => {
            this.addBillingCodeRow(code);
        });

        this.updateGrandTotal();
    }

    /**
     * Add a new billing code row to the table
     */
    addBillingCodeRow(existingCode = null) {
        const tableBody = document.getElementById('unified-booking-billing-table-body');
        if (!tableBody) return;

        const rowIndex = tableBody.children.length;
        const row = document.createElement('tr');
        row.className = 'billing-code-row';
        row.dataset.rowIndex = rowIndex;

        // Default values
        const code = existingCode?.code || '';
        const quantity = existingCode?.quantity || 1;
        const modifier = existingCode?.modifier || '';

        row.innerHTML = `
            <td>
                <select class="billing-code-select" onchange="window.unifiedBookingModal.onBillingCodeChange(${rowIndex})">
                    <option value="">Select code...</option>
                    ${this.generateBillingCodeOptions(code)}
                </select>
            </td>
            <td class="billing-description"></td>
            <td>
                <input type="number" class="billing-quantity" value="${quantity}" min="1" 
                       onchange="window.unifiedBookingModal.onQuantityChange(${rowIndex})" />
            </td>
            <td>
                <select class="billing-modifier-select" onchange="window.unifiedBookingModal.onModifierChange(${rowIndex})">
                    <option value="">No Modifier</option>
                    ${this.generateModifierOptions(modifier)}
                </select>
            </td>
            <td class="billing-rate">R0.00</td>
            <td class="billing-line-total">R0.00</td>
            <td>
                <button type="button" class="btn btn-secondary remove-billing-row" 
                        onclick="window.unifiedBookingModal.removeBillingCodeRow(${rowIndex})" 
                        title="Remove this billing code">×</button>
            </td>
        `;

        tableBody.appendChild(row);

        // If we had an existing code, populate it
        if (existingCode?.code) {
            const codeSelect = row.querySelector('.billing-code-select');
            codeSelect.value = existingCode.code;
            this.onBillingCodeChange(rowIndex);
        }

        console.log('➕ Added billing code row:', rowIndex);
        return row;
    }

    /**
     * Remove a billing code row
     */
    removeBillingCodeRow(rowIndex) {
        const tableBody = document.getElementById('unified-booking-billing-table-body');
        if (!tableBody) return;

        const rows = tableBody.querySelectorAll('.billing-code-row');
        if (rows.length <= 1) {
            // Don't remove the last row, just clear it
            this.clearBillingCodeRow(rowIndex);
            return;
        }

        const row = tableBody.querySelector(`[data-row-index="${rowIndex}"]`);
        if (row) {
            row.remove();
            this.reindexBillingRows();
            this.updateGrandTotal();
            console.log('➖ Removed billing code row:', rowIndex);
        }
    }

    /**
     * Clear a billing code row
     */
    clearBillingCodeRow(rowIndex) {
        const row = document.querySelector(`[data-row-index="${rowIndex}"]`);
        if (!row) return;

        row.querySelector('.billing-code-select').value = '';
        row.querySelector('.billing-quantity').value = '1';
        row.querySelector('.billing-modifier-select').value = '';
        row.querySelector('.billing-description').textContent = '';
        row.querySelector('.billing-rate').textContent = 'R0.00';
        row.querySelector('.billing-line-total').textContent = 'R0.00';
        
        this.updateGrandTotal();
        console.log('🧹 Cleared billing code row:', rowIndex);
    }

    /**
     * Reindex all billing rows after removal
     */
    reindexBillingRows() {
        const tableBody = document.getElementById('unified-booking-billing-table-body');
        if (!tableBody) return;

        const rows = tableBody.querySelectorAll('.billing-code-row');
        rows.forEach((row, index) => {
            row.dataset.rowIndex = index;
            
            // Update event handlers with new index
            const codeSelect = row.querySelector('.billing-code-select');
            const quantityInput = row.querySelector('.billing-quantity');
            const modifierSelect = row.querySelector('.billing-modifier-select');
            const removeBtn = row.querySelector('.remove-billing-row');

            codeSelect.setAttribute('onchange', `window.unifiedBookingModal.onBillingCodeChange(${index})`);
            quantityInput.setAttribute('onchange', `window.unifiedBookingModal.onQuantityChange(${index})`);
            modifierSelect.setAttribute('onchange', `window.unifiedBookingModal.onModifierChange(${index})`);
            removeBtn.setAttribute('onclick', `window.unifiedBookingModal.removeBillingCodeRow(${index})`);
        });
    }

    /**
     * Generate billing code options HTML
     */
    generateBillingCodeOptions(selectedCode = '') {
        if (!this.allBillingCodes || this.allBillingCodes.length === 0) {
            return '<option value="" disabled>No billing codes available</option>';
        }

        return this.allBillingCodes.map(code => {
            const selected = code.code === selectedCode ? 'selected' : '';
            // Show code and description in dropdown for selection, but will display only code when closed
            return `<option value="${code.code}" ${selected} data-description="${code.description}" data-rate="${code.base_fee || code.rate || 0}">${code.code} - ${code.description}</option>`;
        }).join('');
    }

    /**
     * Generate modifier options HTML
     */
    generateModifierOptions(selectedModifier = '') {
        if (!this.billingModifiers || this.billingModifiers.length === 0) {
            return '<option value="" disabled>No modifiers available</option>';
        }

        // Filter modifiers by current user's profession
        const userProfession = this.userContext?.profession || 'Physiotherapy';
        
        return this.billingModifiers
            .filter(modifier => {
                // Always include "No Modifier" option
                if (!modifier.modifier_code) return true;
                // Include modifiers that match profession or have no profession specified
                return !modifier.profession || modifier.profession === userProfession;
            })
            .map(modifier => {
                // Handle "No Modifier" option
                if (!modifier.modifier_code) return '';
                
                const selected = modifier.modifier_code === selectedModifier ? 'selected' : '';
                // Show only the modifier code in dropdown, tooltip will show full name
                return `<option value="${modifier.modifier_code}" ${selected} 
                        data-multiplier="${modifier.modifier_multiplier}" 
                        data-name="${modifier.modifier_name}"
                        title="${modifier.modifier_name}">
                        ${modifier.modifier_code}
                        </option>`;
            })
            .filter(Boolean)
            .join('');
    }

    /**
     * Handle billing code selection change
     */
    onBillingCodeChange(rowIndex) {
        const row = document.querySelector(`[data-row-index="${rowIndex}"]`);
        if (!row) return;

        const codeSelect = row.querySelector('.billing-code-select');
        const selectedOption = codeSelect.selectedOptions[0];
        
        if (selectedOption && selectedOption.value) {
            const code = selectedOption.value;
            const description = selectedOption.dataset.description || '';
            const rate = parseFloat(selectedOption.dataset.rate || 0);

            // Update the description column
            row.querySelector('.billing-description').textContent = description;
            row.querySelector('.billing-rate').textContent = `R${rate.toFixed(2)}`;
            
            // Change the display text of the selected option to show only the code
            selectedOption.textContent = code;
            
            console.log('🏷️ Billing code selected:', code, description, rate);
        } else {
            row.querySelector('.billing-description').textContent = '';
            row.querySelector('.billing-rate').textContent = 'R0.00';
        }

        this.calculateRowTotal(rowIndex);
    }

    /**
     * Handle quantity change
     */
    onQuantityChange(rowIndex) {
        console.log('🔢 Quantity changed for row:', rowIndex);
        this.calculateRowTotal(rowIndex);
    }

    /**
     * Handle modifier selection change
     */
    onModifierChange(rowIndex) {
        const row = document.querySelector(`[data-row-index="${rowIndex}"]`);
        if (!row) return;

        const modifierSelect = row.querySelector('.billing-modifier-select');
        const selectedOption = modifierSelect.selectedOptions[0];
        
        if (selectedOption) {
            const modifierName = selectedOption.dataset.name || '';
            console.log('🔧 Modifier selected:', selectedOption.value, modifierName);
        }

        this.calculateRowTotal(rowIndex);
    }

    /**
     * Calculate line total for a specific row
     */
    calculateRowTotal(rowIndex) {
        const row = document.querySelector(`[data-row-index="${rowIndex}"]`);
        if (!row) return;

        const quantity = parseInt(row.querySelector('.billing-quantity')?.value || 0);
        const rateText = row.querySelector('.billing-rate')?.textContent || 'R0.00';
        const baseRate = parseFloat(rateText.replace('R', '') || 0);
        
        const modifierSelect = row.querySelector('.billing-modifier-select');
        const selectedModifier = modifierSelect.selectedOptions[0];
        const multiplier = selectedModifier ? parseFloat(selectedModifier.dataset.multiplier || 1) : 1;

        const lineTotal = quantity * baseRate * multiplier;
        row.querySelector('.billing-line-total').textContent = `R${lineTotal.toFixed(2)}`;

        this.updateGrandTotal();
        
        console.log('💰 Calculation details:', {
            rowIndex,
            quantity,
            baseRate: `R${baseRate}`,
            modifier: selectedModifier?.value || 'none',
            multiplier,
            lineTotal: `R${lineTotal.toFixed(2)}`
        });
    }

    /**
     * Update grand total
     */
    updateGrandTotal() {
        const tableBody = document.getElementById('unified-booking-billing-table-body');
        const grandTotalElement = document.getElementById('unified-billing-grand-total');
        
        if (!tableBody || !grandTotalElement) return;

        let grandTotal = 0;
        const rows = tableBody.querySelectorAll('.billing-code-row');
        
        rows.forEach(row => {
            const lineTotalText = row.querySelector('.billing-line-total')?.textContent || 'R0.00';
            const lineTotal = parseFloat(lineTotalText.replace('R', '') || 0);
            grandTotal += lineTotal;
        });

        grandTotalElement.textContent = `R${grandTotal.toFixed(2)}`;
        console.log('🧮 Grand total updated:', `R${grandTotal.toFixed(2)}`);
    }

    populateFormWithAppointment(appointmentData) {
        console.log('📝 Populating form with appointment data:', appointmentData);
        
        // Set editing mode
        this.isEditing = true;
        this.editingAppointmentId = appointmentData.id;
        
        // Update modal title
        const modalTitle = document.getElementById('modal-title');
        if (modalTitle) {
            modalTitle.textContent = 'Edit Appointment';
        }

        // Basic appointment fields
        const dateField = document.getElementById('unified-booking-date');
        if (dateField && appointmentData.date) {
            dateField.value = appointmentData.date;
        }

        const timeField = document.getElementById('unified-start-time');
        if (timeField && appointmentData.time) {
            timeField.value = appointmentData.time;
        }

        const durationField = document.getElementById('unified-booking-duration');
        if (durationField && appointmentData.duration) {
            durationField.value = appointmentData.duration;
        }

        const notesField = document.getElementById('unified-booking-notes');
        if (notesField && appointmentData.notes) {
            notesField.value = appointmentData.notes;
        }

        const colorField = document.getElementById('unified-booking-colour');
        const colorPicker = document.getElementById('unified-booking-colour-picker');
        const colorHex = document.getElementById('unified-booking-colour-hex');
        if (appointmentData.colour) {
            if (colorField) colorField.value = appointmentData.colour;
            if (colorPicker) colorPicker.value = appointmentData.colour;
            if (colorHex) colorHex.textContent = appointmentData.colour;
        }

        // Patient selection
        if (appointmentData.patient_id) {
            this.loadPatientForEditing(appointmentData.patient_id);
        }

        // Therapist and profession
        const professionField = document.getElementById('unified-therapist-profession');
        if (professionField && appointmentData.profession) {
            professionField.value = appointmentData.profession;
            this.filterTherapistByProfession();
        }

        setTimeout(() => {
            const therapistField = document.getElementById('unified-therapist-name');
            if (therapistField && appointmentData.therapist) {
                therapistField.value = appointmentData.therapist;
            }
        }, 100);

        // Appointment type - if available, set it and skip Step 1
        if (appointmentData.appointment_type_id) {
            this.loadAppointmentTypeForEditing(appointmentData.appointment_type_id);
        } else {
            // No appointment type, start with Step 1
            this.goToStep(1);
        }

        // Billing codes - parse from billing_code field
        this.populateBillingCodesFromString(appointmentData.billing_code);
    }

    /**
     * Collect all form data for submission
     */
    collectFormData() {
        const formData = {
            // Basic appointment details
            date: document.getElementById('unified-booking-date')?.value,
            time: document.getElementById('unified-start-time')?.value,
            duration: parseInt(document.getElementById('unified-booking-duration')?.value) || 60,
            notes: document.getElementById('unified-booking-notes')?.value || '',
            colour: document.getElementById('unified-booking-colour')?.value || '#007bff',
            
            // Patient and therapist
            patient_id: this.selectedPatient?.id || document.getElementById('unified-patient-name')?.value || null,
            therapist: parseInt(document.getElementById('unified-therapist-name')?.value) || null,
            profession: document.getElementById('unified-therapist-profession')?.value || '',
            
            // Appointment type
            appointment_type_id: this.selectedAppointmentType?.id || null,
            
            // Billing codes
            billingCodes: this.collectBillingCodes()
        };

        console.log('📝 Collected form data:', formData);
        
        // Additional debug for date issues
        if (formData.date) {
            const dateObj = new Date(formData.date);
            console.log('📅 Date analysis:', {
                dateString: formData.date,
                dayOfWeek: dateObj.toLocaleDateString('en-US', { weekday: 'long' }),
                fullDate: dateObj.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
            });
        }
        
        return formData;
    }

    /**
     * Collect billing codes from the table
     */
    collectBillingCodes() {
        const billingCodes = [];
        const rows = document.querySelectorAll('#unified-booking-billing-table-body .billing-code-row');
        
        rows.forEach(row => {
            const codeSelect = row.querySelector('.billing-code-select');
            const quantityInput = row.querySelector('.billing-quantity');
            const modifierSelect = row.querySelector('.billing-modifier-select');
            
            const code = codeSelect?.value;
            const quantity = parseInt(quantityInput?.value) || 1;
            const modifier = modifierSelect?.value || '';
            
            if (code) { // Only include rows with selected codes
                billingCodes.push({
                    code: code,
                    quantity: quantity,
                    modifier: modifier
                });
            }
        });

        console.log('💰 Collected billing codes:', billingCodes);
        return billingCodes;
    }

    /**
     * Validate form data before submission
     */
    validateFormData(formData) {
        const errors = [];

        // Required fields validation
        if (!formData.date) {
            errors.push('Date is required');
        }
        if (!formData.time) {
            errors.push('Time is required');
        }
        if (!formData.therapist) {
            errors.push('Therapist is required');
        }
        if (!formData.appointment_type_id) {
            errors.push('Appointment type is required');
        }

        // Patient validation - required if there are billing codes
        if (formData.billingCodes && formData.billingCodes.length > 0 && !formData.patient_id) {
            console.log('🚨 Patient validation failed:', {
                billingCodes: formData.billingCodes,
                billingCodesCount: formData.billingCodes.length,
                patient_id: formData.patient_id,
                selectedPatient: this.selectedPatient,
                patientDropdownValue: document.getElementById('unified-patient-name')?.value
            });
            errors.push('Patient selection is required when billing codes are present');
        }

        // Date validation
        if (formData.date) {
            const selectedDate = new Date(formData.date);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (selectedDate < today) {
                errors.push('Cannot create appointments in the past');
            }
        }

        // Duration validation
        if (formData.duration < 15 || formData.duration > 480) {
            errors.push('Duration must be between 15 and 480 minutes');
        }

        // Show errors to user
        if (errors.length > 0) {
            this.showErrorMessage('Please fix the following errors:\n• ' + errors.join('\n• '));
            return false;
        }

        return true;
    }

    /**
     * Prepare booking data in the format expected by the API
     */
    prepareBookingData(formData) {
        // Calculate end time
        const startTime = formData.time;
        const endTime = this.calculateEndTime(startTime, formData.duration);
        
        // Generate appointment ID if creating new
        const appointmentId = this.isEditing ? this.editingAppointmentId : this.generateAppointmentId();
        
        // Get day name from date
        const dayName = new Date(formData.date).toLocaleDateString('en-US', { weekday: 'long' });
        console.log('📅 Day name calculation:', {
            inputDate: formData.date,
            calculatedDay: dayName,
            dateObject: new Date(formData.date)
        });

        // Prepare booking data matching the Booking model
        const patientName = this.selectedPatient 
            ? (this.selectedPatient.preferred_name || `${this.selectedPatient.first_name} ${this.selectedPatient.surname}`)
            : 'Walk-in Patient';
            
        const bookingData = {
            id: appointmentId,
            name: patientName,
            therapist: formData.therapist,
            date: formData.date,
            day: dayName,
            time: startTime,
            duration: formData.duration,
            notes: formData.notes,
            colour: formData.colour,
            profession: formData.profession,
            patient_id: formData.patient_id,
            appointment_type_id: formData.appointment_type_id,
            billing_code: this.formatBillingCodesForAPI(formData.billingCodes)
        };

        console.log('📤 Final booking data prepared:', bookingData);
        return bookingData;
    }

    /**
     * Format billing codes for the API (legacy single billing_code field)
     */
    formatBillingCodesForAPI(billingCodes) {
        // For now, use the first billing code for the legacy billing_code field
        // TODO: Update API to handle multiple billing codes properly
        if (billingCodes && billingCodes.length > 0) {
            const primaryCode = billingCodes[0];
            return primaryCode.modifier ? `${primaryCode.code}:${primaryCode.modifier}` : primaryCode.code;
        }
        return null;
    }

    /**
     * Calculate end time based on start time and duration
     */
    calculateEndTime(startTime, duration) {
        if (!startTime) return '';
        
        const [hours, minutes] = startTime.split(':').map(Number);
        const startMinutes = hours * 60 + minutes;
        const endMinutes = startMinutes + duration;
        
        const endHours = Math.floor(endMinutes / 60) % 24;
        const endMins = endMinutes % 60;
        
        return `${endHours.toString().padStart(2, '0')}:${endMins.toString().padStart(2, '0')}`;
    }

    /**
     * Generate unique appointment ID
     */
    generateAppointmentId() {
        return 'apt_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
    }

    /**
     * Show success message to user
     */
    showSuccessMessage(message) {
        // Use existing notification system if available, otherwise alert
        if (window.showNotification) {
            window.showNotification(message, 'success');
        } else if (window.toastr && window.toastr.success) {
            window.toastr.success(message);
        } else {
            alert(message);
        }
    }

    /**
     * Show error message to user
     */
    showErrorMessage(message) {
        // Use existing notification system if available, otherwise alert
        if (window.showNotification) {
            window.showNotification(message, 'error');
        } else if (window.toastr && window.toastr.error) {
            window.toastr.error(message);
        } else {
            alert(message);
        }
    }

    /**
     * Load patient data for editing mode
     */
    async loadPatientForEditing(patientId) {
        try {
            const response = await fetch(`/api/patients/${patientId}`);
            if (response.ok) {
                const patient = await response.json();
                this.selectedPatient = patient;
                
                // Update patient display
                const patientNameField = document.getElementById('unified-patient-name');
                if (patientNameField) {
                    patientNameField.value = patient.name || `${patient.first_name} ${patient.last_name}`;
                }
                
                console.log('👤 Loaded patient for editing:', patient);
            }
        } catch (error) {
            console.error('❌ Error loading patient for editing:', error);
        }
    }

    /**
     * Load appointment type for editing mode
     */
    async loadAppointmentTypeForEditing(appointmentTypeId) {
        try {
            if (this.appointmentTypes) {
                const appointmentType = this.appointmentTypes.find(at => at.id === appointmentTypeId);
                if (appointmentType) {
                    this.selectedAppointmentType = appointmentType;
                    this.updateSelectedTypeDisplay();
                    
                    // Skip to Step 2 since we have the appointment type
                    this.goToStep(2);
                    console.log('🎯 Loaded appointment type for editing:', appointmentType);
                    return;
                }
            }

            // If not found in cache, fetch from API
            const response = await fetch(`/api/appointment-types/${appointmentTypeId}`);
            if (response.ok) {
                const appointmentType = await response.json();
                this.selectedAppointmentType = appointmentType;
                this.updateSelectedTypeDisplay();
                this.goToStep(2);
                console.log('🎯 Fetched appointment type for editing:', appointmentType);
            } else {
                console.warn('⚠️ Appointment type not found, starting with Step 1');
                this.goToStep(1);
            }
        } catch (error) {
            console.error('❌ Error loading appointment type for editing:', error);
            this.goToStep(1);
        }
    }

    /**
     * Parse billing codes from the legacy billing_code string format
     */
    populateBillingCodesFromString(billingCodeString) {
        if (!billingCodeString) {
            this.populateBillingCodes([]);
            return;
        }

        try {
            // Handle different formats:
            // 1. Simple code: "72501"
            // 2. Code with modifier: "72501:0001"
            // 3. JSON array (future format): "[{...}]"
            
            let billingCodes = [];
            
            if (billingCodeString.startsWith('[')) {
                // JSON format
                billingCodes = JSON.parse(billingCodeString);
            } else {
                // String format
                const parts = billingCodeString.split(':');
                billingCodes = [{
                    code: parts[0],
                    quantity: 1,
                    modifier: parts[1] || ''
                }];
            }

            this.populateBillingCodes(billingCodes);
            console.log('💰 Populated billing codes from string:', billingCodes);
            
        } catch (error) {
            console.error('❌ Error parsing billing codes:', error);
            this.populateBillingCodes([]);
        }
    }

    /**
     * Open modal for editing an existing appointment
     */
    openForEditing(appointmentData) {
        console.log('✏️ Opening modal for editing appointment:', appointmentData.id);
        
        // Reset state
        this.reset();
        
        // Show modal
        const modal = document.getElementById('unified-booking-modal');
        if (modal) {
            modal.style.display = 'block';
        }

        // Populate form with appointment data
        this.populateFormWithAppointment(appointmentData);
    }
}

// Note: openUnifiedPatientSearch and closeUnifiedPatientSearch functions
// are defined in the HTML template to have access to the modal instance

function filterUnifiedTherapistByProfession() {
    if (window.unifiedBookingModal) {
        window.unifiedBookingModal.filterTherapistByProfession();
    }
}

// Initialize global instance
window.unifiedBookingModal = new UnifiedBookingModal();

console.log('🚀 Unified Booking Modal JavaScript loaded - Version 20250827d');