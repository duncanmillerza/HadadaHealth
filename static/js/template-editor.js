/**
 * Structured Template Editor
 * Handles dynamic form generation, auto-population, draft saving, and section deletion
 */

class TemplateEditor {
    constructor(instanceId) {
        this.instanceId = instanceId;
        this.instance = null;
        this.template = null;
        this.isDirty = false;
        this.autoSaveTimer = null;
        this.deletedSections = [];
        
        this.initializeEditor();
    }
    
    async initializeEditor() {
        try {
            // Load template instance data
            await this.loadInstance();
            
            // Initialize UI elements
            this.initializeElements();
            
            // Generate dynamic form
            this.generateDynamicForm();
            
            // Set up auto-save
            this.setupAutoSave();
            
            // Bind events
            this.bindEvents();
            
            console.log('✅ Template Editor initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize template editor:', error);
            this.showError('Failed to load template');
        }
    }
    
    async loadInstance() {
        const response = await fetch(`/api/templates/instances/${this.instanceId}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Failed to load template instance');
        }
        
        this.instance = await response.json();
        this.deletedSections = this.instance.sections_deleted || [];
        
        // Also load the template structure
        const templateResponse = await fetch(`/api/templates/${this.instance.template_id}`, {
            credentials: 'include'
        });
        
        if (templateResponse.ok) {
            this.template = await templateResponse.json();
        }
        
        console.log('📄 Loaded template instance:', this.instance);
    }
    
    initializeElements() {
        this.editorContainer = document.getElementById('template-editor-container');
        this.headerTitle = document.getElementById('template-header-title');
        this.headerPatient = document.getElementById('template-header-patient');
        this.headerStatus = document.getElementById('template-header-status');
        this.saveBtn = document.getElementById('save-template-btn');
        this.completeBtn = document.getElementById('complete-template-btn');
        this.exportBtn = document.getElementById('export-template-btn');
        this.statusIndicator = document.getElementById('save-status');
        
        // Update header information
        if (this.headerTitle) this.headerTitle.textContent = this.instance.title;
        if (this.headerPatient) this.headerPatient.textContent = this.instance.patient_name;
        if (this.headerStatus) this.updateStatusDisplay();
    }
    
    generateDynamicForm() {
        if (!this.template || !this.editorContainer) return;
        
        const sections = this.template.template_structure.sections || [];
        const instanceData = this.instance.instance_data || {};
        
        this.editorContainer.innerHTML = sections
            .filter(section => !this.deletedSections.includes(section.id))
            .map(section => this.renderSection(section, instanceData))
            .join('');
        
        // Initialize section-specific functionality
        this.initializeSectionFeatures();
    }
    
    renderSection(section, data) {
        // Handle both flat data structure (auto-populated) and section-organized data
        const sectionData = data[section.id] || data; // Fallback to flat data if section data not found
        const canDelete = section.deletable !== false;
        
        return `
            <div class="template-section" data-section-id="${section.id}">
                <div class="section-header">
                    <h3 class="section-title">${section.title}</h3>
                    ${canDelete ? `
                        <button type="button" class="section-delete-btn" title="Delete Section">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    ` : ''}
                </div>
                <div class="section-content">
                    ${this.renderSectionContent(section, sectionData)}
                </div>
            </div>
        `;
    }
    
    renderSectionContent(section, data) {
        switch (section.type) {
            case 'form_section':
                return this.renderFormFields(section.fields || [], data);
            case 'ai_generated_section':
                return this.renderAISection(section, data);
            case 'outcomes_table':
                return this.renderOutcomesTable(section, data);
            case 'assessment_tables':
                return this.renderAssessmentTables(section, data);
            case 'goals_section':
                return this.renderGoalsSection(section.fields || [], data);
            case 'treatment_grid':
                return this.renderTreatmentGrid(section, data);
            default:
                return this.renderFormFields(section.fields || [], data);
        }
    }
    
    renderFormFields(fields, data) {
        return fields.map(field => this.renderField(field, data[field.id] || '')).join('');
    }
    
    renderField(field, value) {
        const isReadonly = field.readonly || field.auto_populate;
        const fieldClass = `form-field ${field.type}-field ${isReadonly ? 'readonly' : ''}`;
        
        let input = '';
        switch (field.type) {
            case 'text':
            case 'tel':
                input = `<input type="${field.type}" id="${field.id}" name="${field.id}" 
                        value="${this.escapeHtml(value)}" ${isReadonly ? 'readonly' : ''} 
                        ${field.required ? 'required' : ''} />`;
                break;
            case 'date':
                input = `<input type="date" id="${field.id}" name="${field.id}" 
                        value="${value}" ${isReadonly ? 'readonly' : ''} 
                        ${field.required ? 'required' : ''} />`;
                break;
            case 'textarea':
                input = `<textarea id="${field.id}" name="${field.id}" rows="4" 
                        ${isReadonly ? 'readonly' : ''} ${field.required ? 'required' : ''}
                        placeholder="${field.placeholder || ''}">${this.escapeHtml(value)}</textarea>`;
                break;
            case 'rich_textarea':
                input = `<div class="rich-editor-container">
                    <textarea id="${field.id}" name="${field.id}" rows="6" 
                            ${isReadonly ? 'readonly' : ''} ${field.required ? 'required' : ''}
                            class="rich-textarea">${this.escapeHtml(value)}</textarea>
                    ${field.ai_generated ? `
                        <div class="ai-buttons-group mt-2">
                            <button type="button" class="btn btn-sm btn-secondary ai-generate-btn" data-field-id="${field.id}">
                                <i class="fas fa-magic"></i> Generate AI Content
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-secondary ai-regenerate-btn" data-field-id="${field.id}">
                                <i class="fas fa-redo"></i> Regenerate from Notes
                            </button>
                        </div>
                    ` : ''}
                </div>`;
                break;
            default:
                input = `<input type="text" id="${field.id}" name="${field.id}" 
                        value="${this.escapeHtml(value)}" ${isReadonly ? 'readonly' : ''} />`;
        }
        
        return `
            <div class="${fieldClass}">
                <label for="${field.id}">
                    ${field.label}
                    ${field.required ? '<span class="required">*</span>' : ''}
                </label>
                ${input}
                ${field.help ? `<div class="field-help">${field.help}</div>` : ''}
            </div>
        `;
    }
    
    renderAISection(section, data) {
        const field = section.fields[0];
        const value = data[field.id] || '';
        
        return `
            <div class="ai-section">
                <div class="ai-section-header">
                    <div class="ai-indicator">
                        <i class="fas fa-robot"></i>
                        <span>AI Generated Content</span>
                    </div>
                    <button type="button" class="ai-regenerate-btn" data-section-id="${section.id}" data-field-id="${field.id}">
                        <i class="fas fa-sync-alt"></i> Regenerate
                    </button>
                </div>
                <div class="ai-content-container">
                    <textarea id="${field.id}" name="${field.id}" rows="8" class="ai-content-field">${this.escapeHtml(value)}</textarea>
                </div>
            </div>
        `;
    }
    
    renderAssessmentTables(section, data) {
        if (!section.tables) return '';
        
        return section.tables.map(table => {
            const tableData = data[table.id] || {};
            
            if (table.columns && table.rows) {
                // Structured table
                return this.renderStructuredTable(table, tableData);
            } else if (table.fields) {
                // Field-based table
                return this.renderFieldTable(table, tableData);
            }
            
            return '';
        }).join('');
    }
    
    renderStructuredTable(table, data) {
        const headers = table.columns;
        const rowData = data.rows || table.rows.map(() => Array(headers.length).fill(''));
        
        return `
            <div class="assessment-table-container">
                <h4>${table.title}</h4>
                <div class="table-responsive">
                    <table class="assessment-table" data-table-id="${table.id}">
                        <thead>
                            <tr>
                                ${headers.map(header => `<th>${header}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${rowData.map((row, rowIndex) => `
                                <tr>
                                    ${row.map((cell, colIndex) => `
                                        <td>
                                            ${colIndex === 0 ? 
                                                `<strong>${table.rows ? table.rows[rowIndex]?.aspect || cell : cell}</strong>` :
                                                `<input type="text" value="${this.escapeHtml(cell)}" data-row="${rowIndex}" data-col="${colIndex}" />`
                                            }
                                        </td>
                                    `).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    renderFieldTable(table, data) {
        return `
            <div class="field-table">
                <h5>${table.title || 'Assessment'}</h5>
                <div class="table-responsive">
                    <table class="assessment-table">
                        <tbody>
                            ${table.fields.map(field => `
                                <tr>
                                    <th>${field.label}</th>
                                    <td>
                                        <textarea 
                                            id="${table.id}_${field.id}" 
                                            name="${table.id}_${field.id}" 
                                            rows="3"
                                            class="form-control"
                                        >${this.escapeHtml(data[field.id] || '')}</textarea>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    renderOutcomesTable(section, data) {
        if (!section.fields) return '';
        
        return `
            <div class="outcomes-table">
                <h4>Rehabilitation Outcomes Matrix</h4>
                <div class="table-responsive">
                    <table class="assessment-table">
                        <tbody>
                            ${section.fields.map(field => `
                                <tr>
                                    <th>${field.label}</th>
                                    <td>
                                        <textarea 
                                            id="${field.id}" 
                                            name="${field.id}" 
                                            rows="3"
                                            ${field.ai_generated ? 'class="ai-generatable"' : ''}
                                        >${this.escapeHtml(data[field.id] || '')}</textarea>
                                        ${field.ai_generated ? `
                                            <div class="ai-buttons-group mt-2">
                                                <button type="button" class="btn btn-sm btn-secondary ai-generate-btn" 
                                                        data-section-id="${section.id}" data-field-id="${field.id}">
                                                    <i class="fas fa-magic"></i> Generate AI Content
                                                </button>
                                                <button type="button" class="btn btn-sm btn-outline-secondary ai-regenerate-btn" 
                                                        data-section-id="${section.id}" data-field-id="${field.id}">
                                                    <i class="fas fa-redo"></i> Regenerate from Notes
                                                </button>
                                            </div>
                                        ` : ''}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    renderGoalsSection(fields, data) {
        return `
            <div class="goals-section">
                <h4>Goals Achievement Summary</h4>
                <div class="goals-grid">
                    ${fields.map(field => `
                        <div class="goal-item">
                            <label for="${field.id}" class="form-label">${field.label}</label>
                            <textarea 
                                id="${field.id}" 
                                name="${field.id}" 
                                rows="4"
                                class="form-control"
                            >${this.escapeHtml(data[field.id] || '')}</textarea>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    renderTreatmentGrid(section, data) {
        if (!section.grid) return '';
        
        const grid = section.grid;
        return `
            <div class="treatment-grid">
                <h4>Monthly Treatment Plan & Goals</h4>
                <div class="table-responsive">
                    <table class="treatment-table">
                        <thead>
                            <tr>
                                ${grid.columns.map(col => `<th>${col}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${grid.sections.map(gridSection => `
                                <tr class="section-header">
                                    <td colspan="${grid.columns.length}"><strong>${gridSection.title}</strong></td>
                                </tr>
                                ${Array(gridSection.rows).fill().map((_, rowIndex) => `
                                    <tr>
                                        ${grid.columns.map((col, colIndex) => `
                                            <td>
                                                ${colIndex === 0 ? 
                                                    `<input type="date" data-section="${gridSection.title}" data-row="${rowIndex}" data-col="${colIndex}" />` :
                                                    `<textarea rows="2" data-section="${gridSection.title}" data-row="${rowIndex}" data-col="${colIndex}">${this.escapeHtml(data[`${gridSection.title}_${rowIndex}_${colIndex}`] || '')}</textarea>`
                                                }
                                            </td>
                                        `).join('')}
                                    </tr>
                                `).join('')}
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    initializeSectionFeatures() {
        // Section deletion
        document.querySelectorAll('.section-delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const section = e.target.closest('.template-section');
                const sectionId = section.dataset.sectionId;
                this.deleteSection(sectionId);
            });
        });
        
        // AI generation buttons
        document.querySelectorAll('.ai-generate-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sectionId = e.target.dataset.sectionId || e.target.closest('.template-section')?.dataset.sectionId;
                const fieldId = e.target.dataset.fieldId;
                this.generateAIContent(sectionId, fieldId);
            });
        });
        
        // AI regeneration buttons
        document.querySelectorAll('.ai-regenerate-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sectionId = e.target.dataset.sectionId || e.target.closest('.template-section')?.dataset.sectionId;
                const fieldId = e.target.dataset.fieldId;
                this.regenerateAIContent(sectionId, fieldId);
            });
        });
        
        // Form field change events
        document.querySelectorAll('.template-section input, .template-section textarea, .template-section select').forEach(field => {
            field.addEventListener('input', () => {
                this.markDirty();
            });
        });
        
        // Assessment table inputs
        document.querySelectorAll('.assessment-table input').forEach(input => {
            input.addEventListener('input', () => {
                this.markDirty();
            });
        });
    }
    
    deleteSection(sectionId) {
        if (confirm('Are you sure you want to delete this section? This action cannot be undone.')) {
            const sectionElement = document.querySelector(`[data-section-id="${sectionId}"]`);
            if (sectionElement) {
                sectionElement.remove();
                this.deletedSections.push(sectionId);
                this.markDirty();
                this.showSuccess('Section deleted successfully');
            }
        }
    }
    
    async generateAIContent(sectionId, fieldId) {
        // Find the generate button that was clicked
        const btn = document.querySelector(`[data-section-id="${sectionId}"][data-field-id="${fieldId}"].ai-generate-btn`) || 
                   document.querySelector(`[data-field-id="${fieldId}"].ai-generate-btn`);
        const originalText = btn ? btn.innerHTML : 'Generate AI Content';
        
        try {
            if (btn) {
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
                btn.disabled = true;
            }
            
            const response = await fetch(`/api/templates/instances/${this.instanceId}/ai-generate/${sectionId}/${fieldId}`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('AI generation failed');
            }
            
            const result = await response.json();
            
            // Update the field with generated content - target form fields specifically
            console.log(`Looking for field with ID: ${fieldId}`);
            const fieldElement = document.querySelector(`input[name="${fieldId}"], textarea[name="${fieldId}"], input[id="${fieldId}"], textarea[id="${fieldId}"], select[name="${fieldId}"], select[id="${fieldId}"]`);
            console.log('Found field element:', fieldElement);
            
            if (fieldElement) {
                console.log('Field element tag:', fieldElement.tagName);
                console.log('Setting content:', result.content);
                
                if (fieldElement.tagName === 'TEXTAREA') {
                    fieldElement.value = result.content;
                } else if (fieldElement.tagName === 'INPUT') {
                    fieldElement.value = result.content;
                } else {
                    fieldElement.innerHTML = result.content;
                }
                
                // Trigger input event to mark as dirty
                fieldElement.dispatchEvent(new Event('input', { bubbles: true }));
                console.log('Content updated successfully');
            } else {
                console.warn(`Field element not found for fieldId: ${fieldId}`);
                console.log('Available elements with name attribute:', document.querySelectorAll('[name]'));
                console.log('Available elements with id attribute:', document.querySelectorAll('[id]'));
            }
            
            this.showSuccess('AI content generated successfully');
        } catch (error) {
            console.error('AI generation error:', error);
            this.showError('Failed to generate AI content');
        } finally {
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    }
    
    async regenerateAIContent(sectionId, fieldId) {
        // Find the regenerate button that was clicked
        const btn = document.querySelector(`[data-section-id="${sectionId}"][data-field-id="${fieldId}"].ai-regenerate-btn`) || 
                   document.querySelector(`[data-field-id="${fieldId}"].ai-regenerate-btn`);
        const originalText = btn ? btn.innerHTML : 'Regenerate from Notes';
        
        try {            
            if (btn) {
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Regenerating...';
                btn.disabled = true;
            }
            
            const response = await fetch(`/api/templates/instances/${this.instanceId}/ai-regenerate/${sectionId}/${fieldId}`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('AI regeneration failed');
            }
            
            const result = await response.json();
            
            // Update the field with the new content - target form fields specifically
            console.log(`Looking for field with ID: ${fieldId}`);
            const fieldElement = document.querySelector(`input[name="${fieldId}"], textarea[name="${fieldId}"], input[id="${fieldId}"], textarea[id="${fieldId}"], select[name="${fieldId}"], select[id="${fieldId}"]`);
            console.log('Found field element:', fieldElement);
            
            if (fieldElement) {
                console.log('Field element tag:', fieldElement.tagName);
                console.log('Full result object:', result);
                console.log('Result type:', typeof result);
                console.log('Result.content:', result.content);
                console.log('Result.content type:', typeof result.content);
                
                // Extract the actual content - handle nested response structure
                let actualContent;
                if (typeof result === 'string') {
                    actualContent = result;
                } else if (result.content && typeof result.content === 'string') {
                    // Direct content string
                    actualContent = result.content;
                } else if (result.content && result.content.content && typeof result.content.content === 'string') {
                    // Nested content structure: result.content.content
                    actualContent = result.content.content;
                } else if (typeof result === 'object' && result.content) {
                    // Fallback: try to extract content from object
                    actualContent = result.content.content || result.content;
                } else {
                    console.error('Unable to extract content from result:', result);
                    actualContent = 'Error: Unable to extract generated content';
                }
                
                // Clean up Markdown formatting for better display in textarea
                const cleanedContent = this.cleanMarkdownForTextarea(actualContent);
                console.log('Actual content to set:', cleanedContent);
                
                if (fieldElement.tagName === 'TEXTAREA') {
                    fieldElement.value = cleanedContent;
                } else if (fieldElement.tagName === 'INPUT') {
                    fieldElement.value = cleanedContent;
                } else {
                    fieldElement.innerHTML = cleanedContent;
                }
                
                // Trigger input event to mark as dirty
                fieldElement.dispatchEvent(new Event('input', { bubbles: true }));
                console.log('Content updated successfully');
            } else {
                console.warn(`Field element not found for fieldId: ${fieldId}`);
                console.log('Available elements with name attribute:', document.querySelectorAll('[name]'));
                console.log('Available elements with id attribute:', document.querySelectorAll('[id]'));
            }
            
            this.showSuccess('AI content regenerated successfully from treatment notes');
        } catch (error) {
            console.error('AI regeneration error:', error);
            this.showError('Failed to regenerate AI content');
        } finally {
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    }
    
    cleanMarkdownForTextarea(content) {
        if (!content || typeof content !== 'string') {
            return content;
        }
        
        // Convert Markdown formatting to more readable plain text
        return content
            // Convert **bold** to uppercase for emphasis
            .replace(/\*\*(.*?)\*\*/g, '$1')
            // Convert bullet points with proper spacing
            .replace(/^- /gm, '• ')
            // Add extra spacing after headers/sections
            .replace(/^([A-Z][^:]*:)\s*$/gm, '\n$1\n')
            // Clean up excessive newlines
            .replace(/\n{3,}/g, '\n\n')
            // Trim whitespace
            .trim();
    }
    
    bindEvents() {
        // Save button
        this.saveBtn?.addEventListener('click', () => this.saveDraft());
        
        // Complete button
        this.completeBtn?.addEventListener('click', () => this.completeTemplate());
        
        // Export button
        this.exportBtn?.addEventListener('click', () => this.exportTemplate());
        
        // Auto-save on form changes (handled in initializeSectionFeatures)
        
        // Prevent accidental navigation
        window.addEventListener('beforeunload', (e) => {
            if (this.isDirty) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
    }
    
    setupAutoSave() {
        // Auto-save every 30 seconds if dirty
        setInterval(() => {
            if (this.isDirty) {
                this.autoSaveDraft();
            }
        }, 30000);
    }
    
    markDirty() {
        this.isDirty = true;
        this.updateSaveStatus('Unsaved changes');
    }
    
    async saveDraft() {
        console.log('🔄 Save Draft clicked');
        console.log('📝 Current instance:', this.instance);
        console.log('🗃️ Form is dirty:', this.isDirty);
        return await this.saveInstance('draft');
    }
    
    async completeTemplate() {
        console.log('✅ Complete Template clicked');
        console.log('📝 Current instance:', this.instance);
        console.log('🗃️ Form is dirty:', this.isDirty);
        if (confirm('Are you sure you want to mark this template as completed? You can still edit it later if needed.')) {
            return await this.saveInstance('completed');
        }
    }
    
    async autoSaveDraft() {
        if (!this.isDirty) return;
        
        try {
            await this.saveInstance('draft', true);
            this.updateSaveStatus('Auto-saved');
        } catch (error) {
            console.error('Auto-save failed:', error);
        }
    }
    
    async saveInstance(status = 'draft', isAutoSave = false) {
        console.log(`💾 saveInstance called: status=${status}, isAutoSave=${isAutoSave}`);
        console.log(`🆔 Instance ID: ${this.instanceId}`);
        
        try {
            if (!isAutoSave) {
                this.updateSaveStatus('Saving...');
                console.log('📊 Updating save status to "Saving..."');
            }
            
            const formData = this.collectFormData();
            console.log('📝 Collected form data:', formData);
            console.log('🗑️ Deleted sections:', this.deletedSections);
            
            const payload = {
                instance_data: formData,
                sections_deleted: this.deletedSections,
                status: status
            };
            console.log('📦 Payload being sent:', payload);
            
            const url = `/api/templates/instances/${this.instanceId}`;
            console.log('🌐 Making PUT request to:', url);
            
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(payload)
            });
            
            console.log('📡 Response status:', response.status);
            console.log('📡 Response ok:', response.ok);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Server error response:', errorText);
                throw new Error(`Failed to save template: ${response.status} - ${errorText}`);
            }
            
            const result = await response.json();
            console.log('✅ Save successful, server response:', result);
            
            this.instance = result;
            this.isDirty = false;
            
            this.updateStatusDisplay();
            console.log('🔄 Status display updated');
            
            if (isAutoSave) {
                this.updateSaveStatus('Auto-saved');
                console.log('💾 Auto-save complete');
            } else {
                this.updateSaveStatus('Saved');
                const successMessage = status === 'completed' ? 'Template completed successfully' : 'Template saved successfully';
                this.showSuccess(successMessage);
                console.log(`✅ ${status === 'completed' ? 'Template completed' : 'Template saved'} successfully`);
                
                // Redirect to reports dashboard after save/complete
                console.log('🔄 Redirecting to reports dashboard...');
                setTimeout(() => {
                    window.location.href = '/ai-reports';
                }, 1500); // Give time to show success message
            }
            
            return result;
        } catch (error) {
            console.error('❌ Save error details:', error);
            console.error('❌ Error stack:', error.stack);
            this.showError('Failed to save template');
            throw error;
        }
    }
    
    collectFormData() {
        console.log('📋 collectFormData: Starting form data collection');
        const formData = {};
        const sections = document.querySelectorAll('.template-section');
        console.log(`📋 Found ${sections.length} template sections`);
        
        document.querySelectorAll('.template-section').forEach((section, index) => {
            const sectionId = section.dataset.sectionId;
            console.log(`📋 Processing section ${index + 1}: ID=${sectionId}`);
            const sectionData = {};
            
            // Collect form fields
            section.querySelectorAll('input, textarea, select').forEach(field => {
                if (field.name) {
                    sectionData[field.name] = field.value;
                }
            });
            
            // Collect table data
            section.querySelectorAll('.assessment-table').forEach(table => {
                const tableId = table.dataset.tableId;
                const rows = [];
                
                table.querySelectorAll('tbody tr').forEach(row => {
                    const rowData = [];
                    row.querySelectorAll('input').forEach(input => {
                        rowData.push(input.value);
                    });
                    if (rowData.length > 0) {
                        rows.push(rowData);
                    }
                });
                
                if (tableId) {
                    sectionData[tableId] = { rows };
                }
            });
            
            formData[sectionId] = sectionData;
        });
        
        return formData;
    }
    
    updateSaveStatus(message) {
        if (this.statusIndicator) {
            this.statusIndicator.textContent = message;
            this.statusIndicator.className = 'save-status';
            
            if (message.includes('Saved') || message.includes('Auto-saved')) {
                this.statusIndicator.classList.add('saved');
            } else if (message.includes('Saving')) {
                this.statusIndicator.classList.add('saving');
            } else {
                this.statusIndicator.classList.add('unsaved');
            }
        }
    }
    
    updateStatusDisplay() {
        if (this.headerStatus) {
            const status = this.instance.status;
            this.headerStatus.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            this.headerStatus.className = `status-badge status-${status}`;
        }
    }
    
    async exportTemplate() {
        try {
            window.print();
        } catch (error) {
            console.error('Export error:', error);
            this.showError('Failed to export template');
        }
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type) {
        // Create or update notification element
        let notification = document.getElementById('template-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'template-notification';
            document.body.appendChild(notification);
        }
        
        notification.textContent = message;
        notification.className = `template-notification ${type} show`;
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 4000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global template editor instance
let templateEditor;

// Initialize editor when page loads
function initializeTemplateEditor(instanceId) {
    templateEditor = new TemplateEditor(instanceId);
}

// Export for external use
window.TemplateEditor = TemplateEditor;
window.initializeTemplateEditor = initializeTemplateEditor;