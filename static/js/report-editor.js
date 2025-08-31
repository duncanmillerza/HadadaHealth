/**
 * Report Editor with AI Content Highlighting
 * Provides comprehensive editing interface for medical reports with visual AI indicators
 */

// Editor state management
let editorState = {
    currentReport: null,
    sections: [],
    hasUnsavedChanges: false,
    autoSaveTimer: null,
    aiHighlightingEnabled: true,
    revisionHistory: [],
    suggestions: []
};

// Initialize report editor
function initializeReportEditor() {
    setupAutoSave();
    setupEventListeners();
    loadEditorFragments();
}

// Load editor fragments into DOM
function loadEditorFragments() {
    fetch('/static/fragments/report-editor.html')
        .then(response => response.text())
        .then(html => {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            document.body.appendChild(tempDiv.firstElementChild);
            document.body.appendChild(tempDiv.children[0]); // Preview modal
        })
        .catch(error => {
            console.error('Failed to load report editor fragments:', error);
        });
}

// Open report editor with specific report
function openReportEditor(reportId = null) {
    const modal = document.getElementById('report-editor-modal');
    const title = document.getElementById('editor-title');
    
    if (reportId) {
        loadReportForEditing(reportId);
        title.textContent = 'Edit Report';
    } else {
        createNewReport();
        title.textContent = 'Create New Report';
    }
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    // Focus first input
    setTimeout(() => {
        const firstInput = modal.querySelector('input[type="text"]');
        if (firstInput) firstInput.focus();
    }, 100);
}

// Close report editor
function closeReportEditor() {
    if (editorState.hasUnsavedChanges) {
        if (!confirm('You have unsaved changes. Are you sure you want to close the editor?')) {
            return;
        }
    }
    
    const modal = document.getElementById('report-editor-modal');
    modal.style.display = 'none';
    document.body.style.overflow = '';
    
    // Clear state
    editorState.currentReport = null;
    editorState.sections = [];
    editorState.hasUnsavedChanges = false;
    clearAutoSave();
}

// Load report for editing
async function loadReportForEditing(reportId) {
    try {
        showLoadingState();
        
        const response = await fetch(`/api/reports/${reportId}`);
        if (!response.ok) throw new Error('Failed to load report');
        
        const report = await response.json();
        editorState.currentReport = report;
        
        // Populate form fields
        document.getElementById('report-title-editor').value = report.title || '';
        document.getElementById('patient-name-editor').value = report.patient_name || '';
        document.getElementById('report-date-editor').value = report.created_date ? new Date(report.created_date).toISOString().split('T')[0] : '';
        
        // Load content sections
        await loadContentSections(report.content);
        
        // Load revision history
        await loadRevisionHistory(reportId);
        
        hideLoadingState();
        
    } catch (error) {
        console.error('Error loading report:', error);
        showNotification('Failed to load report for editing', 'error');
        hideLoadingState();
    }
}

// Create new report
function createNewReport() {
    editorState.currentReport = {
        id: null,
        title: '',
        patient_name: '',
        content: {},
        status: 'draft'
    };
    
    // Clear form
    document.getElementById('report-title-editor').value = '';
    document.getElementById('patient-name-editor').value = '';
    document.getElementById('report-date-editor').value = new Date().toISOString().split('T')[0];
    
    // Create initial sections
    const initialSections = [
        { title: 'Assessment Summary', content: '', ai_status: 'human-added' },
        { title: 'Clinical Findings', content: '', ai_status: 'human-added' },
        { title: 'Treatment Plan', content: '', ai_status: 'human-added' },
        { title: 'Recommendations', content: '', ai_status: 'human-added' }
    ];
    
    loadContentSections({ sections: initialSections });
}

// Load content sections
function loadContentSections(content) {
    const container = document.getElementById('content-sections');
    container.innerHTML = '';
    
    const sections = content?.sections || [];
    editorState.sections = [];
    
    sections.forEach((section, index) => {
        createContentSection(section, index);
    });
    
    if (sections.length === 0) {
        addSection(); // Add initial section if none exist
    }
}

// Create a content section
function createContentSection(sectionData, index) {
    const template = document.getElementById('section-template');
    const sectionElement = template.content.cloneNode(true);
    const container = document.getElementById('content-sections');
    
    const section = sectionElement.querySelector('.content-section');
    const sectionId = `section-${Date.now()}-${index}`;
    section.setAttribute('data-section-id', sectionId);
    section.setAttribute('data-ai-status', sectionData.ai_status || 'human-added');
    
    // Populate section data
    const titleInput = section.querySelector('.section-title-input');
    const contentEditor = section.querySelector('.content-editor');
    const statusText = section.querySelector('.status-text');
    const wordCount = section.querySelector('.count');
    
    titleInput.value = sectionData.title || '';
    contentEditor.value = sectionData.content || '';
    statusText.textContent = formatAIStatus(sectionData.ai_status || 'human-added');
    statusText.className = `status-text ${sectionData.ai_status || 'human-added'}`;
    
    // Apply AI highlighting
    if (editorState.aiHighlightingEnabled) {
        contentEditor.classList.add(sectionData.ai_status || 'human-added');
    }
    
    // Update word count
    updateWordCount(wordCount, contentEditor.value);
    
    // Add event listeners
    titleInput.addEventListener('input', handleSectionChange);
    contentEditor.addEventListener('input', (e) => {
        handleSectionChange(e);
        updateWordCount(wordCount, e.target.value);
        markAsModified(section);
    });
    
    container.appendChild(sectionElement);
    
    // Store in state
    editorState.sections.push({
        id: sectionId,
        title: sectionData.title || '',
        content: sectionData.content || '',
        ai_status: sectionData.ai_status || 'human-added'
    });
}

// Add new section
function addSection() {
    const newSection = {
        title: 'New Section',
        content: '',
        ai_status: 'human-added'
    };
    
    createContentSection(newSection, editorState.sections.length);
    markHasChanges();
}

// Delete section
function deleteSection(button) {
    if (editorState.sections.length <= 1) {
        showNotification('Cannot delete the last remaining section', 'warning');
        return;
    }
    
    if (confirm('Are you sure you want to delete this section?')) {
        const section = button.closest('.content-section');
        const sectionId = section.getAttribute('data-section-id');
        
        // Remove from DOM
        section.remove();
        
        // Remove from state
        editorState.sections = editorState.sections.filter(s => s.id !== sectionId);
        markHasChanges();
    }
}

// Move section up or down
function moveSection(button, direction) {
    const section = button.closest('.content-section');
    const container = section.parentNode;
    
    if (direction === 'up' && section.previousElementSibling) {
        container.insertBefore(section, section.previousElementSibling);
        markHasChanges();
    } else if (direction === 'down' && section.nextElementSibling) {
        container.insertBefore(section.nextElementSibling, section);
        markHasChanges();
    }
}

// Handle section content changes
function handleSectionChange(event) {
    markHasChanges();
    const section = event.target.closest('.content-section');
    markAsModified(section);
    
    // Update section in state
    const sectionId = section.getAttribute('data-section-id');
    const sectionData = editorState.sections.find(s => s.id === sectionId);
    if (sectionData) {
        if (event.target.classList.contains('section-title-input')) {
            sectionData.title = event.target.value;
        } else if (event.target.classList.contains('content-editor')) {
            sectionData.content = event.target.value;
        }
    }
}

// Mark section as modified by human
function markAsModified(section) {
    const currentStatus = section.getAttribute('data-ai-status');
    if (currentStatus === 'ai-generated') {
        section.setAttribute('data-ai-status', 'human-edited');
        
        const statusText = section.querySelector('.status-text');
        statusText.textContent = 'Human Modified';
        statusText.className = 'status-text human-edited';
        
        // Update editor highlighting
        const editor = section.querySelector('.content-editor');
        editor.classList.remove('ai-highlighted');
        editor.classList.add('human-modified');
        
        // Update in state
        const sectionId = section.getAttribute('data-section-id');
        const sectionData = editorState.sections.find(s => s.id === sectionId);
        if (sectionData) {
            sectionData.ai_status = 'human-edited';
        }
    }
}

// Toggle AI highlighting
function toggleAIHighlighting() {
    editorState.aiHighlightingEnabled = !editorState.aiHighlightingEnabled;
    const button = document.getElementById('ai-highlight-btn-text');
    
    if (editorState.aiHighlightingEnabled) {
        button.textContent = 'Hide AI Highlights';
        document.querySelectorAll('.content-editor').forEach(editor => {
            const section = editor.closest('.content-section');
            const status = section.getAttribute('data-ai-status');
            editor.classList.add(status);
        });
    } else {
        button.textContent = 'Show AI Highlights';
        document.querySelectorAll('.content-editor').forEach(editor => {
            editor.classList.remove('ai-highlighted', 'human-modified', 'human-added');
        });
    }
}

// Regenerate AI content
async function regenerateAIContent() {
    if (!confirm('This will regenerate AI content for all sections. Your manual changes will be preserved. Continue?')) {
        return;
    }
    
    showNotification('Regenerating AI content...', 'info');
    
    try {
        const reportData = collectReportData();
        const response = await fetch('/api/reports/regenerate-ai', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(reportData)
        });
        
        if (!response.ok) throw new Error('Failed to regenerate content');
        
        const result = await response.json();
        
        // Update sections with new AI content (only for AI-generated sections)
        result.sections.forEach(newSection => {
            const existingSection = editorState.sections.find(s => s.title === newSection.title);
            if (existingSection && existingSection.ai_status === 'ai-generated') {
                // Update DOM
                const sectionElement = document.querySelector(`[data-section-id="${existingSection.id}"]`);
                if (sectionElement) {
                    const editor = sectionElement.querySelector('.content-editor');
                    editor.value = newSection.content;
                    
                    // Update word count
                    const wordCount = sectionElement.querySelector('.count');
                    updateWordCount(wordCount, newSection.content);
                }
                
                // Update state
                existingSection.content = newSection.content;
            }
        });
        
        markHasChanges();
        showNotification('AI content regenerated successfully', 'success');
        
    } catch (error) {
        console.error('Error regenerating AI content:', error);
        showNotification('Failed to regenerate AI content', 'error');
    }
}

// Collect report data from form
function collectReportData() {
    const sections = [];
    
    document.querySelectorAll('.content-section').forEach(sectionElement => {
        const title = sectionElement.querySelector('.section-title-input').value;
        const content = sectionElement.querySelector('.content-editor').value;
        const ai_status = sectionElement.getAttribute('data-ai-status');
        
        sections.push({ title, content, ai_status });
    });
    
    return {
        id: editorState.currentReport?.id || null,
        title: document.getElementById('report-title-editor').value,
        patient_name: document.getElementById('patient-name-editor').value,
        report_date: document.getElementById('report-date-editor').value,
        content: { sections },
        status: 'draft'
    };
}

// Save report
async function saveReport(finalize = false) {
    try {
        const reportData = collectReportData();
        if (finalize) {
            reportData.status = 'completed';
        }
        
        updateSaveStatus('saving');
        
        const url = editorState.currentReport?.id 
            ? `/api/reports/${editorState.currentReport.id}`
            : '/api/reports';
        
        const method = editorState.currentReport?.id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(reportData)
        });
        
        if (!response.ok) throw new Error('Failed to save report');
        
        const result = await response.json();
        
        // Update current report state
        if (!editorState.currentReport?.id) {
            editorState.currentReport = result;
        }
        
        editorState.hasUnsavedChanges = false;
        updateSaveStatus('saved');
        
        if (finalize) {
            showNotification('Report saved and finalized successfully', 'success');
            // Trigger dashboard refresh
            if (typeof loadDashboardData === 'function') {
                loadDashboardData();
            }
        } else {
            showNotification('Report saved as draft', 'success');
        }
        
        return result;
        
    } catch (error) {
        console.error('Error saving report:', error);
        updateSaveStatus('error');
        showNotification('Failed to save report', 'error');
        throw error;
    }
}

// Save as draft
function saveAsDraft() {
    saveReport(false);
}

// Save and finalize
function saveAndFinalize() {
    const reportData = collectReportData();
    
    // Validate required fields
    if (!reportData.title.trim()) {
        showNotification('Please enter a report title', 'warning');
        document.getElementById('report-title-editor').focus();
        return;
    }
    
    if (!reportData.patient_name.trim()) {
        showNotification('Please enter a patient name', 'warning');
        document.getElementById('patient-name-editor').focus();
        return;
    }
    
    const hasContent = reportData.content.sections.some(s => s.content.trim());
    if (!hasContent) {
        showNotification('Please add content to at least one section', 'warning');
        return;
    }
    
    saveReport(true).then(() => {
        // Close editor after successful save
        setTimeout(() => closeReportEditor(), 1000);
    });
}

// Preview report
function previewReport() {
    const reportData = collectReportData();
    const previewModal = document.getElementById('report-preview-modal');
    const previewContent = document.getElementById('preview-content');
    
    // Generate preview HTML
    let html = `<h1>${reportData.title}</h1>`;
    html += `<div style="margin-bottom: 2rem; font-style: italic; color: #666;">`;
    html += `Patient: ${reportData.patient_name}<br>`;
    html += `Date: ${new Date(reportData.report_date).toLocaleDateString()}<br>`;
    html += `</div>`;
    
    reportData.content.sections.forEach(section => {
        if (section.title && section.content) {
            html += `<h2>${section.title}</h2>`;
            html += `<p>${section.content.replace(/\n/g, '<br>')}</p>`;
        }
    });
    
    previewContent.innerHTML = html;
    previewModal.style.display = 'flex';
}

// Close report preview
function closeReportPreview() {
    const previewModal = document.getElementById('report-preview-modal');
    previewModal.style.display = 'none';
}

// Export to PDF
function exportToPDF() {
    showNotification('PDF export feature coming soon...', 'info');
    // This would integrate with a PDF generation service
}

// Load revision history
async function loadRevisionHistory(reportId) {
    try {
        const response = await fetch(`/api/reports/${reportId}/revisions`);
        if (!response.ok) return; // Gracefully handle if revisions aren't available
        
        const revisions = await response.json();
        editorState.revisionHistory = revisions;
        
        renderRevisionHistory(revisions);
        
    } catch (error) {
        console.log('Revision history not available:', error);
    }
}

// Render revision history
function renderRevisionHistory(revisions) {
    const container = document.querySelector('.revision-list');
    
    if (revisions.length === 0) {
        container.innerHTML = '<p>No revision history available</p>';
        return;
    }
    
    const html = revisions.map(revision => `
        <div class="revision-item" onclick="viewRevision('${revision.id}')">
            <div class="revision-info">
                <div class="revision-date">${new Date(revision.created_date).toLocaleString()}</div>
                <div class="revision-author">by ${revision.author || 'Unknown'}</div>
            </div>
            <div class="revision-changes">${revision.changes_summary || 'Changes made'}</div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Toggle revision history
function toggleRevisionHistory() {
    const history = document.getElementById('revision-history');
    const button = document.getElementById('history-toggle-text');
    
    if (history.style.display === 'none') {
        history.style.display = 'block';
        button.textContent = 'Hide History';
    } else {
        history.style.display = 'none';
        button.textContent = 'Show History';
    }
}

// Utility functions
function formatAIStatus(status) {
    switch (status) {
        case 'ai-generated': return 'AI Generated';
        case 'human-edited': return 'Human Modified';
        case 'human-added': return 'Human Added';
        default: return 'Unknown';
    }
}

function updateWordCount(element, text) {
    const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
    element.textContent = wordCount;
}

function markHasChanges() {
    editorState.hasUnsavedChanges = true;
    updateSaveStatus('unsaved');
    setupAutoSave();
}

function updateSaveStatus(status) {
    const statusElement = document.getElementById('save-status');
    statusElement.className = `save-status ${status}`;
    
    switch (status) {
        case 'saving':
            statusElement.textContent = 'Saving...';
            break;
        case 'saved':
            statusElement.textContent = 'All changes saved';
            break;
        case 'unsaved':
            statusElement.textContent = 'Unsaved changes';
            break;
        case 'error':
            statusElement.textContent = 'Save failed';
            break;
    }
}

function showLoadingState() {
    const modal = document.getElementById('report-editor-modal');
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <p>Loading report...</p>
        </div>
    `;
    overlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    modal.appendChild(overlay);
}

function hideLoadingState() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Auto-save functionality
function setupAutoSave() {
    clearAutoSave();
    
    editorState.autoSaveTimer = setTimeout(() => {
        if (editorState.hasUnsavedChanges && editorState.currentReport) {
            saveReport(false);
        }
    }, 30000); // Auto-save every 30 seconds
}

function clearAutoSave() {
    if (editorState.autoSaveTimer) {
        clearTimeout(editorState.autoSaveTimer);
        editorState.autoSaveTimer = null;
    }
}

// Event listeners setup
function setupEventListeners() {
    // Handle beforeunload to warn about unsaved changes
    window.addEventListener('beforeunload', (event) => {
        if (editorState.hasUnsavedChanges) {
            event.preventDefault();
            event.returnValue = '';
        }
    });
    
    // Handle keyboard shortcuts
    document.addEventListener('keydown', (event) => {
        if (event.ctrlKey || event.metaKey) {
            if (event.key === 's') {
                event.preventDefault();
                saveAsDraft();
            }
        }
        
        if (event.key === 'Escape') {
            const modal = document.getElementById('report-editor-modal');
            if (modal && modal.style.display !== 'none') {
                closeReportEditor();
            }
        }
    });
}

// Show notification (assumes notification system exists)
function showNotification(message, type = 'info') {
    if (typeof showToastNotification === 'function') {
        showToastNotification({
            title: type.charAt(0).toUpperCase() + type.slice(1),
            message: message,
            type: type
        });
    } else {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeReportEditor);
} else {
    initializeReportEditor();
}