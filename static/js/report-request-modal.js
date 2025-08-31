/**
 * Report Request Modal - JavaScript functionality
 * Supports both manager-initiated and therapist-initiated workflows
 */

// Global state
let reportRequestState = {
    currentStep: 1,
    workflowType: null, // 'manager' or 'therapist'
    selectedPatient: null,
    selectedTemplate: null,
    selectedDisciplines: [],
    selectedDisciplineDetails: [],
    aiContentOptions: {
        generateMedicalHistory: true,
        generateTreatmentSummary: true,
        generateOutcomeAnalysis: false
    },
    isEditing: false,
    editingReportId: null
};

// Modal control functions
function openReportRequestModal(workflowType = 'therapist', reportId = null) {
    reportRequestState.workflowType = workflowType;
    reportRequestState.isEditing = !!reportId;
    reportRequestState.editingReportId = reportId;
    
    const modal = document.getElementById('report-request-modal');
    const backdrop = document.getElementById('report-request-modal-backdrop');
    
    // Set workflow type
    const workflowTypeElement = document.getElementById('workflow-type');
    if (workflowTypeElement) {
        workflowTypeElement.value = workflowType;
    }
    
    // Update UI based on workflow
    updateWorkflowUI();
    
    // Load initial data
    loadReportRequestData();
    
    // Show modal
    modal.style.display = 'flex';
    backdrop.style.display = 'block';
    
    // Set focus
    setTimeout(() => {
        const patientSelect = document.getElementById('report-patient-select');
        patientSelect.focus();
    }, 100);
}

function closeReportRequestModal() {
    const modal = document.getElementById('report-request-modal');
    const backdrop = document.getElementById('report-request-modal-backdrop');
    
    modal.style.display = 'none';
    backdrop.style.display = 'none';
    
    // Reset form
    resetReportRequestForm();
}

function updateWorkflowUI() {
    const workflowType = reportRequestState.workflowType;
    
    // Show/hide workflow indicators (with null checks)
    const managerIndicator = document.getElementById('manager-workflow-indicator');
    const therapistIndicator = document.getElementById('therapist-workflow-indicator');
    const selfNote = document.getElementById('self-assignment-note');
    const managerNote = document.getElementById('manager-assignment-note');
    const modalTitle = document.getElementById('report-modal-title');
    
    // Only update if elements exist (old modal might not be loaded)
    if (!managerIndicator || !therapistIndicator || !selfNote || !managerNote) {
        console.log('⚠️ Old modal elements not found - this is expected when using wizard');
        return;
    }
    
    if (workflowType === 'manager') {
        managerIndicator.style.display = 'flex';
        therapistIndicator.style.display = 'none';
        selfNote.style.display = 'none';
        managerNote.style.display = 'block';
        
        if (modalTitle) modalTitle.textContent = 'Create Report Request (Manager)';
    } else {
        managerIndicator.style.display = 'none';
        therapistIndicator.style.display = 'flex';
        selfNote.style.display = 'block';
        managerNote.style.display = 'none';
        
        if (modalTitle) modalTitle.textContent = 'Create Report Request';
    }
    
    // Update assigned therapists based on workflow
    updateAssignedTherapists();
}

// Data loading functions
async function loadReportRequestData() {
    try {
        // Load patients
        await loadPatientsForReports();
        
        // Add event listener for patient selection changes
        const patientSelect = document.getElementById('report-patient-select');
        patientSelect.addEventListener('change', function() {
            console.log('👤 Patient selection changed, updating therapist list...');
            loadTherapistsForAssignment();
        });
        
        // Load report templates
        await loadReportTemplates();
        
        // Load therapists
        await loadTherapistsForAssignment();
        
        // If editing, load existing report data
        if (reportRequestState.isEditing) {
            await loadExistingReportData();
        }
        
    } catch (error) {
        console.error('Error loading report request data:', error);
        showNotification('Error loading data. Please try again.', 'error');
    }
}

async function loadPatientsForReports() {
    try {
        const response = await fetch('/patients');
        const patients = await response.json();
        
        const patientSelect = document.getElementById('report-patient-select');
        patientSelect.innerHTML = '<option value="">Select a patient...</option>';
        
        patients.forEach(patient => {
            const option = document.createElement('option');
            option.value = patient.id;
            option.textContent = `${patient.first_name} ${patient.surname} (${patient.id})`;
            patientSelect.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading patients:', error);
        showNotification('Error loading patients', 'error');
    }
}

async function loadReportTemplates() {
    try {
        const response = await fetch('/api/report-templates');
        const templates = await response.json();
        
        const templateSelect = document.getElementById('report-template-select');
        templateSelect.innerHTML = '<option value="">Select template...</option>';
        
        templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            option.setAttribute('data-type', template.template_type);
            templateSelect.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading templates:', error);
        showNotification('Error loading templates', 'error');
    }
}

async function loadTherapistsForAssignment() {
    try {
        const selectedPatientId = document.getElementById('report-patient-select').value;
        
        if (selectedPatientId) {
            // Load only therapists who have treated this patient
            console.log('🔄 Loading therapists who treated patient:', selectedPatientId);
            const bookingsResponse = await fetch(`/api/patient/${selectedPatientId}/bookings`);
            
            if (bookingsResponse.ok) {
                const bookings = await bookingsResponse.json();
                
                // Extract unique therapists from bookings
                const patientTherapists = bookings
                    .filter(b => b.therapist_name && b.profession)
                    .reduce((acc, booking) => {
                        const key = booking.therapist_name;
                        if (!acc[key]) {
                            acc[key] = {
                                name: booking.therapist_name,
                                profession: booking.profession
                            };
                        }
                        return acc;
                    }, {});
                
                const therapistSelect = document.getElementById('assigned-therapists');
                therapistSelect.innerHTML = '<option value="">Select therapist who treated this patient...</option>';
                
                Object.values(patientTherapists).forEach(therapist => {
                    const option = document.createElement('option');
                    option.value = therapist.name; // Using name as value since we don't have user_id from bookings
                    option.textContent = `${therapist.name} (${therapist.profession})`;
                    therapistSelect.appendChild(option);
                });
                
                console.log('✅ Loaded therapists from patient history:', Object.keys(patientTherapists).length);
                
                if (Object.keys(patientTherapists).length === 0) {
                    therapistSelect.innerHTML = '<option value="">No therapists found in patient history</option>';
                    showNotification('No therapists found in this patient\'s booking history', 'warning');
                }
                
                return;
            }
        }
        
        // Fallback to all therapists if no patient selected or API fails
        console.log('🔄 Loading all therapists (fallback)');
        const response = await fetch('/therapists');
        const therapists = await response.json();
        
        const therapistSelect = document.getElementById('assigned-therapists');
        therapistSelect.innerHTML = '<option value="">Select a therapist...</option>';
        
        therapists.forEach(therapist => {
            const option = document.createElement('option');
            option.value = therapist.user_id;
            option.textContent = `${therapist.first_name} ${therapist.last_name} (${therapist.profession})`;
            therapistSelect.appendChild(option);
        });
        
        // Auto-select current user if therapist workflow
        if (reportRequestState.workflowType === 'therapist') {
            const currentUserId = getCurrentUserId();
            for (let option of therapistSelect.options) {
                if (option.value === currentUserId) {
                    option.selected = true;
                    break;
                }
            }
        }
        
    } catch (error) {
        console.error('Error loading therapists:', error);
        showNotification('Error loading therapists', 'error');
    }
}

// Form interaction handlers
function updateAssignedTherapists() {
    const therapistSelect = document.getElementById('assigned-therapists');
    
    if (reportRequestState.workflowType === 'therapist') {
        // Therapist workflow: auto-assign current user, make read-only
        therapistSelect.setAttribute('disabled', 'disabled');
    } else {
        // Manager workflow: allow selection of multiple therapists
        therapistSelect.removeAttribute('disabled');
    }
}

function generateReportTitle() {
    const patientSelect = document.getElementById('report-patient-select');
    const reportTypeSelect = document.getElementById('report-type-select');
    const titleInput = document.getElementById('report-title-input');
    
    if (patientSelect.value && reportTypeSelect.value) {
        const patientName = patientSelect.options[patientSelect.selectedIndex].textContent.split(' (')[0];
        const reportType = reportTypeSelect.options[reportTypeSelect.selectedIndex].textContent;
        const date = new Date().toLocaleDateString();
        
        const title = `${reportType} - ${patientName} - ${date}`;
        titleInput.value = title;
    }
}

function setDeadline(days) {
    const deadlineInput = document.getElementById('report-deadline');
    const deadline = new Date();
    deadline.setDate(deadline.getDate() + days);
    
    const formattedDate = deadline.toISOString().split('T')[0];
    deadlineInput.value = formattedDate;
}

async function autoDetectDisciplines() {
    const patientId = document.getElementById('report-patient-select').value;
    
    if (!patientId) {
        showNotification('Please select a patient first', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/reports/patient/${patientId}/disciplines`);
        const data = await response.json();
        
        // Clear existing selections
        const checkboxes = document.querySelectorAll('input[name="disciplines"]');
        checkboxes.forEach(cb => cb.checked = false);
        
        // Select detected disciplines
        data.disciplines.forEach(discipline => {
            const checkbox = document.getElementById(`discipline-${discipline.replace('_', '-')}`);
            if (checkbox) {
                checkbox.checked = true;
            }
        });
        
        showNotification(`Auto-detected ${data.disciplines.length} disciplines`, 'success');
        
    } catch (error) {
        console.error('Error auto-detecting disciplines:', error);
        showNotification('Could not auto-detect disciplines', 'error');
    }
}

// Step navigation
function goToStep(stepNumber) {
    const steps = document.querySelectorAll('.modal-step');
    const progressSteps = document.querySelectorAll('.progress-indicator .step');
    const buttons = {
        continue: document.getElementById('report-continue-button'),
        back: document.getElementById('report-back-button'),
        create: document.getElementById('create-report-button'),
        preview: document.getElementById('preview-ai-content-button')
    };
    
    // Hide all steps
    steps.forEach(step => step.classList.remove('active'));
    
    // Update progress indicator
    progressSteps.forEach((step, index) => {
        if (index + 1 <= stepNumber) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });
    
    if (stepNumber === 1) {
        // Step 1: Report Details
        document.getElementById('report-details-step').classList.add('active');
        buttons.back.style.display = 'none';
        buttons.continue.style.display = 'inline-block';
        buttons.create.style.display = 'none';
        buttons.preview.style.display = 'none';
        
    } else if (stepNumber === 2) {
        // Step 2: AI Content
        document.getElementById('ai-content-step').classList.add('active');
        buttons.back.style.display = 'inline-block';
        buttons.continue.style.display = 'none';
        buttons.create.style.display = 'inline-block';
        buttons.preview.style.display = 'inline-block';
    }
    
    reportRequestState.currentStep = stepNumber;
    validateCurrentStep();
}

function validateCurrentStep() {
    const continueBtn = document.getElementById('report-continue-button');
    const createBtn = document.getElementById('create-report-button');
    
    if (reportRequestState.currentStep === 1) {
        // Validate Step 1: Required fields
        const requiredFields = [
            'report-patient-select',
            'report-type-select',
            'report-template-select',
            'report-title-input'
        ];
        
        const isValid = requiredFields.every(fieldId => {
            const field = document.getElementById(fieldId);
            return field.value.trim() !== '';
        });
        
        // Also check that at least one discipline is selected
        const disciplineSelected = document.querySelectorAll('input[name="disciplines"]:checked').length > 0;
        
        // And at least one therapist is assigned
        const therapistSelect = document.getElementById('assigned-therapists');
        const therapistSelected = therapistSelect.selectedOptions.length > 0;
        
        continueBtn.disabled = !(isValid && disciplineSelected && therapistSelected);
        
    } else if (reportRequestState.currentStep === 2) {
        // Step 2 is always valid (AI content is optional)
        createBtn.disabled = false;
    }
}

// AI Content Generation
async function previewAIContent() {
    const patientId = document.getElementById('report-patient-select').value;
    const disciplines = getSelectedDisciplines();
    
    if (!patientId || disciplines.length === 0) {
        showNotification('Please select a patient and disciplines first', 'warning');
        return;
    }
    
    const statusDiv = document.getElementById('ai-generation-status');
    const previewDiv = document.querySelector('.ai-content-preview');
    
    statusDiv.style.display = 'block';
    previewDiv.style.display = 'none';
    
    try {
        // Generate medical history if requested
        if (document.getElementById('generate-medical-history').checked) {
            await generatePreviewContent('medical_history', patientId, disciplines);
        }
        
        // Generate treatment summary if requested
        if (document.getElementById('generate-treatment-summary').checked) {
            await generatePreviewContent('treatment_summary', patientId, disciplines);
        }
        
        statusDiv.style.display = 'none';
        previewDiv.style.display = 'block';
        
    } catch (error) {
        console.error('Error generating AI preview:', error);
        showNotification('Error generating AI content preview', 'error');
        statusDiv.style.display = 'none';
    }
}

async function generatePreviewContent(contentType, patientId, disciplines) {
    try {
        const response = await fetch('/api/ai/generate-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                patient_id: patientId,
                content_type: contentType,
                disciplines: disciplines
            })
        });
        
        const result = await response.json();
        
        // Display preview
        const previewElement = document.getElementById(`${contentType.replace('_', '-')}-preview`);
        if (previewElement) {
            previewElement.innerHTML = `
                <div class="ai-content">
                    <div class="content-source">
                        <small>Source: ${result.source} | Generated: ${new Date(result.generated_at).toLocaleString()}</small>
                    </div>
                    <div class="content-text">
                        ${result.content}
                    </div>
                </div>
            `;
        }
        
    } catch (error) {
        console.error(`Error generating ${contentType} preview:`, error);
    }
}

// Form submission
async function createReport() {
    if (reportRequestState.currentStep !== 2) {
        goToStep(2);
        return;
    }
    
    const formData = collectFormData();
    
    try {
        const url = reportRequestState.isEditing 
            ? `/api/reports/${reportRequestState.editingReportId}` 
            : '/api/reports';
        
        const method = reportRequestState.isEditing ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const result = await response.json();
            
            const successMessage = reportRequestState.isEditing 
                ? 'Report updated successfully' 
                : 'Report created successfully';
            
            showNotification(successMessage, 'success');
            
            // Show toast notification if available
            if (typeof showToastNotification === 'function') {
                showToastNotification({
                    title: reportRequestState.isEditing ? 'Report Updated' : 'Report Created',
                    message: `Report "${formData.title}" has been ${reportRequestState.isEditing ? 'updated' : 'created'} successfully`,
                    type: 'success'
                });
            }
            
            // Trigger custom events for other systems
            const eventType = reportRequestState.isEditing ? 'reportUpdated' : 'reportCreated';
            document.dispatchEvent(new CustomEvent(eventType, {
                detail: {
                    id: result.id,
                    title: formData.title,
                    patient_id: formData.patient_id,
                    assigned_therapist_ids: formData.assigned_therapist_ids
                }
            }));
            
            closeReportRequestModal();
            
            // Refresh dashboard widgets
            if (typeof loadDashboardData === 'function') {
                loadDashboardData();
            }
            
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save report');
        }
        
    } catch (error) {
        console.error('Error creating report:', error);
        showNotification(error.message, 'error');
    }
}

function collectFormData() {
    const disciplines = getSelectedDisciplines();
    const assignedTherapists = getSelectedTherapists();
    
    return {
        patient_id: document.getElementById('report-patient-select').value,
        report_type: document.getElementById('report-type-select').value,
        template_id: parseInt(document.getElementById('report-template-select').value),
        title: document.getElementById('report-title-input').value,
        assigned_therapist_ids: assignedTherapists,
        disciplines: disciplines,
        priority: parseInt(document.getElementById('report-priority').value),
        deadline_date: document.getElementById('report-deadline').value || null,
        generate_ai_content: document.getElementById('generate-medical-history').checked || 
                           document.getElementById('generate-treatment-summary').checked
    };
}

function getSelectedDisciplines() {
    const checkboxes = document.querySelectorAll('input[name="disciplines"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function getSelectedTherapists() {
    const select = document.getElementById('assigned-therapists');
    return Array.from(select.selectedOptions).map(option => option.value);
}

// Utility functions
function resetReportRequestForm() {
    reportRequestState = {
        currentStep: 1,
        workflowType: null,
        selectedPatient: null,
        selectedTemplate: null,
        aiContentOptions: {
            generateMedicalHistory: true,
            generateTreatmentSummary: true,
            generateOutcomeAnalysis: false
        },
        isEditing: false,
        editingReportId: null
    };
    
    document.getElementById('report-request-form').reset();
    goToStep(1);
}

function getCurrentUserId() {
    // This would typically come from session/auth context
    return window.currentUser?.user_id || localStorage.getItem('user_id');
}

// Patient search functions
function openReportPatientSearch() {
    document.getElementById('report-patient-search-modal').style.display = 'flex';
    document.getElementById('report-patient-search-input').focus();
}

function closeReportPatientSearch() {
    document.getElementById('report-patient-search-modal').style.display = 'none';
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Modal controls
    document.getElementById('close-report-modal')?.addEventListener('click', closeReportRequestModal);
    document.getElementById('report-cancel-button')?.addEventListener('click', closeReportRequestModal);
    document.getElementById('report-request-modal-backdrop')?.addEventListener('click', closeReportRequestModal);
    
    // Navigation buttons
    document.getElementById('report-continue-button')?.addEventListener('click', () => goToStep(2));
    document.getElementById('report-back-button')?.addEventListener('click', () => goToStep(1));
    document.getElementById('create-report-button')?.addEventListener('click', createReport);
    document.getElementById('preview-ai-content-button')?.addEventListener('click', previewAIContent);
    
    // Form validation
    const formInputs = [
        'report-patient-select', 'report-type-select', 'report-template-select', 
        'report-title-input', 'assigned-therapists'
    ];
    
    formInputs.forEach(inputId => {
        document.getElementById(inputId)?.addEventListener('change', validateCurrentStep);
    });
    
    // Discipline checkboxes
    document.querySelectorAll('input[name="disciplines"]').forEach(checkbox => {
        checkbox.addEventListener('change', validateCurrentStep);
    });
    
    // Report type change handler
    document.getElementById('report-type-select')?.addEventListener('change', function() {
        // Filter templates based on selected type
        filterTemplatesByType(this.value);
    });
});

function filterTemplatesByType(reportType) {
    const templateSelect = document.getElementById('report-template-select');
    const options = templateSelect.querySelectorAll('option');
    
    options.forEach(option => {
        if (option.value === '') {
            option.style.display = 'block';
            return;
        }
        
        const templateType = option.getAttribute('data-type');
        if (!reportType || templateType === reportType) {
            option.style.display = 'block';
        } else {
            option.style.display = 'none';
        }
    });
    
    // Reset template selection if current selection is now hidden
    if (templateSelect.value && templateSelect.options[templateSelect.selectedIndex].style.display === 'none') {
        templateSelect.value = '';
    }
}

// Simple notification utility
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background-color: ${type === 'error' ? '#f44336' : type === 'success' ? '#4caf50' : type === 'warning' ? '#ff9800' : '#2196f3'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        font-size: 0.9rem;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Remove after delay
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

// Discipline Selector Integration Functions
function openDisciplineSelectorForReport() {
    const patientId = reportRequestState.selectedPatient?.id;
    const currentlySelected = reportRequestState.selectedDisciplines || [];
    
    if (typeof openDisciplineSelector === 'function') {
        openDisciplineSelector(patientId, currentlySelected, function(selectedDisciplines) {
            // Update state
            reportRequestState.selectedDisciplines = selectedDisciplines.map(d => d.id);
            reportRequestState.selectedDisciplineDetails = selectedDisciplines;
            
            // Update preview
            updateDisciplinePreview(selectedDisciplines);
            
            showNotification(`Selected ${selectedDisciplines.length} disciplines`, 'success');
        });
    } else {
        showNotification('Discipline selector not available', 'error');
    }
}

function autoDetectDisciplinesForReport() {
    const patientId = reportRequestState.selectedPatient?.id;
    
    if (!patientId) {
        showNotification('Please select a patient first', 'warning');
        return;
    }
    
    if (typeof autoDetectDisciplines === 'function') {
        autoDetectDisciplines(patientId).then(function(detectedDisciplines) {
            if (detectedDisciplines && detectedDisciplines.length > 0) {
                // Open discipline selector with pre-selected disciplines
                openDisciplineSelectorForReport();
            }
        });
    } else {
        showNotification('Auto-detection not available', 'error');
    }
}

function updateDisciplinePreview(selectedDisciplines) {
    const preview = document.getElementById('report-disciplines-preview');
    if (!preview) return;
    
    if (!selectedDisciplines || selectedDisciplines.length === 0) {
        preview.innerHTML = '<p class="empty-preview">No disciplines selected. Click "Select Disciplines" to choose.</p>';
        return;
    }
    
    const html = selectedDisciplines.map(discipline => 
        `<span class="preview-item">${discipline.name}${discipline.autoDetected ? ' 🤖' : ''}</span>`
    ).join('');
    
    preview.innerHTML = html;
}

// Override the existing getSelectedDisciplines function to use new state
function getSelectedDisciplines() {
    if (reportRequestState.selectedDisciplines) {
        return reportRequestState.selectedDisciplines;
    }
    
    // Fallback to original checkbox method for backwards compatibility
    const checkboxes = document.querySelectorAll('input[name="disciplines"]:checked');
    return Array.from(checkboxes).map(checkbox => checkbox.value);
}

// Export functions for global use
// Only set global if wizard version doesn't exist (for compatibility)
if (!window.openReportRequestModal) {
    window.openReportRequestModal = openReportRequestModal;
}
window.closeReportRequestModal = closeReportRequestModal;
window.generateReportTitle = generateReportTitle;
window.setDeadline = setDeadline;
window.autoDetectDisciplines = autoDetectDisciplines;
window.openReportPatientSearch = openReportPatientSearch;
window.closeReportPatientSearch = closeReportPatientSearch;
window.showNotification = showNotification;
window.openDisciplineSelectorForReport = openDisciplineSelectorForReport;
window.autoDetectDisciplinesForReport = autoDetectDisciplinesForReport;