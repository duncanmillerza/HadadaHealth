/**
 * Appointment Type Modal Component
 * 
 * Handles the appointment type selection modal that appears when users click
 * on calendar slots. Provides hierarchical appointment type selection with
 * practice-specific customizations.
 */

class AppointmentTypeModal {
    constructor() {
        this.isOpen = false;
        this.selectedType = null;
        this.appointmentTypes = [];
        this.practiceId = null;
        this.onSelectionCallback = null;
        this.onCancelCallback = null;
        
        // DOM elements
        this.modal = null;
        this.backdrop = null;
        this.tree = null;
        this.confirmBtn = null;
        this.cancelBtn = null;
        this.closeBtn = null;
        this.loadingSpinner = null;
        this.selectedPreview = null;
        this.errorModal = null;
        
        this.init();
    }

    /**
     * Initialize the modal component
     */
    init() {
        this.bindDOMElements();
        this.bindEvents();
    }

    /**
     * Bind DOM elements to instance variables
     */
    bindDOMElements() {
        this.modal = document.getElementById('appointment-type-modal');
        this.backdrop = document.getElementById('appointment-type-modal-backdrop');
        this.tree = document.getElementById('appointment-type-tree');
        this.confirmBtn = document.getElementById('confirm-appointment-type');
        this.cancelBtn = document.getElementById('cancel-appointment-type');
        this.closeBtn = document.getElementById('close-appointment-type-modal');
        this.loadingSpinner = document.getElementById('appointment-type-loading');
        this.selectedPreview = document.getElementById('selected-type-preview');
        this.errorModal = document.getElementById('appointment-type-error-modal');

        if (!this.modal || !this.backdrop || !this.tree) {
            console.error('AppointmentTypeModal: Required DOM elements not found');
            return;
        }
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.close());
        }
        
        if (this.cancelBtn) {
            this.cancelBtn.addEventListener('click', () => this.close());
        }
        
        if (this.backdrop) {
            this.backdrop.addEventListener('click', () => this.close());
        }
        
        if (this.confirmBtn) {
            this.confirmBtn.addEventListener('click', () => this.confirmSelection());
        }

        // Error modal handlers
        const closeErrorBtn = document.getElementById('close-appointment-type-error');
        const closeErrorBtnAlt = document.getElementById('close-appointment-type-error-btn');
        const retryBtn = document.getElementById('retry-appointment-types');

        if (closeErrorBtn) {
            closeErrorBtn.addEventListener('click', () => this.closeErrorModal());
        }
        if (closeErrorBtnAlt) {
            closeErrorBtnAlt.addEventListener('click', () => this.closeErrorModal());
        }
        if (retryBtn) {
            retryBtn.addEventListener('click', () => this.retryLoadAppointmentTypes());
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (this.isOpen) {
                if (e.key === 'Escape') {
                    this.close();
                } else if (e.key === 'Enter' && !this.confirmBtn.disabled) {
                    this.confirmSelection();
                }
            }
        });
    }

    /**
     * Open the appointment type selection modal
     * 
     * @param {Object} options - Configuration options
     * @param {number} options.practiceId - Practice ID to filter appointment types
     * @param {Function} options.onSelection - Callback when type is selected
     * @param {Function} options.onCancel - Callback when modal is cancelled
     * @param {Function} options.onError - Callback when loading fails (optional)
     * @param {Object} options.slotData - Calendar slot data (date, time, etc.)
     */
    async open({ practiceId, onSelection, onCancel, onError, slotData } = {}) {
        this.practiceId = practiceId || 1; // Default to practice 1
        this.onSelectionCallback = onSelection;
        this.onCancelCallback = onCancel;
        this.onErrorCallback = onError;
        this.slotData = slotData;
        this.selectedType = null;

        // Show modal
        this.modal.style.display = 'block';
        this.backdrop.style.display = 'block';
        this.isOpen = true;

        // Reset state
        this.resetModalState();

        // Load appointment types
        await this.loadAppointmentTypes();
    }

    /**
     * Close the modal
     */
    close() {
        if (!this.isOpen) return;

        this.modal.style.display = 'none';
        this.backdrop.style.display = 'none';
        this.isOpen = false;
        this.selectedType = null;

        // Call cancel callback if provided
        if (this.onCancelCallback) {
            this.onCancelCallback();
        }
    }

    /**
     * Reset modal to initial state
     */
    resetModalState() {
        this.confirmBtn.disabled = true;
        this.selectedPreview.style.display = 'none';
        this.tree.innerHTML = '<div class="loading-spinner" id="appointment-type-loading"><div class="spinner"></div><span>Loading appointment types...</span></div>';
    }

    /**
     * Load appointment types from the API
     */
    async loadAppointmentTypes() {
        try {
            // Show loading state
            this.showLoadingState();

            // Fetch effective appointment types for the practice
            const response = await fetch(`/api/practices/${this.practiceId}/appointment-types/effective?enabled_only=true`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    // Add authentication headers if needed
                },
            });

            if (!response.ok) {
                throw new Error(`Failed to load appointment types: ${response.status} ${response.statusText}`);
            }

            const appointmentTypes = await response.json();
            this.processAppointmentTypes(appointmentTypes);
            this.renderAppointmentTypeTree();

        } catch (error) {
            console.error('Error loading appointment types:', error);
            
            // If onError callback is provided, call it and close modal
            if (this.onErrorCallback) {
                this.close();
                this.onErrorCallback();
                return;
            }
            
            // Otherwise show error state
            this.showError('Failed to load appointment types. Please try again.');
        }
    }

    /**
     * Process flat appointment types into hierarchical structure
     * 
     * @param {Array} appointmentTypes - Flat array of appointment types
     */
    processAppointmentTypes(appointmentTypes) {
        // Group into categories (parent types) and their children
        const categories = new Map();
        
        appointmentTypes.forEach(type => {
            if (!type.parent_id) {
                // This is a parent category
                if (!categories.has(type.id)) {
                    categories.set(type.id, {
                        ...type,
                        children: []
                    });
                }
            } else {
                // This is a child type
                const parentId = type.parent_id;
                
                // Ensure parent category exists
                if (!categories.has(parentId)) {
                    // Find parent in the list
                    const parent = appointmentTypes.find(t => t.id === parentId);
                    if (parent) {
                        categories.set(parentId, {
                            ...parent,
                            children: []
                        });
                    }
                }
                
                // Add child to parent
                if (categories.has(parentId)) {
                    categories.get(parentId).children.push(type);
                }
            }
        });

        // Convert to array and sort
        this.appointmentTypes = Array.from(categories.values()).sort((a, b) => {
            // Custom sort order: Patient, Meeting, Admin, Travel, then alphabetical
            const order = { 'Patient': 1, 'Meeting': 2, 'Admin': 3, 'Travel': 4 };
            const aOrder = order[a.name] || 999;
            const bOrder = order[b.name] || 999;
            
            if (aOrder !== bOrder) {
                return aOrder - bOrder;
            }
            return a.name.localeCompare(b.name);
        });

        // Sort children within each category
        this.appointmentTypes.forEach(category => {
            category.children.sort((a, b) => {
                // Sort by sort_order first, then name
                if (a.sort_order !== b.sort_order) {
                    return a.sort_order - b.sort_order;
                }
                return a.name.localeCompare(b.name);
            });
        });
    }

    /**
     * Render the appointment type tree
     */
    renderAppointmentTypeTree() {
        this.tree.innerHTML = '';

        if (this.appointmentTypes.length === 0) {
            this.tree.innerHTML = `
                <div class="no-appointment-types">
                    <p>No appointment types available for this practice.</p>
                    <p><small>Contact your administrator to set up appointment types.</small></p>
                </div>
            `;
            return;
        }

        this.appointmentTypes.forEach(category => {
            const categoryElement = this.createCategoryElement(category);
            this.tree.appendChild(categoryElement);
        });
    }

    /**
     * Create a category element (parent appointment type with children)
     * 
     * @param {Object} category - Category data with children
     * @returns {HTMLElement} - Category DOM element
     */
    createCategoryElement(category) {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'appointment-type-category';
        categoryDiv.dataset.categoryId = category.id;

        // Create header
        const header = document.createElement('div');
        header.className = 'category-header';
        header.innerHTML = `
            <div class="category-color" style="background-color: ${category.color}"></div>
            <div class="category-name">${this.escapeHtml(category.name)}</div>
            <span class="category-expand-icon">▶</span>
        `;

        // Create children list
        const typesList = document.createElement('div');
        typesList.className = 'appointment-type-list';

        if (category.children && category.children.length > 0) {
            category.children.forEach(type => {
                const typeElement = this.createTypeElement(type);
                typesList.appendChild(typeElement);
            });
        } else {
            // If no children, make the category itself selectable
            const categoryType = this.createTypeElement(category, true);
            typesList.appendChild(categoryType);
        }

        // Add click event to header
        header.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleCategory(categoryDiv);
        });

        categoryDiv.appendChild(header);
        categoryDiv.appendChild(typesList);

        return categoryDiv;
    }

    /**
     * Create an appointment type element
     * 
     * @param {Object} type - Appointment type data
     * @param {boolean} isCategory - Whether this is a category type
     * @returns {HTMLElement} - Type DOM element
     */
    createTypeElement(type, isCategory = false) {
        const typeDiv = document.createElement('div');
        typeDiv.className = 'appointment-type-item';
        if (isCategory) {
            typeDiv.classList.add('is-category');
        }
        typeDiv.dataset.typeId = type.id;

        let billingCodeHtml = '';
        if (type.default_billing_code) {
            billingCodeHtml = `<span class="type-billing-code">${this.escapeHtml(type.default_billing_code)}</span>`;
        }

        typeDiv.innerHTML = `
            <div class="type-color" style="background-color: ${type.color}"></div>
            <div class="type-name">${this.escapeHtml(type.name)}</div>
            <div class="type-duration">${type.effective_duration || type.duration}min</div>
            ${billingCodeHtml}
        `;

        // Add click event
        typeDiv.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.selectAppointmentType(type, typeDiv);
        });

        return typeDiv;
    }

    /**
     * Toggle category expansion
     * 
     * @param {HTMLElement} categoryElement - Category DOM element
     */
    toggleCategory(categoryElement) {
        categoryElement.classList.toggle('category-expanded');
    }

    /**
     * Select an appointment type
     * 
     * @param {Object} type - Selected appointment type data
     * @param {HTMLElement} element - Selected element
     */
    selectAppointmentType(type, element) {
        // Clear previous selection
        this.tree.querySelectorAll('.appointment-type-item.selected').forEach(el => {
            el.classList.remove('selected');
        });

        // Select new type
        element.classList.add('selected');
        this.selectedType = type;

        // Enable confirm button
        this.confirmBtn.disabled = false;

        // Show preview
        this.showSelectedTypePreview(type);
    }

    /**
     * Show preview of selected appointment type
     * 
     * @param {Object} type - Selected appointment type
     */
    showSelectedTypePreview(type) {
        const preview = this.selectedPreview;
        const colorEl = preview.querySelector('.preview-color');
        const nameEl = preview.querySelector('.preview-name');
        const durationEl = preview.querySelector('.preview-duration');
        const descriptionEl = preview.querySelector('.preview-description');

        colorEl.style.backgroundColor = type.color;
        nameEl.textContent = type.name;
        durationEl.textContent = `${type.effective_duration || type.duration} min`;
        
        if (type.description) {
            descriptionEl.textContent = type.description;
            descriptionEl.style.display = 'block';
        } else {
            descriptionEl.style.display = 'none';
        }

        preview.style.display = 'block';
    }

    /**
     * Confirm the selected appointment type
     */
    confirmSelection() {
        if (!this.selectedType) return;

        // Call selection callback
        if (this.onSelectionCallback) {
            this.onSelectionCallback({
                appointmentType: this.selectedType,
                slotData: this.slotData
            });
        }

        this.close();
    }

    /**
     * Show loading state
     */
    showLoadingState() {
        this.tree.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <span>Loading appointment types...</span>
            </div>
        `;
    }

    /**
     * Show error state
     * 
     * @param {string} message - Error message to display
     */
    showError(message) {
        if (this.errorModal) {
            const errorMessageEl = document.getElementById('appointment-type-error-message');
            if (errorMessageEl) {
                errorMessageEl.textContent = message;
            }
            this.errorModal.style.display = 'block';
        } else {
            // Fallback: show error in tree
            this.tree.innerHTML = `
                <div class="error-state">
                    <div class="error-icon">⚠️</div>
                    <p>${this.escapeHtml(message)}</p>
                    <button onclick="window.appointmentTypeModal.retryLoadAppointmentTypes()" class="btn btn-primary">
                        Retry
                    </button>
                </div>
            `;
        }
    }

    /**
     * Close error modal
     */
    closeErrorModal() {
        if (this.errorModal) {
            this.errorModal.style.display = 'none';
        }
    }

    /**
     * Retry loading appointment types
     */
    async retryLoadAppointmentTypes() {
        this.closeErrorModal();
        await this.loadAppointmentTypes();
    }

    /**
     * Utility function to escape HTML
     * 
     * @param {string} text - Text to escape
     * @returns {string} - Escaped text
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize global instance
let appointmentTypeModal;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    appointmentTypeModal = new AppointmentTypeModal();
    
    // Make available globally for easy access
    window.appointmentTypeModal = appointmentTypeModal;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AppointmentTypeModal;
}