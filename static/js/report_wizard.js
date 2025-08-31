/**
 * Report Creation Wizard - 5-Step Process
 * Handles multi-step report creation with booking-based recommendations
 */

class ReportWizard {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 5;
        this.state = {
            patient: null,
            reportType: null,
            template: null,
            title: '',
            disciplines: [],
            therapists: [],
            priority: 2,
            deadline: null
        };
        this.recommendationData = null;
        this.isManager = false;
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        this.modal = document.getElementById('report-wizard-modal');
        this.backdrop = document.getElementById('report-wizard-backdrop');
        this.steps = document.querySelectorAll('.wizard-step');
        this.progressSteps = document.querySelectorAll('.progress-step');
        
        console.log('🔍 Wizard elements found:', {
            modal: !!this.modal,
            backdrop: !!this.backdrop, 
            steps: this.steps.length,
            progressSteps: this.progressSteps.length
        });
        
        // Navigation buttons
        this.backBtn = document.getElementById('wizard-back-btn');
        this.nextBtn = document.getElementById('wizard-next-btn');
        this.finishBtn = document.getElementById('wizard-finish-btn');
        this.cancelBtn = document.getElementById('wizard-cancel-btn');
        
        // Step 1 elements
        this.patientSearch = document.getElementById('wizard-patient-search');
        this.patientResults = document.getElementById('wizard-patient-results');
        this.recentPatients = document.getElementById('wizard-recent-patients');
        this.selectedPatientDiv = document.getElementById('wizard-selected-patient');
        
        // Step 2 elements
        this.reportTypeSelect = document.getElementById('wizard-report-type');
        this.templateSelect = document.getElementById('wizard-template');
        this.titleInput = document.getElementById('wizard-title');
        this.templatePreview = document.getElementById('wizard-template-preview');
        
        // Step 3 elements
        this.recommendedDisciplines = document.getElementById('wizard-recommended-disciplines');
        this.disciplineCheckboxes = document.querySelectorAll('input[type="checkbox"][value*="therapy"], input[type="checkbox"][value="psychology"]');
        
        // Step 4 elements
        this.therapistRoleInfo = document.getElementById('therapist-role-info');
        this.suggestedTherapists = document.getElementById('wizard-suggested-therapists');
        this.otherTherapists = document.getElementById('wizard-other-therapists');
        
        // Step 5 elements
        this.priorityRadios = document.querySelectorAll('input[name="wizard-priority"]');
        this.deadlineInput = document.getElementById('wizard-deadline');
        
        // Summary elements
        this.summaryElements = {
            patient: document.getElementById('sidebar-patient'),
            reportType: document.getElementById('sidebar-report-type'),
            title: document.getElementById('sidebar-title'),
            disciplines: document.getElementById('sidebar-disciplines'),
            therapists: document.getElementById('sidebar-therapists'),
            priority: document.getElementById('sidebar-priority'),
            deadline: document.getElementById('sidebar-deadline')
        };
    }
    
    bindEvents() {
        // Navigation events
        this.backBtn?.addEventListener('click', () => this.goToPreviousStep());
        this.nextBtn?.addEventListener('click', () => this.goToNextStep());
        this.finishBtn?.addEventListener('click', () => this.submitReport());
        this.cancelBtn?.addEventListener('click', () => this.close());
        
        // Close events
        document.getElementById('close-wizard-modal')?.addEventListener('click', () => this.close());
        this.backdrop?.addEventListener('click', () => this.close());
        
        // Step 1 events
        this.patientSearch?.addEventListener('input', this.debounce((e) => this.searchPatients(e.target.value), 300));
        
        // Step 2 events
        this.reportTypeSelect?.addEventListener('change', () => this.onReportTypeChange());
        this.templateSelect?.addEventListener('change', () => this.onTemplateChange());
        this.titleInput?.addEventListener('input', () => this.updateSummary());
        
        // Step 3 events
        this.disciplineCheckboxes?.forEach(checkbox => {
            checkbox.addEventListener('change', () => this.onDisciplineChange());
        });
        
        // Step 5 events
        this.priorityRadios?.forEach(radio => {
            radio.addEventListener('change', () => this.updateSummary());
        });
        this.deadlineInput?.addEventListener('change', () => this.updateSummary());
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (this.modal && this.modal.style.display !== 'none') {
                if (e.key === 'Escape') this.close();
                if (e.key === 'Enter' && !e.target.matches('input, textarea')) {
                    e.preventDefault();
                    if (this.currentStep < this.totalSteps) this.goToNextStep();
                    else this.submitReport();
                }
            }
        });
    }
    
    open(workflowType = 'therapist', reportId = null) {
        this.isManager = workflowType === 'manager';
        this.reset();
        
        // Set modal title based on workflow
        document.getElementById('wizard-modal-title').textContent = 
            this.isManager ? 'Assign Report to Therapist' : 'Create New Report';
        
        // Show role info in step 4
        if (!this.isManager) {
            this.therapistRoleInfo.style.display = 'block';
        }
        
        this.modal.style.display = 'block';
        this.backdrop.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Load initial data
        this.loadRecentPatients();
        this.loadWizardOptions();
        
        // Focus on patient search
        setTimeout(() => this.patientSearch?.focus(), 100);
    }
    
    close() {
        this.modal.style.display = 'none';
        this.backdrop.style.display = 'none';
        document.body.style.overflow = '';
        this.reset();
    }
    
    reset() {
        this.currentStep = 1;
        this.state = {
            patient: null,
            reportType: null,
            template: null,
            title: '',
            disciplines: [],
            therapists: [],
            priority: 2,
            deadline: null
        };
        this.recommendationData = null;
        
        // Reset UI
        this.showStep(1);
        this.updateNavigation();
        this.updateSummary();
        this.clearValidationMessages();
    }
    
    showStep(stepNumber) {
        // Update progress indicator
        this.progressSteps.forEach((step, index) => {
            step.classList.toggle('active', index + 1 === stepNumber);
            step.classList.toggle('completed', index + 1 < stepNumber);
        });
        
        // Show/hide step content
        this.steps.forEach((step, index) => {
            step.classList.toggle('active', index + 1 === stepNumber);
        });
        
        this.currentStep = stepNumber;
        this.updateNavigation();
        
        // Step-specific actions
        switch(stepNumber) {
            case 3:
                this.loadDisciplineRecommendations();
                break;
            case 4:
                this.loadTherapistSuggestions();
                break;
            case 5:
                this.updateFinalSummary();
                break;
        }
    }
    
    updateNavigation() {
        // Back button
        this.backBtn.style.display = this.currentStep > 1 ? 'block' : 'none';
        
        // Next/Finish button
        if (this.currentStep < this.totalSteps) {
            this.nextBtn.style.display = 'block';
            this.finishBtn.style.display = 'none';
            this.nextBtn.disabled = !this.isStepValid(this.currentStep);
        } else {
            this.nextBtn.style.display = 'none';
            this.finishBtn.style.display = 'block';
            this.finishBtn.disabled = !this.isStepValid(this.currentStep);
        }
    }
    
    goToNextStep() {
        if (this.isStepValid(this.currentStep) && this.currentStep < this.totalSteps) {
            this.showStep(this.currentStep + 1);
        }
    }
    
    goToPreviousStep() {
        if (this.currentStep > 1) {
            this.showStep(this.currentStep - 1);
        }
    }
    
    isStepValid(stepNumber) {
        switch(stepNumber) {
            case 1:
                return this.state.patient !== null;
            case 2:
                return this.state.reportType && this.state.template && this.state.title.trim();
            case 3:
                return this.state.disciplines.length > 0;
            case 4:
                return this.state.therapists.length > 0;
            case 5:
                return true; // Priority has default, deadline is optional
            default:
                return false;
        }
    }
    
    // ========== API CALLS ==========
    
    async loadWizardOptions(patientId = null, disciplines = null) {
        try {
            let url = '/api/reports/wizard/options';
            const params = new URLSearchParams();
            if (patientId) params.append('patient_id', patientId);
            if (disciplines && disciplines.length > 0) params.append('disciplines', disciplines.join(','));
            
            if (params.toString()) url += '?' + params.toString();
            
            const response = await fetch(url, { credentials: 'include' });
            if (!response.ok) throw new Error('Failed to load wizard options');
            
            this.recommendationData = await response.json();
            this.populateReportTypes();
            
            return this.recommendationData;
        } catch (error) {
            console.error('Error loading wizard options:', error);
            this.showError('Failed to load wizard options');
            return null;
        }
    }
    
    async loadRecentPatients() {
        try {
            const response = await fetch('/api/patients/recent?limit=5', { credentials: 'include' });
            if (!response.ok) throw new Error('Failed to load recent patients');
            
            const patients = await response.json();
            this.displayRecentPatients(patients);
        } catch (error) {
            console.error('Error loading recent patients:', error);
            this.recentPatients.innerHTML = '<div class="error-message">Failed to load recent patients</div>';
        }
    }
    
    async searchPatients(query) {
        if (!query || query.length < 2) {
            this.patientResults.innerHTML = '';
            return;
        }
        
        try {
            this.patientResults.innerHTML = '<div class="loading">Searching...</div>';
            
            const response = await fetch(`/api/patients/search?query=${encodeURIComponent(query)}&limit=10`, { credentials: 'include' });
            if (!response.ok) throw new Error('Search failed');
            
            const patients = await response.json();
            this.displaySearchResults(patients);
        } catch (error) {
            console.error('Error searching patients:', error);
            this.patientResults.innerHTML = '<div class="error-message">Search failed</div>';
        }
    }
    
    async loadTemplates(reportType) {
        try {
            const response = await fetch(`/api/report-templates?template_type=${reportType}&is_active=true`, { credentials: 'include' });
            if (!response.ok) throw new Error('Failed to load templates');
            
            const templates = await response.json();
            this.populateTemplates(templates);
        } catch (error) {
            console.error('Error loading templates:', error);
            this.showError('Failed to load templates');
        }
    }
    
    // ========== UI POPULATION METHODS ==========
    
    populateReportTypes() {
        const options = this.recommendationData?.allowed_report_types || [];
        this.reportTypeSelect.innerHTML = '<option value="">Select report type...</option>';
        
        const typeLabels = {
            'discharge': 'Discharge Report',
            'progress': 'Progress Report', 
            'insurance': 'Insurance Report',
            'outcome_summary': 'Outcome Summary',
            'assessment': 'Assessment Report'
        };
        
        options.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = typeLabels[type] || type;
            this.reportTypeSelect.appendChild(option);
        });
    }
    
    populateTemplates(templates) {
        this.templateSelect.innerHTML = '<option value="">Select template...</option>';
        
        templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            this.templateSelect.appendChild(option);
        });
    }
    
    displayRecentPatients(patients) {
        if (!patients || patients.length === 0) {
            this.recentPatients.innerHTML = '<div class="no-results">No recent patients found</div>';
            return;
        }
        
        this.recentPatients.innerHTML = patients.map(patient => `
            <div class="patient-card recent-patient" onclick="selectPatient('${patient.id}', '${patient.first_name} ${patient.surname}', '${patient.dob}', '${patient.identifiers || ''}')">
                <div class="patient-info">
                    <div class="patient-name">${patient.first_name} ${patient.surname}</div>
                    <div class="patient-details">
                        <span class="patient-dob">DOB: ${patient.dob}</span>
                        ${patient.identifiers ? `<span class="patient-id">${patient.identifiers}</span>` : ''}
                    </div>
                </div>
                <div class="patient-meta">
                    <span class="recent-indicator">Recent</span>
                </div>
            </div>
        `).join('');
    }
    
    displaySearchResults(patients) {
        if (!patients || patients.length === 0) {
            this.patientResults.innerHTML = '<div class="no-results">No patients found</div>';
            return;
        }
        
        this.patientResults.innerHTML = patients.map(patient => `
            <div class="patient-card search-result" onclick="selectPatient('${patient.id}', '${patient.first_name} ${patient.surname}', '${patient.dob}', '${patient.identifiers || ''}')">
                <div class="patient-info">
                    <div class="patient-name">${patient.first_name} ${patient.surname}</div>
                    <div class="patient-details">
                        <span class="patient-dob">DOB: ${patient.dob}</span>
                        ${patient.identifiers ? `<span class="patient-id">${patient.identifiers}</span>` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    async loadDisciplineRecommendations() {
        if (!this.state.patient) return;
        
        try {
            const data = await this.loadWizardOptions(this.state.patient.id);
            if (data?.recommended_disciplines && data.recommended_disciplines.length > 0) {
                this.displayDisciplineRecommendations(data.recommended_disciplines);
                this.preselectRecommendedDisciplines(data.recommended_disciplines);
            }
        } catch (error) {
            console.error('Error loading discipline recommendations:', error);
        }
    }
    
    displayDisciplineRecommendations(recommendations) {
        this.recommendedDisciplines.style.display = 'block';
        
        const container = this.recommendedDisciplines.querySelector('.discipline-recommendations');
        container.innerHTML = recommendations.map(rec => `
            <div class="recommendation-chip" data-discipline="${rec.discipline}">
                <div class="recommendation-content">
                    <div class="recommendation-name">${this.formatDisciplineName(rec.discipline)}</div>
                    <div class="recommendation-stats">
                        ${rec.bookings_count} booking${rec.bookings_count !== 1 ? 's' : ''} | Last: ${this.formatDate(rec.last_seen)}
                    </div>
                </div>
                <div class="recommendation-badge">Recommended</div>
            </div>
        `).join('');
    }
    
    preselectRecommendedDisciplines(recommendations) {
        recommendations.forEach(rec => {
            const checkbox = document.getElementById(`discipline-${rec.discipline.replace(/_/g, '-')}`);
            if (checkbox) {
                checkbox.checked = true;
                this.state.disciplines.push(rec.discipline);
            }
        });
        this.updateSummary();
        this.updateNavigation();
    }
    
    async loadTherapistSuggestions() {
        if (!this.state.patient || this.state.disciplines.length === 0) return;
        
        try {
            const data = await this.loadWizardOptions(this.state.patient.id, this.state.disciplines);
            
            if (data?.suggested_therapists && data.suggested_therapists.length > 0) {
                this.displayTherapistSuggestions(data.suggested_therapists);
            }
            
            if (data?.other_therapists && data.other_therapists.length > 0) {
                this.displayOtherTherapists(data.other_therapists);
            }
            
            // Auto-select current user if therapist
            if (!this.isManager && data?.user_defaults?.assigned_therapist_ids) {
                this.state.therapists = [...data.user_defaults.assigned_therapist_ids];
                this.updateTherapistSelection();
            }
            
        } catch (error) {
            console.error('Error loading therapist suggestions:', error);
        }
    }
    
    displayTherapistSuggestions(suggestions) {
        this.suggestedTherapists.style.display = 'block';
        
        const container = this.suggestedTherapists.querySelector('.therapist-suggestions');
        container.innerHTML = suggestions.map(therapist => `
            <div class="therapist-card suggested" data-user-id="${therapist.user_id}">
                <div class="therapist-checkbox">
                    <input type="checkbox" id="therapist-${therapist.user_id}" value="${therapist.user_id}" 
                           onchange="wizard.toggleTherapist('${therapist.user_id}', '${therapist.name}')" />
                </div>
                <div class="therapist-info">
                    <div class="therapist-name">${therapist.name}</div>
                    <div class="therapist-disciplines">${therapist.disciplines.join(', ')}</div>
                    <div class="therapist-stats">
                        ${therapist.bookings_count_with_patient} session${therapist.bookings_count_with_patient !== 1 ? 's' : ''} | 
                        Last: ${this.formatDate(therapist.last_seen)}
                    </div>
                </div>
                <div class="suggestion-badge">Suggested</div>
            </div>
        `).join('');
    }
    
    displayOtherTherapists(others) {
        if (others.length === 0) return;
        
        this.otherTherapists.style.display = 'block';
        
        const container = this.otherTherapists.querySelector('.therapist-list');
        container.innerHTML = others.map(therapist => `
            <div class="therapist-card" data-user-id="${therapist.user_id}">
                <div class="therapist-checkbox">
                    <input type="checkbox" id="therapist-${therapist.user_id}" value="${therapist.user_id}" 
                           onchange="wizard.toggleTherapist('${therapist.user_id}', '${therapist.name}')" />
                </div>
                <div class="therapist-info">
                    <div class="therapist-name">${therapist.name}</div>
                    <div class="therapist-disciplines">${therapist.disciplines.join(', ')}</div>
                </div>
            </div>
        `).join('');
    }
    
    // ========== EVENT HANDLERS ==========
    
    selectPatient(patientId, patientName, dob, identifiers) {
        this.state.patient = {
            id: patientId,
            name: patientName,
            dob: dob,
            identifiers: identifiers
        };
        
        // Show selected patient
        document.getElementById('selected-patient-name').textContent = patientName;
        document.getElementById('selected-patient-dob').textContent = `DOB: ${dob}`;
        document.getElementById('selected-patient-id').textContent = identifiers || '';
        
        this.selectedPatientDiv.style.display = 'block';
        this.patientSearch.value = '';
        this.patientResults.innerHTML = '';
        
        this.updateSummary();
        this.updateNavigation();
    }
    
    clearSelectedPatient() {
        this.state.patient = null;
        this.selectedPatientDiv.style.display = 'none';
        this.updateSummary();
        this.updateNavigation();
    }
    
    async onReportTypeChange() {
        const reportType = this.reportTypeSelect.value;
        this.state.reportType = reportType;
        
        if (reportType) {
            await this.loadTemplates(reportType);
        } else {
            this.templateSelect.innerHTML = '<option value="">Select template...</option>';
            this.state.template = null;
        }
        
        this.updateSummary();
        this.updateNavigation();
    }
    
    onTemplateChange() {
        this.state.template = {
            id: this.templateSelect.value,
            name: this.templateSelect.options[this.templateSelect.selectedIndex]?.text
        };
        
        this.generateAutoTitle();
        this.updateSummary();
        this.updateNavigation();
    }
    
    onDisciplineChange() {
        const selectedDisciplines = Array.from(this.disciplineCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        
        this.state.disciplines = selectedDisciplines;
        this.updateSummary();
        this.updateNavigation();
    }
    
    toggleTherapist(userId, name) {
        const index = this.state.therapists.findIndex(t => t.id === userId);
        if (index >= 0) {
            this.state.therapists.splice(index, 1);
        } else {
            this.state.therapists.push({ id: userId, name: name });
        }
        
        this.updateSummary();
        this.updateNavigation();
    }
    
    updateTherapistSelection() {
        this.state.therapists.forEach(therapist => {
            const checkbox = document.getElementById(`therapist-${therapist.id}`);
            if (checkbox) checkbox.checked = true;
        });
    }
    
    // ========== UTILITY METHODS ==========
    
    generateAutoTitle() {
        if (this.state.patient && this.state.reportType) {
            const today = new Date().toISOString().split('T')[0];
            const typeLabel = this.reportTypeSelect.options[this.reportTypeSelect.selectedIndex]?.text;
            
            this.state.title = `${this.state.patient.name} - ${typeLabel} - ${today}`;
            this.titleInput.value = this.state.title;
            this.updateSummary();
        }
    }
    
    updateSummary() {
        // Update sidebar summary
        this.summaryElements.patient.textContent = this.state.patient?.name || 'Not selected';
        this.summaryElements.reportType.textContent = this.state.reportType ? 
            this.reportTypeSelect.options[this.reportTypeSelect.selectedIndex]?.text : 'Not selected';
        this.summaryElements.title.textContent = this.state.title || '-';
        this.summaryElements.disciplines.textContent = this.state.disciplines.length > 0 ? 
            this.state.disciplines.map(d => this.formatDisciplineName(d)).join(', ') : 'Not selected';
        this.summaryElements.therapists.textContent = this.state.therapists.length > 0 ?
            this.state.therapists.map(t => t.name).join(', ') : 'Not selected';
        
        // Priority
        const priorityValue = document.querySelector('input[name="wizard-priority"]:checked')?.value || 2;
        const priorityLabels = {1: 'Low', 2: 'Medium', 3: 'High'};
        this.summaryElements.priority.textContent = priorityLabels[priorityValue];
        this.state.priority = parseInt(priorityValue);
        
        // Deadline
        this.state.deadline = this.deadlineInput?.value || null;
        this.summaryElements.deadline.textContent = this.state.deadline || 'No deadline';
    }
    
    updateFinalSummary() {
        // Update the main summary in step 5
        document.getElementById('summary-patient').textContent = this.state.patient?.name || '-';
        document.getElementById('summary-report-type').textContent = this.state.reportType || '-';
        document.getElementById('summary-template').textContent = this.state.template?.name || '-';
        document.getElementById('summary-title').textContent = this.state.title || '-';
        document.getElementById('summary-disciplines').textContent = 
            this.state.disciplines.map(d => this.formatDisciplineName(d)).join(', ') || '-';
        document.getElementById('summary-therapists').textContent = 
            this.state.therapists.map(t => t.name).join(', ') || '-';
    }
    
    formatDisciplineName(discipline) {
        const formatMap = {
            'physiotherapy': 'Physiotherapy',
            'occupational_therapy': 'Occupational Therapy',
            'speech_therapy': 'Speech Therapy',
            'psychology': 'Psychology'
        };
        return formatMap[discipline] || discipline.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    formatDate(dateString) {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        return date.toLocaleDateString();
    }
    
    clearValidationMessages() {
        document.querySelectorAll('.validation-message, .error-text').forEach(el => {
            el.style.display = 'none';
        });
    }
    
    showError(message) {
        // Show error in a toast or alert
        console.error(message);
        alert(message); // Simple implementation, can be enhanced
    }
    
    // ========== SUBMISSION ==========
    
    async submitReport() {
        if (!this.isStepValid(5)) {
            this.showError('Please complete all required fields');
            return;
        }
        
        try {
            this.finishBtn.disabled = true;
            this.finishBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
            
            const payload = {
                patient_id: this.state.patient.id,
                report_type: this.state.reportType,
                template_id: parseInt(this.state.template.id),
                title: this.state.title,
                disciplines: this.state.disciplines,
                assigned_therapist_ids: this.state.therapists.map(t => t.id),
                priority: this.state.priority,
                deadline_date: this.state.deadline,
                generate_ai_content: true  // Default to generating AI content
            };
            
            const response = await fetch('/api/reports/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create report');
            }
            
            const result = await response.json();
            
            // Success - close modal and refresh dashboard
            this.close();
            this.showSuccess('Report created successfully!');
            
            // Refresh dashboard if available
            if (window.refreshDashboard) {
                window.refreshDashboard();
            }
            
        } catch (error) {
            console.error('Error creating report:', error);
            this.showError(error.message);
            this.finishBtn.disabled = false;
            this.finishBtn.innerHTML = '<i class="fas fa-check"></i> Create Report';
        }
    }
    
    showSuccess(message) {
        // Simple success implementation
        alert(message);
    }
    
    // ========== UTILITY FUNCTIONS ==========
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// ========== GLOBAL FUNCTIONS ==========

// Initialize wizard when page loads or script loads
let wizard;

function initializeWizard() {
    console.log('🧙‍♂️ Initializing Report Wizard...');
    wizard = new ReportWizard();
    console.log('✅ Report Wizard initialized successfully');
}

// Initialize immediately if DOM is already ready, otherwise wait for DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWizard);
} else {
    // DOM is already ready
    setTimeout(initializeWizard, 100); // Small delay to ensure HTML is inserted
}

// Global functions for external access
function openReportWizard(workflowType = 'therapist', reportId = null) {
    console.log(`🚀 Opening Report Wizard - workflowType: ${workflowType}, reportId: ${reportId}`);
    if (wizard) {
        wizard.open(workflowType, reportId);
        console.log('✅ Wizard opened successfully');
    } else {
        console.log('⏳ Wizard not ready yet, waiting...');
        // Wait a bit and try again
        setTimeout(() => {
            if (wizard) {
                console.log('✅ Wizard ready after delay');
                wizard.open(workflowType, reportId);
            } else {
                console.error('❌ Wizard still not initialized after delay');
                alert('Report wizard is loading, please try again in a moment.');
            }
        }, 500);
    }
}

function closeReportWizard() {
    if (wizard) {
        wizard.close();
    }
}

// Compatibility function for legacy calls
function openReportRequestModal(workflowType = 'therapist', reportId = null) {
    console.log('⚠️ openReportRequestModal is deprecated, redirecting to wizard...');
    openReportWizard(workflowType, reportId);
}

// Set global window functions to ensure they take priority
window.openReportWizard = openReportWizard;
window.closeReportWizard = closeReportWizard; 
window.openReportRequestModal = openReportRequestModal;

// Patient selection function (called from onclick in HTML)
function selectPatient(patientId, patientName, dob, identifiers) {
    if (wizard) {
        wizard.selectPatient(patientId, patientName, dob, identifiers);
    }
}

// Clear patient selection
function clearSelectedPatient() {
    if (wizard) {
        wizard.clearSelectedPatient();
    }
}

// Auto-generate title
function generateWizardTitle() {
    if (wizard) {
        wizard.generateAutoTitle();
    }
}

// Deadline shortcuts
function setWizardDeadline(days) {
    const deadline = new Date();
    deadline.setDate(deadline.getDate() + days);
    
    const deadlineInput = document.getElementById('wizard-deadline');
    if (deadlineInput) {
        deadlineInput.value = deadline.toISOString().split('T')[0];
        if (wizard) {
            wizard.updateSummary();
        }
    }
}