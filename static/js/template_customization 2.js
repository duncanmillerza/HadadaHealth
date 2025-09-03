/**
 * Template Customization System for HadadaHealth
 * 
 * Provides admin/manager interface for creating, editing, and managing
 * custom report templates with field type support and validation.
 */

class TemplateCustomization {
    constructor() {
        this.currentTemplate = null;
        this.fieldsSchema = {};
        this.sectionOrder = [];
        this.supportedFieldTypes = {
            'auto_populated': {
                name: 'Auto-populated Data',
                icon: 'fas fa-user',
                description: 'Automatically filled patient information',
                config: ['fields']
            },
            'ai_generated_paragraph': {
                name: 'AI Generated Content',
                icon: 'fas fa-robot',
                description: 'AI-generated content from patient data',
                config: ['ai_source', 'editable']
            },
            'rich_text': {
                name: 'Rich Text Editor',
                icon: 'fas fa-edit',
                description: 'Rich text input with formatting',
                config: ['placeholder', 'min_length', 'max_length']
            },
            'paragraph': {
                name: 'Simple Paragraph',
                icon: 'fas fa-paragraph',
                description: 'Simple text paragraph input',
                config: ['placeholder', 'min_length', 'max_length']
            },
            'multiple_choice': {
                name: 'Multiple Choice',
                icon: 'fas fa-list-ul',
                description: 'Single selection from predefined options',
                config: ['options', 'default']
            },
            'checklist': {
                name: 'Checklist',
                icon: 'fas fa-check-square',
                description: 'Multiple selection checklist',
                config: ['options', 'min_selections', 'max_selections']
            },
            'structured_table': {
                name: 'Data Table',
                icon: 'fas fa-table',
                description: 'Structured data table with columns',
                config: ['columns', 'min_rows', 'max_rows']
            },
            'digital_signature': {
                name: 'Digital Signature',
                icon: 'fas fa-signature',
                description: 'Digital signature capture',
                config: ['capture_credentials', 'signature_type']
            },
            'date_picker': {
                name: 'Date Picker',
                icon: 'fas fa-calendar',
                description: 'Date selection input',
                config: ['date_format', 'min_date', 'max_date']
            },
            'number_input': {
                name: 'Number Input',
                icon: 'fas fa-hashtag',
                description: 'Numeric input with validation',
                config: ['min_value', 'max_value', 'decimal_places']
            }
        };
        
        this.initializeEventListeners();
        this.loadAvailableTemplates();
    }

    /**
     * Initialize event listeners for the template customization interface
     */
    initializeEventListeners() {
        // Add field button
        document.getElementById('addFieldBtn').addEventListener('click', () => {
            this.addField();
        });

        // Save template button
        document.getElementById('saveTemplateBtn').addEventListener('click', () => {
            this.saveTemplate();
        });

        // Save and approve button
        document.getElementById('saveAndApproveBtn').addEventListener('click', () => {
            this.saveAndApproveTemplate();
        });

        // Load template button
        document.getElementById('loadTemplateBtn').addEventListener('click', () => {
            this.loadSelectedTemplate();
        });

        // Refresh preview button
        document.getElementById('refreshPreviewBtn').addEventListener('click', () => {
            this.updatePreview();
        });

        // View history button
        document.getElementById('viewHistoryBtn').addEventListener('click', () => {
            this.viewTemplateHistory();
        });

        // Save field configuration
        document.getElementById('saveFieldConfigBtn').addEventListener('click', () => {
            this.saveFieldConfiguration();
        });

        // Tab change handlers
        document.querySelectorAll('#templateTabs button[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (event) => {
                const targetTab = event.target.getAttribute('data-bs-target');
                if (targetTab === '#preview-template') {
                    this.updatePreview();
                }
            });
        });

        // Form validation on input
        document.getElementById('templateName').addEventListener('input', () => {
            this.validateTemplate();
        });

        document.getElementById('templateType').addEventListener('change', () => {
            this.validateTemplate();
        });
    }

    /**
     * Add a new field to the template
     */
    addField() {
        const fieldType = document.getElementById('fieldTypeSelect').value;
        const fieldLabel = document.getElementById('fieldLabelInput').value.trim();

        if (!fieldType || !fieldLabel) {
            this.showAlert('Please select a field type and enter a label', 'warning');
            return;
        }

        // Generate unique field name
        const fieldName = this.generateFieldName(fieldLabel);

        // Create basic field configuration
        const fieldConfig = {
            type: fieldType,
            label: fieldLabel,
            required: false,
            description: `${fieldLabel} field`
        };

        // Add field to schema
        this.fieldsSchema[fieldName] = fieldConfig;
        this.sectionOrder.push(fieldName);

        // Update UI
        this.renderFieldList();
        this.validateTemplate();

        // Clear inputs
        document.getElementById('fieldTypeSelect').value = '';
        document.getElementById('fieldLabelInput').value = '';

        this.showAlert(`Field "${fieldLabel}" added successfully`, 'success');
    }

    /**
     * Generate a field name from label
     */
    generateFieldName(label) {
        let baseName = label.toLowerCase()
            .replace(/[^a-z0-9\s]/g, '')
            .replace(/\s+/g, '_')
            .substring(0, 30);

        let fieldName = baseName;
        let counter = 1;

        // Ensure uniqueness
        while (this.fieldsSchema.hasOwnProperty(fieldName)) {
            fieldName = `${baseName}_${counter}`;
            counter++;
        }

        return fieldName;
    }

    /**
     * Render the field list in the UI
     */
    renderFieldList() {
        const fieldList = document.getElementById('fieldList');
        
        if (this.sectionOrder.length === 0) {
            fieldList.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    No fields added yet. Click "Add Field" to start building your template.
                </div>
            `;
            return;
        }

        const fieldsHtml = this.sectionOrder.map((fieldName, index) => {
            const field = this.fieldsSchema[fieldName];
            const fieldType = this.supportedFieldTypes[field.type];
            
            return `
                <div class="field-item card mb-2" data-field-name="${fieldName}">
                    <div class="card-body py-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="field-info">
                                <i class="${fieldType.icon} me-2 text-primary"></i>
                                <strong>${field.label}</strong>
                                <span class="badge bg-secondary ms-2">${fieldType.name}</span>
                                ${field.required ? '<span class="badge bg-warning ms-1">Required</span>' : ''}
                            </div>
                            <div class="field-actions">
                                <button class="btn btn-sm btn-outline-secondary me-1" onclick="templateCustomization.moveField('${fieldName}', -1)" ${index === 0 ? 'disabled' : ''}>
                                    <i class="fas fa-arrow-up"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-secondary me-1" onclick="templateCustomization.moveField('${fieldName}', 1)" ${index === this.sectionOrder.length - 1 ? 'disabled' : ''}>
                                    <i class="fas fa-arrow-down"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-primary me-1" onclick="templateCustomization.editField('${fieldName}')">
                                    <i class="fas fa-cog"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="templateCustomization.removeField('${fieldName}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        fieldList.innerHTML = fieldsHtml;
    }

    /**
     * Move field up or down in the order
     */
    moveField(fieldName, direction) {
        const currentIndex = this.sectionOrder.indexOf(fieldName);
        const newIndex = currentIndex + direction;

        if (newIndex < 0 || newIndex >= this.sectionOrder.length) {
            return;
        }

        // Swap positions
        [this.sectionOrder[currentIndex], this.sectionOrder[newIndex]] = 
        [this.sectionOrder[newIndex], this.sectionOrder[currentIndex]];

        this.renderFieldList();
        this.validateTemplate();
    }

    /**
     * Edit field configuration
     */
    editField(fieldName) {
        const field = this.fieldsSchema[fieldName];
        const fieldType = this.supportedFieldTypes[field.type];

        // Generate field configuration form
        const configForm = this.generateFieldConfigForm(field, fieldType);
        
        document.getElementById('fieldConfigForm').innerHTML = configForm;
        document.getElementById('fieldConfigModalLabel').textContent = `Configure: ${field.label}`;
        
        // Store current field being edited
        this.currentEditingField = fieldName;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('fieldConfigModal'));
        modal.show();
    }

    /**
     * Generate field configuration form HTML
     */
    generateFieldConfigForm(field, fieldType) {
        let formHtml = `
            <div class="mb-3">
                <label class="form-label">Field Label <span class="text-danger">*</span></label>
                <input type="text" class="form-control" id="configFieldLabel" value="${field.label}" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Description</label>
                <textarea class="form-control" id="configFieldDescription" rows="2">${field.description || ''}</textarea>
            </div>
            <div class="mb-3">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="configFieldRequired" ${field.required ? 'checked' : ''}>
                    <label class="form-check-label" for="configFieldRequired">Required Field</label>
                </div>
            </div>
        `;

        // Add type-specific configuration
        if (fieldType.config.includes('placeholder')) {
            formHtml += `
                <div class="mb-3">
                    <label class="form-label">Placeholder Text</label>
                    <input type="text" class="form-control" id="configFieldPlaceholder" value="${field.placeholder || ''}">
                </div>
            `;
        }

        if (fieldType.config.includes('options')) {
            const options = field.options || [];
            formHtml += `
                <div class="mb-3">
                    <label class="form-label">Options <span class="text-danger">*</span></label>
                    <div class="options-container" id="optionsContainer">
                        ${options.map((option, index) => `
                            <div class="input-group mb-2">
                                <input type="text" class="form-control option-input" value="${option}" placeholder="Option ${index + 1}">
                                <button class="btn btn-outline-danger" type="button" onclick="this.parentElement.remove()">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        `).join('')}
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="templateCustomization.addOption()">
                        <i class="fas fa-plus me-1"></i>Add Option
                    </button>
                </div>
            `;
        }

        if (fieldType.config.includes('columns')) {
            const columns = field.columns || [];
            formHtml += `
                <div class="mb-3">
                    <label class="form-label">Table Columns <span class="text-danger">*</span></label>
                    <div class="columns-container" id="columnsContainer">
                        ${columns.map((column, index) => `
                            <div class="input-group mb-2">
                                <input type="text" class="form-control column-input" value="${column}" placeholder="Column ${index + 1}">
                                <button class="btn btn-outline-danger" type="button" onclick="this.parentElement.remove()">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        `).join('')}
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="templateCustomization.addColumn()">
                        <i class="fas fa-plus me-1"></i>Add Column
                    </button>
                </div>
            `;
        }

        if (fieldType.config.includes('ai_source')) {
            formHtml += `
                <div class="mb-3">
                    <label class="form-label">AI Content Source <span class="text-danger">*</span></label>
                    <select class="form-select" id="configAiSource">
                        <option value="treatment_notes" ${field.ai_source === 'treatment_notes' ? 'selected' : ''}>Treatment Notes</option>
                        <option value="treatment_progress" ${field.ai_source === 'treatment_progress' ? 'selected' : ''}>Treatment Progress</option>
                        <option value="assessment_summary" ${field.ai_source === 'assessment_summary' ? 'selected' : ''}>Assessment Summary</option>
                        <option value="outcome_summary" ${field.ai_source === 'outcome_summary' ? 'selected' : ''}>Outcome Summary</option>
                    </select>
                </div>
            `;
        }

        if (fieldType.config.includes('editable')) {
            formHtml += `
                <div class="mb-3">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="configFieldEditable" ${field.editable ? 'checked' : ''}>
                        <label class="form-check-label" for="configFieldEditable">Allow editing of AI-generated content</label>
                    </div>
                </div>
            `;
        }

        return formHtml;
    }

    /**
     * Add option to multiple choice configuration
     */
    addOption() {
        const container = document.getElementById('optionsContainer');
        const optionCount = container.children.length + 1;
        const optionHtml = `
            <div class="input-group mb-2">
                <input type="text" class="form-control option-input" placeholder="Option ${optionCount}">
                <button class="btn btn-outline-danger" type="button" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', optionHtml);
    }

    /**
     * Add column to table configuration
     */
    addColumn() {
        const container = document.getElementById('columnsContainer');
        const columnCount = container.children.length + 1;
        const columnHtml = `
            <div class="input-group mb-2">
                <input type="text" class="form-control column-input" placeholder="Column ${columnCount}">
                <button class="btn btn-outline-danger" type="button" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', columnHtml);
    }

    /**
     * Save field configuration
     */
    saveFieldConfiguration() {
        if (!this.currentEditingField) return;

        const field = this.fieldsSchema[this.currentEditingField];
        
        // Update basic properties
        field.label = document.getElementById('configFieldLabel').value.trim();
        field.description = document.getElementById('configFieldDescription').value.trim();
        field.required = document.getElementById('configFieldRequired').checked;

        // Update type-specific properties
        const placeholderInput = document.getElementById('configFieldPlaceholder');
        if (placeholderInput) {
            field.placeholder = placeholderInput.value.trim();
        }

        const aiSourceSelect = document.getElementById('configAiSource');
        if (aiSourceSelect) {
            field.ai_source = aiSourceSelect.value;
        }

        const editableCheckbox = document.getElementById('configFieldEditable');
        if (editableCheckbox) {
            field.editable = editableCheckbox.checked;
        }

        // Handle options for multiple choice
        const optionInputs = document.querySelectorAll('.option-input');
        if (optionInputs.length > 0) {
            field.options = Array.from(optionInputs)
                .map(input => input.value.trim())
                .filter(option => option.length > 0);
        }

        // Handle columns for tables
        const columnInputs = document.querySelectorAll('.column-input');
        if (columnInputs.length > 0) {
            field.columns = Array.from(columnInputs)
                .map(input => input.value.trim())
                .filter(column => column.length > 0);
        }

        // Update UI
        this.renderFieldList();
        this.validateTemplate();

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('fieldConfigModal'));
        modal.hide();

        this.showAlert(`Field "${field.label}" updated successfully`, 'success');
    }

    /**
     * Remove field from template
     */
    removeField(fieldName) {
        if (!confirm('Are you sure you want to remove this field?')) {
            return;
        }

        delete this.fieldsSchema[fieldName];
        this.sectionOrder = this.sectionOrder.filter(name => name !== fieldName);

        this.renderFieldList();
        this.validateTemplate();

        this.showAlert('Field removed successfully', 'success');
    }

    /**
     * Validate current template configuration
     */
    validateTemplate() {
        const name = document.getElementById('templateName').value.trim();
        const type = document.getElementById('templateType').value;
        
        let isValid = true;
        let errors = [];

        // Basic validation
        if (!name) {
            errors.push('Template name is required');
            isValid = false;
        }

        if (!type) {
            errors.push('Template type is required');
            isValid = false;
        }

        if (Object.keys(this.fieldsSchema).length === 0) {
            errors.push('At least one field is required');
            isValid = false;
        }

        // Field-specific validation
        for (const [fieldName, field] of Object.entries(this.fieldsSchema)) {
            if (field.type === 'multiple_choice' && (!field.options || field.options.length === 0)) {
                errors.push(`Multiple choice field "${field.label}" must have options`);
                isValid = false;
            }

            if (field.type === 'structured_table' && (!field.columns || field.columns.length === 0)) {
                errors.push(`Table field "${field.label}" must have columns`);
                isValid = false;
            }

            if (field.type === 'ai_generated_paragraph' && !field.ai_source) {
                errors.push(`AI field "${field.label}" must have an AI source`);
                isValid = false;
            }
        }

        // Update UI
        const saveBtn = document.getElementById('saveTemplateBtn');
        const approveBtn = document.getElementById('saveAndApproveBtn');
        const validationStatus = document.getElementById('validationStatus');
        const validBadge = document.getElementById('validBadge');
        const invalidBadge = document.getElementById('invalidBadge');

        saveBtn.disabled = !isValid;
        approveBtn.disabled = !isValid;

        if (isValid) {
            validBadge.style.display = 'inline';
            invalidBadge.style.display = 'none';
            validationStatus.className = 'd-block';
        } else {
            validBadge.style.display = 'none';
            invalidBadge.style.display = 'inline';
            invalidBadge.title = errors.join(', ');
            validationStatus.className = 'd-block';
        }

        return { valid: isValid, errors };
    }

    /**
     * Save template
     */
    async saveTemplate() {
        const validation = this.validateTemplate();
        if (!validation.valid) {
            this.showAlert('Please fix validation errors before saving', 'danger');
            return;
        }

        const templateData = {
            name: document.getElementById('templateName').value.trim(),
            description: document.getElementById('templateDescription').value.trim(),
            template_type: document.getElementById('templateType').value,
            practice_id: this.getCurrentPracticeId(),
            fields_schema: this.fieldsSchema,
            section_order: this.sectionOrder,
            created_by_user_id: this.getCurrentUserId()
        };

        try {
            const response = await fetch('/api/templates/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(templateData)
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert('Template saved successfully!', 'success');
                this.loadAvailableTemplates();
                // Switch to edit tab
                document.getElementById('edit-tab').click();
            } else {
                this.showAlert(`Error saving template: ${result.error}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error saving template: ${error.message}`, 'danger');
        }
    }

    /**
     * Save and approve template
     */
    async saveAndApproveTemplate() {
        // First save the template
        await this.saveTemplate();
        
        // Then approve it (implementation would depend on approval workflow)
        this.showAlert('Template saved and approved for production use!', 'success');
    }

    /**
     * Load available templates for editing
     */
    async loadAvailableTemplates() {
        try {
            const response = await fetch('/api/templates');
            const templates = await response.json();

            const select = document.getElementById('templateSelect');
            select.innerHTML = '<option value="">Choose a template...</option>';

            templates.forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = `${template.name} (${template.template_type})`;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading templates:', error);
        }
    }

    /**
     * Update template preview
     */
    async updatePreview() {
        const validation = this.validateTemplate();
        const previewContainer = document.getElementById('templatePreviewContent');
        const previewPlaceholder = document.querySelector('.preview-placeholder');

        if (!validation.valid || Object.keys(this.fieldsSchema).length === 0) {
            previewContainer.style.display = 'none';
            previewPlaceholder.style.display = 'block';
            return;
        }

        const templateData = {
            name: document.getElementById('templateName').value.trim(),
            fields_schema: this.fieldsSchema,
            section_order: this.sectionOrder
        };

        try {
            const response = await fetch('/api/templates/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(templateData)
            });

            const result = await response.json();

            if (result.success) {
                previewContainer.innerHTML = result.preview_html;
                previewContainer.style.display = 'block';
                previewPlaceholder.style.display = 'none';
            } else {
                this.showAlert(`Error generating preview: ${result.error}`, 'warning');
            }
        } catch (error) {
            this.showAlert(`Error generating preview: ${error.message}`, 'warning');
        }
    }

    /**
     * Utility functions
     */
    showAlert(message, type) {
        // Simple alert implementation - could be enhanced with toast notifications
        const alertClass = {
            'success': 'alert-success',
            'danger': 'alert-danger', 
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';

        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;

        // Insert at top of modal body
        const modalBody = document.querySelector('#templateCustomizationModal .modal-body');
        modalBody.insertAdjacentHTML('afterbegin', alertHtml);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = modalBody.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }

    getCurrentPracticeId() {
        // Implementation depends on how practice context is managed
        return window.currentUser?.practice_id || null;
    }

    getCurrentUserId() {
        // Implementation depends on how user context is managed  
        return window.currentUser?.user_id || 'system';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.templateCustomization = new TemplateCustomization();
});

/**
 * Helper function to open template customization modal
 */
async function openTemplateCustomization() {
    console.log('🔧 Opening template customization modal...');
    
    try {
        // Load modal HTML if not already loaded
        if (!document.getElementById('templateCustomizationModal')) {
            console.log('📥 Loading template customization modal HTML...');
            const response = await fetch('/static/fragments/template_customization_modal.html');
            const modalHtml = await response.text();
            
            const container = document.getElementById('template-customization-modal-container');
            if (!container) {
                console.error('❌ Modal container not found');
                alert('Error: Modal container not found. Please refresh the page.');
                return;
            }
            container.innerHTML = modalHtml;
            
            console.log('✅ Template customization modal HTML loaded');
        }
        
        // Check if Bootstrap is available
        if (typeof bootstrap === 'undefined') {
            console.error('❌ Bootstrap not available, trying alternative approach...');
            
            // Try jQuery approach if available
            if (typeof $ !== 'undefined') {
                $('#templateCustomizationModal').modal('show');
                console.log('✅ Opened modal using jQuery');
                return;
            }
            
            // Manual modal display as last resort
            const modalElement = document.getElementById('templateCustomizationModal');
            if (modalElement) {
                modalElement.style.display = 'block';
                modalElement.classList.add('show');
                modalElement.setAttribute('aria-modal', 'true');
                modalElement.setAttribute('role', 'dialog');
                
                // Add backdrop
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                backdrop.id = 'template-modal-backdrop';
                document.body.appendChild(backdrop);
                
                // Add close functionality
                const closeButtons = modalElement.querySelectorAll('[data-bs-dismiss="modal"], .btn-close');
                closeButtons.forEach(btn => {
                    btn.onclick = () => {
                        modalElement.style.display = 'none';
                        modalElement.classList.remove('show');
                        const backdrop = document.getElementById('template-modal-backdrop');
                        if (backdrop) backdrop.remove();
                    };
                });
                
                console.log('✅ Opened modal using manual approach');
                return;
            }
            
            alert('Error: Could not open template customization modal. Bootstrap framework not available.');
            return;
        }
        
        // Open the modal using Bootstrap
        const modalElement = document.getElementById('templateCustomizationModal');
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            console.log('✅ Template customization modal opened using Bootstrap');
        } else {
            console.error('❌ Template customization modal element not found');
            alert('Error: Could not find template customization modal.');
        }
        
    } catch (error) {
        console.error('❌ Error loading template customization:', error);
        alert('Error loading template customization. Please check the console for details.');
    }
}