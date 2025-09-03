/**
 * Outcome Measures Modal System
 * Handles the three-step process for adding outcome measures to treatment notes
 */

class OutcomeMeasuresManager {
    constructor() {
        this.currentModal = null;
        this.currentStep = 1;
        this.selectedDomain = null;
        this.selectedMeasure = null;
        this.entryData = {};
        this.currentTreatmentNoteId = null;
        this.isEditMode = false;
        this.currentEntryId = null;
        
        // Cache for frequently accessed data
        this.domains = [];
        this.recentMeasures = [];
        
        this.init();
    }
    
    init() {
        // Load initial data
        this.loadDomains();
        this.loadRecentMeasures();
    }
    
    async loadDomains() {
        try {
            const response = await fetch('/api/outcome-measures/domains');
            if (response.ok) {
                const data = await response.json();
                this.domains = data.domains;
            }
        } catch (error) {
            console.error('Error loading domains:', error);
        }
    }
    
    loadRecentMeasures() {
        // Load from localStorage or set defaults
        const stored = localStorage.getItem('recentOutcomeMeasures');
        if (stored) {
            this.recentMeasures = JSON.parse(stored);
        } else {
            // Default favorites based on common usage
            this.recentMeasures = [
                { id: 1, name: 'Berg Balance Scale', abbreviation: 'BBS' },
                { id: 3, name: '10 Meter Walk Test', abbreviation: '10mWT' },
                { id: 6, name: 'Six Minute Walk Test', abbreviation: '6MWT' }
            ];
        }
    }
    
    saveRecentMeasure(measure) {
        // Add to recent measures (limit to 5)
        const existing = this.recentMeasures.findIndex(m => m.id === measure.id);
        if (existing !== -1) {
            this.recentMeasures.splice(existing, 1);
        }
        this.recentMeasures.unshift(measure);
        this.recentMeasures = this.recentMeasures.slice(0, 5);
        localStorage.setItem('recentOutcomeMeasures', JSON.stringify(this.recentMeasures));
    }
    
    // Main modal functions
    openOutcomeModal(treatmentNoteId) {
        this.currentTreatmentNoteId = treatmentNoteId;
        this.currentStep = 1;
        this.selectedDomain = null;
        this.selectedMeasure = null;
        this.entryData = {};
        this.isEditMode = false;
        this.currentEntryId = null;
        
        this.createModal();
        this.loadStep1();
        document.body.appendChild(this.currentModal);
    }
    
    async editOutcome(entryId) {
        try {
            this.showLoadingModal();
            
            const response = await fetch(`/api/outcome-entries/${entryId}`);
            if (!response.ok) throw new Error('Failed to load outcome entry');
            
            const data = await response.json();
            this.entryData = data.entry;
            this.currentEntryId = entryId;
            this.isEditMode = true;
            
            // Get measure details
            const measureResponse = await fetch(`/api/outcome-measures/measures/${this.entryData.measure_id}`);
            if (!measureResponse.ok) throw new Error('Failed to load measure details');
            
            const measureData = await measureResponse.json();
            this.selectedMeasure = measureData.measure;
            
            // Find domain
            this.selectedDomain = this.domains.find(d => d.id === this.selectedMeasure.domain_id);
            
            this.createModal();
            this.loadStep3(true);
            document.body.appendChild(this.currentModal);
            
        } catch (error) {
            this.closeModal();
            this.showNotification('Error loading outcome measure for editing', 'error');
            console.error('Edit error:', error);
        }
    }
    
    createModal() {
        if (this.currentModal) {
            this.currentModal.remove();
        }
        
        this.currentModal = document.createElement('div');
        this.currentModal.className = 'modal-overlay outcome-measures-modal';
        this.currentModal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <!-- Content will be loaded by step functions -->
                </div>
            </div>
        `;
        
        // Add click-outside-to-close
        this.currentModal.addEventListener('click', (e) => {
            if (e.target === this.currentModal) {
                this.closeModal();
            }
        });
        
        // Add escape key to close
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
    }
    
    handleKeyDown(e) {
        if (e.key === 'Escape' && this.currentModal) {
            this.closeModal();
        }
    }
    
    closeModal() {
        if (this.currentModal) {
            this.currentModal.remove();
            this.currentModal = null;
        }
        document.removeEventListener('keydown', this.handleKeyDown);
    }
    
    showLoadingModal() {
        const loadingModal = document.createElement('div');
        loadingModal.className = 'modal-overlay';
        loadingModal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <p>Loading...</p>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(loadingModal);
        this.currentModal = loadingModal;
    }
    
    // Step 1: Domain Selection
    loadStep1() {
        const modalContent = this.currentModal.querySelector('.modal-content');
        
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>Add Outcome Measure</h3>
                <button class="btn-close" onclick="outcomeMgr.closeModal()">✕</button>
            </div>
            <div class="modal-body">
                ${this.recentMeasures.length > 0 ? `
                    <div class="recent-favorites">
                        <h4>📊 Recent/Favorites</h4>
                        <div class="recent-measures-grid">
                            ${this.recentMeasures.map(measure => `
                                <button class="recent-measure-btn" onclick="outcomeMgr.selectRecentMeasure(${measure.id})">
                                    <strong>${measure.abbreviation}</strong>
                                    <span>${measure.name}</span>
                                </button>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="domain-selection">
                    <h4>Select Domain:</h4>
                    <div class="domains-grid">
                        ${this.domains.map(domain => `
                            <button class="domain-btn" onclick="outcomeMgr.selectDomain(${domain.id})">
                                <div class="domain-icon">${this.getDomainIcon(domain.name)}</div>
                                <span>${domain.name}</span>
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="outcomeMgr.closeModal()">Cancel</button>
            </div>
        `;
    }
    
    getDomainIcon(domainName) {
        const icons = {
            'Balance': '⚖️',
            'Mobility': '🚶',
            'Function': '💪'
        };
        return icons[domainName] || '📊';
    }
    
    async selectRecentMeasure(measureId) {
        try {
            const response = await fetch(`/api/outcome-measures/measures/${measureId}`);
            if (!response.ok) throw new Error('Failed to load measure');
            
            const data = await response.json();
            this.selectedMeasure = data.measure;
            this.selectedDomain = this.domains.find(d => d.id === this.selectedMeasure.domain_id);
            
            this.currentStep = 3;
            this.loadStep3();
            
        } catch (error) {
            this.showNotification('Error loading measure', 'error');
            console.error('Error selecting recent measure:', error);
        }
    }
    
    async selectDomain(domainId) {
        this.selectedDomain = this.domains.find(d => d.id === domainId);
        if (this.selectedDomain) {
            this.currentStep = 2;
            await this.loadStep2();
        }
    }
    
    // Step 2: Measure Selection
    async loadStep2() {
        try {
            const response = await fetch(`/api/outcome-measures/domains/${this.selectedDomain.id}/measures`);
            if (!response.ok) throw new Error('Failed to load measures');
            
            const data = await response.json();
            const measures = data.measures;
            
            const modalContent = this.currentModal.querySelector('.modal-content');
            
            modalContent.innerHTML = `
                <div class="modal-header">
                    <h3>Add Outcome Measure - ${this.selectedDomain.name}</h3>
                    <button class="btn-close" onclick="outcomeMgr.closeModal()">✕</button>
                </div>
                <div class="modal-body">
                    <div class="measure-selection">
                        <h4>Select Measure:</h4>
                        <div class="measures-list">
                            ${measures.map(measure => `
                                <label class="measure-option">
                                    <input type="radio" name="measure" value="${measure.id}" 
                                           onchange="outcomeMgr.selectMeasure(${measure.id})">
                                    <div class="measure-details">
                                        <strong>${measure.name} (${measure.abbreviation})</strong>
                                        <div class="measure-info">
                                            ${this.getMeasureDescription(measure)}
                                        </div>
                                    </div>
                                </label>
                            `).join('')}
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="outcomeMgr.goToStep1()">← Back</button>
                    <button class="btn-secondary" onclick="outcomeMgr.closeModal()">Cancel</button>
                    <button class="btn-primary" id="continue-btn" onclick="outcomeMgr.goToStep3()" disabled>Continue</button>
                </div>
            `;
            
        } catch (error) {
            this.showNotification('Error loading measures', 'error');
            console.error('Error loading step 2:', error);
        }
    }
    
    getMeasureDescription(measure) {
        if (measure.total_items && measure.max_score) {
            return `${measure.total_items} items • 0-${measure.max_score} ${measure.unit || 'points'}`;
        } else if (measure.unit) {
            return `Measured in ${measure.unit}`;
        }
        return 'Single measurement';
    }
    
    selectMeasure(measureId) {
        this.selectedMeasure = this.domains.find(d => d.id === this.selectedDomain.id);
        // Find the measure in the current domain's measures
        // Note: In a real implementation, we'd cache the measures or make another API call
        this.selectedMeasure = { id: measureId }; // Simplified for now
        
        const continueBtn = document.getElementById('continue-btn');
        if (continueBtn) {
            continueBtn.disabled = false;
        }
    }
    
    goToStep1() {
        this.currentStep = 1;
        this.selectedDomain = null;
        this.selectedMeasure = null;
        this.loadStep1();
    }
    
    async goToStep3() {
        if (!this.selectedMeasure || !this.selectedMeasure.id) return;
        
        try {
            // Get full measure details
            const response = await fetch(`/api/outcome-measures/measures/${this.selectedMeasure.id}`);
            if (!response.ok) throw new Error('Failed to load measure details');
            
            const data = await response.json();
            this.selectedMeasure = data.measure;
            
            this.currentStep = 3;
            this.loadStep3();
            
        } catch (error) {
            this.showNotification('Error loading measure details', 'error');
            console.error('Error going to step 3:', error);
        }
    }
    
    goToStep2() {
        if (this.isEditMode) {
            this.closeModal();
            return;
        }
        this.currentStep = 2;
        this.loadStep2();
    }
    
    // Step 3: Input Forms
    loadStep3(isEditMode = false) {
        const modalContent = this.currentModal.querySelector('.modal-content');
        
        const title = isEditMode ? 
            `Edit ${this.selectedMeasure.name}` : 
            this.selectedMeasure.name;
        
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>${title}</h3>
                <button class="btn-close" onclick="outcomeMgr.closeModal()">✕</button>
            </div>
            <div class="modal-body">
                ${this.generateStep3Content()}
            </div>
            <div class="modal-footer">
                ${!isEditMode ? '<button class="btn-secondary" onclick="outcomeMgr.goToStep2()">← Back</button>' : ''}
                <button class="btn-secondary" onclick="outcomeMgr.closeModal()">Cancel</button>
                <button class="btn-primary" onclick="outcomeMgr.saveOutcome()">
                    ${isEditMode ? 'Update' : 'Add'}
                </button>
            </div>
        `;
        
        // Pre-populate form fields if editing
        if (isEditMode) {
            this.populateFormFields();
        }
        
        // Add real-time calculation listeners
        this.attachCalculationListeners();
    }
    
    generateStep3Content() {
        const measure = this.selectedMeasure;
        
        switch (measure.abbreviation) {
            case 'BBS':
                return this.generateBBSForm();
            case 'ABC':
                return this.generateABCForm();
            case '10mWT':
                return this.generate10mWTForm();
            case '5TSTS':
                return this.generate5TSTSForm();
            case 'FGA':
                return this.generateFGAForm();
            case '6MWT':
                return this.generate6MWTForm();
            default:
                return '<p>Unknown measure type</p>';
        }
    }
    
    generateBBSForm() {
        return `
            <div class="measure-form bbs-form">
                <div class="entry-method-selection">
                    <h4>Entry Method:</h4>
                    <label>
                        <input type="radio" name="entry_method" value="individual" 
                               onchange="outcomeMgr.toggleEntryMethod('individual')" checked>
                        Enter individual items
                    </label>
                    <label>
                        <input type="radio" name="entry_method" value="total"
                               onchange="outcomeMgr.toggleEntryMethod('total')">
                        Enter total score only
                    </label>
                </div>
                
                <div id="individual-items" class="individual-items-section">
                    <h4>Berg Balance Scale Items:</h4>
                    <div class="items-container">
                        ${this.generateBBSItems()}
                    </div>
                    <div class="running-total">
                        Running Total: <span id="running-total">0</span>/56
                    </div>
                </div>
                
                <div id="total-only" class="total-only-section" style="display: none;">
                    <h4>Total Score:</h4>
                    <div class="total-input">
                        <input type="number" id="total-score" min="0" max="56" placeholder="0-56">
                        <span>/ 56</span>
                        <div class="validation-message">Valid range: 0-56</div>
                    </div>
                </div>
                
                ${this.generateCommonFields()}
            </div>
        `;
    }
    
    generateBBSItems() {
        const items = [
            "Sitting to standing",
            "Standing unsupported", 
            "Sitting unsupported",
            "Standing to sitting",
            "Transfers",
            "Standing unsupported with eyes closed",
            "Standing unsupported with feet together",
            "Reaching forward with outstretched arm while standing",
            "Pick up object from the floor from a standing position",
            "Turning to look behind over left and right shoulders",
            "Turn 360 degrees",
            "Placing alternate foot on step or stool while standing unsupported",
            "Standing unsupported one foot in front",
            "Standing on one leg"
        ];
        
        return items.map((item, index) => `
            <div class="item-row" data-item="${index + 1}">
                <div class="item-description">
                    <strong>Item ${index + 1}:</strong> ${item}
                </div>
                <div class="score-buttons">
                    ${[0, 1, 2, 3, 4].map(score => `
                        <button type="button" class="score-button" data-score="${score}"
                                onclick="outcomeMgr.selectItemScore(${index + 1}, ${score})">
                            ${score}
                        </button>
                    `).join('')}
                    <span class="max-score">/ 4</span>
                </div>
            </div>
        `).join('');
    }
    
    generate10mWTForm() {
        return `
            <div class="measure-form tenMWT-form">
                <h4>10 Meter Walk Test</h4>
                
                <div class="trial-section">
                    <h5>Comfortable Speed:</h5>
                    <div class="trials-input">
                        <div class="trial-row">
                            <label>Trial 1:</label>
                            <input type="number" id="comfortable-trial-1" step="0.1" min="0" 
                                   placeholder="seconds" onchange="outcomeMgr.updateCalculations()">
                            <span>seconds</span>
                        </div>
                        <div class="trial-row">
                            <label>Trial 2:</label>
                            <input type="number" id="comfortable-trial-2" step="0.1" min="0" 
                                   placeholder="seconds" onchange="outcomeMgr.updateCalculations()">
                            <span>seconds</span>
                        </div>
                        <div class="calculation-result">
                            Average: <span id="comfortable-result">-- s → -- m/s</span>
                        </div>
                    </div>
                </div>
                
                <div class="trial-section">
                    <h5>Fast Speed:</h5>
                    <div class="trials-input">
                        <div class="trial-row">
                            <label>Trial 1:</label>
                            <input type="number" id="fast-trial-1" step="0.1" min="0" 
                                   placeholder="seconds" onchange="outcomeMgr.updateCalculations()">
                            <span>seconds</span>
                        </div>
                        <div class="trial-row">
                            <label>Trial 2:</label>
                            <input type="number" id="fast-trial-2" step="0.1" min="0" 
                                   placeholder="seconds" onchange="outcomeMgr.updateCalculations()">
                            <span>seconds</span>
                        </div>
                        <div class="calculation-result">
                            Average: <span id="fast-result">-- s → -- m/s</span>
                        </div>
                    </div>
                </div>
                
                <div class="assistance-level">
                    <h5>Level of Assistance:</h5>
                    <select id="assistance-level">
                        <option value="7">Independent</option>
                        <option value="6">Modified Independent</option>
                        <option value="5">Supervision</option>
                        <option value="4">Minimum Assistance</option>
                        <option value="3">Moderate Assistance</option>
                        <option value="2">Maximum Assistance</option>
                        <option value="1">Total Assistance</option>
                    </select>
                </div>
                
                ${this.generateCommonFields()}
            </div>
        `;
    }
    
    generate6MWTForm() {
        return `
            <div class="measure-form sixMWT-form">
                <h4>Six Minute Walk Test</h4>
                
                <div class="distance-input">
                    <label>Distance Walked:</label>
                    <input type="number" id="distance-meters" min="0" max="1000" 
                           placeholder="meters" onchange="outcomeMgr.updateCalculations()">
                    <span>meters</span>
                    <div class="validation-message">Typical range: 150-700m</div>
                </div>
                
                <div class="test-completion">
                    <h5>Test Completed:</h5>
                    <label>
                        <input type="radio" name="test_completion" value="full" checked>
                        Full 6 minutes
                    </label>
                    <label>
                        <input type="radio" name="test_completion" value="early">
                        Stopped early at 
                        <input type="number" id="actual-time" min="0.5" max="6" step="0.5" 
                               placeholder="min" style="width: 60px;"> minutes
                    </label>
                </div>
                
                <div class="rest-breaks">
                    <div class="rest-input">
                        <label>Rest Breaks:</label>
                        <input type="number" id="rest-breaks" min="0" placeholder="0"> 
                        <span>Number of stops</span>
                    </div>
                    <div class="rest-time">
                        <label>Total Rest Time:</label>
                        <input type="number" id="rest-time" min="0" step="0.5" placeholder="0">
                        <span>minutes</span>
                    </div>
                </div>
                
                <div class="assistance-level">
                    <h5>Level of Assistance:</h5>
                    <select id="assistance-level">
                        <option value="7">Independent</option>
                        <option value="6">Modified Independent</option>
                        <option value="5">Supervision</option>
                        <option value="4">Minimum Assistance</option>
                        <option value="3">Moderate Assistance</option>
                        <option value="2">Maximum Assistance</option>
                        <option value="1">Total Assistance</option>
                    </select>
                </div>
                
                ${this.generateCommonFields()}
            </div>
        `;
    }
    
    generate5TSTSForm() {
        return `
            <div class="measure-form fiveTSTS-form">
                <h4>Five Times Sit-to-Stand Test</h4>
                
                <div class="time-input">
                    <label>Time to Complete:</label>
                    <input type="number" id="time-seconds" step="0.1" min="0" 
                           placeholder="seconds" onchange="outcomeMgr.updateCalculations()">
                    <span>seconds</span>
                    <div class="validation-message">Typical range: 5-60 seconds</div>
                </div>
                
                <div class="calculation-result">
                    <span id="interpretation-result">Enter time to see interpretation</span>
                </div>
                
                ${this.generateCommonFields()}
            </div>
        `;
    }
    
    generateABCForm() {
        return `
            <div class="measure-form abc-form">
                <div class="entry-method-selection">
                    <h4>Entry Method:</h4>
                    <label>
                        <input type="radio" name="entry_method" value="individual" 
                               onchange="outcomeMgr.toggleEntryMethod('individual')" checked>
                        Enter individual items
                    </label>
                    <label>
                        <input type="radio" name="entry_method" value="total"
                               onchange="outcomeMgr.toggleEntryMethod('total')">
                        Enter average confidence only
                    </label>
                </div>
                
                <div id="individual-items" class="individual-items-section">
                    <h4>How confident are you that you can maintain your balance and remain steady when you...</h4>
                    <div class="items-container">
                        ${this.generateABCItems()}
                    </div>
                    <div class="running-total">
                        Running Average: <span id="running-total">0</span>%
                    </div>
                </div>
                
                <div id="total-only" class="total-only-section" style="display: none;">
                    <h4>Average Confidence:</h4>
                    <div class="total-input">
                        <input type="number" id="total-score" min="0" max="100" placeholder="0-100">
                        <span>%</span>
                        <div class="validation-message">Valid range: 0-100%</div>
                    </div>
                </div>
                
                ${this.generateCommonFields()}
            </div>
        `;
    }
    
    generateABCItems() {
        const activities = [
            "walk around the house?",
            "walk up or down stairs?",
            "bend over and pick up a slipper from the front of a closet floor?",
            "reach for a small can off a shelf at eye level?",
            "stand on tip toes and reach for something above your head?",
            "stand on a chair and reach for something?",
            "sweep the floor?",
            "walk outside the house to a car parked in the driveway?",
            "get into or out of a car?",
            "walk across a parking lot to the mall?",
            "walk up or down a ramp?",
            "walk in a crowded mall where people rapidly walk past you?",
            "are bumped into by people as you walk through the mall?",
            "step onto or off of an escalator while you are holding onto a railing?",
            "step onto or off an escalator while holding onto parcels such that you cannot hold onto the railing?",
            "walk outside on icy sidewalks?"
        ];
        
        return activities.map((activity, index) => `
            <div class="item-row" data-item="${index + 1}">
                <div class="item-description">
                    <strong>${index + 1}.</strong> ...${activity}
                </div>
                <div class="confidence-input">
                    <input type="number" min="0" max="100" placeholder="0-100"
                           onchange="outcomeMgr.updateABCRunningTotal()" 
                           data-item="${index + 1}">
                    <span>%</span>
                </div>
            </div>
        `).join('');
    }
    
    generateFGAForm() {
        return `
            <div class="measure-form fga-form">
                <div class="entry-method-selection">
                    <h4>Entry Method:</h4>
                    <label>
                        <input type="radio" name="entry_method" value="individual" 
                               onchange="outcomeMgr.toggleEntryMethod('individual')" checked>
                        Enter individual items
                    </label>
                    <label>
                        <input type="radio" name="entry_method" value="total"
                               onchange="outcomeMgr.toggleEntryMethod('total')">
                        Enter total score only
                    </label>
                </div>
                
                <div id="individual-items" class="individual-items-section">
                    <h4>Functional Gait Assessment Items:</h4>
                    <div class="items-container">
                        ${this.generateFGAItems()}
                    </div>
                    <div class="running-total">
                        Running Total: <span id="running-total">0</span>/30
                    </div>
                </div>
                
                <div id="total-only" class="total-only-section" style="display: none;">
                    <h4>Total Score:</h4>
                    <div class="total-input">
                        <input type="number" id="total-score" min="0" max="30" placeholder="0-30">
                        <span>/ 30</span>
                        <div class="validation-message">Valid range: 0-30</div>
                    </div>
                </div>
                
                ${this.generateCommonFields()}
            </div>
        `;
    }
    
    generateFGAItems() {
        const items = [
            "Gait Level Surfaces",
            "Change in Gait Speed",
            "Gait with Horizontal Head Turns",
            "Gait with Vertical Head Turns",
            "Gait and Pivot Turn",
            "Step over Obstacle",
            "Gait with Narrow Base of Support",
            "Gait with Eyes Closed",
            "Ambulating Backwards",
            "Steps"
        ];
        
        return items.map((item, index) => `
            <div class="item-row" data-item="${index + 1}">
                <div class="item-description">
                    <strong>Item ${index + 1}:</strong> ${item}
                </div>
                <div class="score-buttons">
                    ${[0, 1, 2, 3].map(score => `
                        <button type="button" class="score-button" data-score="${score}"
                                onclick="outcomeMgr.selectItemScore(${index + 1}, ${score})">
                            ${score}
                        </button>
                    `).join('')}
                    <span class="max-score">/ 3</span>
                </div>
            </div>
        `).join('');
    }
    
    generateCommonFields() {
        return `
            <div class="common-fields">
                <div class="field-group">
                    <label for="assistive-device">Assistive Device:</label>
                    <input type="text" id="assistive-device" placeholder="e.g., Walker, None">
                </div>
                
                <div class="field-group">
                    <label for="additional-notes">Additional Notes:</label>
                    <textarea id="additional-notes" rows="3" 
                              placeholder="Any additional observations or comments"></textarea>
                </div>
            </div>
        `;
    }
    
    // Event handlers and calculation functions
    toggleEntryMethod(method) {
        const individualSection = document.getElementById('individual-items');
        const totalSection = document.getElementById('total-only');
        
        if (method === 'individual') {
            individualSection.style.display = 'block';
            totalSection.style.display = 'none';
        } else {
            individualSection.style.display = 'none';
            totalSection.style.display = 'block';
        }
    }
    
    selectItemScore(itemNumber, score) {
        const itemRow = document.querySelector(`[data-item="${itemNumber}"]`);
        const buttons = itemRow.querySelectorAll('.score-button');
        
        // Update button states
        buttons.forEach(btn => {
            btn.classList.toggle('selected', parseInt(btn.dataset.score) === score);
        });
        
        // Update running total
        this.updateRunningTotal();
    }
    
    updateRunningTotal() {
        const selectedButtons = document.querySelectorAll('.score-button.selected');
        let total = 0;
        selectedButtons.forEach(btn => {
            total += parseInt(btn.dataset.score);
        });
        
        const runningTotalElement = document.getElementById('running-total');
        if (runningTotalElement) {
            runningTotalElement.textContent = total;
        }
    }
    
    updateABCRunningTotal() {
        const inputs = document.querySelectorAll('.confidence-input input');
        let sum = 0;
        let count = 0;
        
        inputs.forEach(input => {
            const value = parseFloat(input.value);
            if (!isNaN(value) && value >= 0 && value <= 100) {
                sum += value;
                count++;
            }
        });
        
        const average = count > 0 ? (sum / inputs.length).toFixed(1) : 0;
        const runningTotalElement = document.getElementById('running-total');
        if (runningTotalElement) {
            runningTotalElement.textContent = average;
        }
    }
    
    updateCalculations() {
        const measure = this.selectedMeasure;
        
        if (measure.abbreviation === '10mWT') {
            this.update10mWTCalculations();
        } else if (measure.abbreviation === '5TSTS') {
            this.update5TSTSCalculations();
        } else if (measure.abbreviation === '6MWT') {
            this.update6MWTCalculations();
        }
    }
    
    update10mWTCalculations() {
        // Comfortable speed calculation
        const comfTrial1 = parseFloat(document.getElementById('comfortable-trial-1')?.value) || 0;
        const comfTrial2 = parseFloat(document.getElementById('comfortable-trial-2')?.value) || 0;
        
        if (comfTrial1 > 0 && comfTrial2 > 0) {
            const avgTime = (comfTrial1 + comfTrial2) / 2;
            const speed = (6.0 / avgTime).toFixed(2);
            document.getElementById('comfortable-result').textContent = `${avgTime.toFixed(1)}s → ${speed} m/s`;
        }
        
        // Fast speed calculation
        const fastTrial1 = parseFloat(document.getElementById('fast-trial-1')?.value) || 0;
        const fastTrial2 = parseFloat(document.getElementById('fast-trial-2')?.value) || 0;
        
        if (fastTrial1 > 0 && fastTrial2 > 0) {
            const avgTime = (fastTrial1 + fastTrial2) / 2;
            const speed = (6.0 / avgTime).toFixed(2);
            document.getElementById('fast-result').textContent = `${avgTime.toFixed(1)}s → ${speed} m/s`;
        }
    }
    
    update5TSTSCalculations() {
        const timeSeconds = parseFloat(document.getElementById('time-seconds')?.value);
        const resultElement = document.getElementById('interpretation-result');
        
        if (timeSeconds > 0 && resultElement) {
            let interpretation;
            if (timeSeconds <= 11) {
                interpretation = "Normal function";
            } else if (timeSeconds <= 13.6) {
                interpretation = "Mostly normal function";
            } else {
                interpretation = "Below normal function";
            }
            
            resultElement.textContent = `${timeSeconds}s - ${interpretation}`;
        }
    }
    
    update6MWTCalculations() {
        const distance = parseFloat(document.getElementById('distance-meters')?.value);
        // Could add interpretation display here if needed
    }
    
    attachCalculationListeners() {
        // This function adds event listeners for real-time calculations
        // Already handled by onchange events in the HTML generation
    }
    
    populateFormFields() {
        if (!this.entryData || !this.isEditMode) return;
        
        const data = this.entryData;
        const measure = this.selectedMeasure;
        
        // Populate common fields
        if (data.assistive_device) {
            const deviceField = document.getElementById('assistive-device');
            if (deviceField) deviceField.value = data.assistive_device;
        }
        
        if (data.additional_notes) {
            const notesField = document.getElementById('additional-notes');
            if (notesField) notesField.value = data.additional_notes;
        }
        
        // Populate measure-specific fields
        switch (measure.abbreviation) {
            case 'BBS':
            case 'ABC':
            case 'FGA':
                this.populateMultiItemFields(data);
                break;
            case '10mWT':
                this.populate10mWTFields(data);
                break;
            case '5TSTS':
                this.populate5TSTSFields(data);
                break;
            case '6MWT':
                this.populate6MWTFields(data);
                break;
        }
    }
    
    populateMultiItemFields(data) {
        // Implementation for populating multi-item fields
        if (data.individual_items && data.individual_items.length > 0) {
            const individualRadio = document.querySelector('input[name="entry_method"][value="individual"]');
            if (individualRadio) {
                individualRadio.checked = true;
                this.toggleEntryMethod('individual');
            }
            
            // Populate individual item scores
            data.individual_items.forEach((score, index) => {
                const itemRow = document.querySelector(`[data-item="${index + 1}"]`);
                if (itemRow) {
                    const button = itemRow.querySelector(`[data-score="${score}"]`);
                    if (button) {
                        button.classList.add('selected');
                    }
                }
            });
            
            this.updateRunningTotal();
        } else if (data.total_score !== null) {
            const totalRadio = document.querySelector('input[name="entry_method"][value="total"]');
            if (totalRadio) {
                totalRadio.checked = true;
                this.toggleEntryMethod('total');
            }
            
            const totalField = document.getElementById('total-score');
            if (totalField) {
                totalField.value = data.total_score;
            }
        }
    }
    
    populate10mWTFields(data) {
        // Populate 10mWT fields from raw data
        if (data.raw_data) {
            const comfTimes = data.raw_data.comfortable_time_trial_1 || [];
            const fastTimes = data.raw_data.fast_time_trial_1 || [];
            
            if (comfTimes.length >= 2) {
                document.getElementById('comfortable-trial-1').value = comfTimes[0];
                document.getElementById('comfortable-trial-2').value = comfTimes[1];
            }
            
            if (fastTimes.length >= 2) {
                document.getElementById('fast-trial-1').value = fastTimes[0];
                document.getElementById('fast-trial-2').value = fastTimes[1];
            }
            
            this.updateCalculations();
        }
    }
    
    populate5TSTSFields(data) {
        if (data.raw_data && data.raw_data.time_seconds) {
            document.getElementById('time-seconds').value = data.raw_data.time_seconds[0];
            this.updateCalculations();
        }
    }
    
    populate6MWTFields(data) {
        if (data.raw_data) {
            if (data.raw_data.distance_meters) {
                document.getElementById('distance-meters').value = data.raw_data.distance_meters[0];
            }
            if (data.raw_data.time_minutes && data.raw_data.time_minutes[0] !== 6.0) {
                document.querySelector('input[name="test_completion"][value="early"]').checked = true;
                document.getElementById('actual-time').value = data.raw_data.time_minutes[0];
            }
        }
    }
    
    // Save outcome measure
    async saveOutcome() {
        try {
            const formData = this.collectFormData();
            
            if (!formData) {
                this.showNotification('Please complete the required fields', 'warning');
                return;
            }
            
            const url = this.isEditMode ? 
                `/api/outcome-entries/${this.currentEntryId}` : 
                '/api/outcome-entries';
            
            const method = this.isEditMode ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    appointment_id: this.currentTreatmentNoteId,
                    measure_id: this.selectedMeasure.id,
                    ...formData
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                if (errorData.detail && errorData.detail.validation_errors) {
                    this.showValidationErrors(errorData.detail.validation_errors);
                    return;
                }
                throw new Error('Failed to save outcome measure');
            }
            
            // Save to recent measures
            this.saveRecentMeasure({
                id: this.selectedMeasure.id,
                name: this.selectedMeasure.name,
                abbreviation: this.selectedMeasure.abbreviation
            });
            
            this.closeModal();
            this.refreshOutcomesList();
            this.showNotification(
                `Outcome measure ${this.isEditMode ? 'updated' : 'saved'} successfully`, 
                'success'
            );
            
        } catch (error) {
            console.error('Error saving outcome:', error);
            this.showNotification('Error saving outcome measure', 'error');
        }
    }
    
    collectFormData() {
        const measure = this.selectedMeasure;
        const entryMethod = document.querySelector('input[name="entry_method"]:checked')?.value || 'total';
        
        const formData = {
            entry_method: entryMethod,
            assistive_device: document.getElementById('assistive-device')?.value || '',
            additional_notes: document.getElementById('additional-notes')?.value || ''
        };
        
        // Collect measure-specific data
        switch (measure.abbreviation) {
            case 'BBS':
            case 'FGA':
                return this.collectMultiItemData(formData, measure);
            case 'ABC':
                return this.collectABCData(formData);
            case '10mWT':
                return this.collect10mWTData(formData);
            case '5TSTS':
                return this.collect5TSTSData(formData);
            case '6MWT':
                return this.collect6MWTData(formData);
            default:
                return null;
        }
    }
    
    collectMultiItemData(formData, measure) {
        const entryMethod = formData.entry_method;
        
        if (entryMethod === 'individual') {
            const selectedButtons = document.querySelectorAll('.score-button.selected');
            const itemScores = [];
            
            for (let i = 1; i <= measure.total_items; i++) {
                const itemRow = document.querySelector(`[data-item="${i}"]`);
                const selectedBtn = itemRow?.querySelector('.score-button.selected');
                if (selectedBtn) {
                    itemScores.push(parseInt(selectedBtn.dataset.score));
                } else {
                    this.showNotification(`Please score item ${i}`, 'warning');
                    return null;
                }
            }
            
            formData.individual_items = itemScores;
            formData.max_item_score = measure.abbreviation === 'FGA' ? 3 : 4;
            
        } else {
            const totalScore = parseInt(document.getElementById('total-score')?.value);
            if (isNaN(totalScore)) {
                this.showNotification('Please enter a total score', 'warning');
                return null;
            }
            formData.total_score = totalScore;
        }
        
        return formData;
    }
    
    collectABCData(formData) {
        const entryMethod = formData.entry_method;
        
        if (entryMethod === 'individual') {
            const inputs = document.querySelectorAll('.confidence-input input');
            const itemScores = [];
            
            for (let input of inputs) {
                const value = parseFloat(input.value);
                if (isNaN(value) || value < 0 || value > 100) {
                    this.showNotification('All confidence ratings must be 0-100%', 'warning');
                    return null;
                }
                itemScores.push(value);
            }
            
            formData.individual_items = itemScores;
            formData.max_item_score = 100;
            
        } else {
            const totalScore = parseFloat(document.getElementById('total-score')?.value);
            if (isNaN(totalScore) || totalScore < 0 || totalScore > 100) {
                this.showNotification('Average confidence must be 0-100%', 'warning');
                return null;
            }
            formData.total_score = totalScore;
        }
        
        return formData;
    }
    
    collect10mWTData(formData) {
        const comfTrial1 = parseFloat(document.getElementById('comfortable-trial-1')?.value);
        const comfTrial2 = parseFloat(document.getElementById('comfortable-trial-2')?.value);
        const fastTrial1 = parseFloat(document.getElementById('fast-trial-1')?.value);
        const fastTrial2 = parseFloat(document.getElementById('fast-trial-2')?.value);
        
        const comfortableTrials = [];
        const fastTrials = [];
        
        if (!isNaN(comfTrial1) && comfTrial1 > 0) comfortableTrials.push(comfTrial1);
        if (!isNaN(comfTrial2) && comfTrial2 > 0) comfortableTrials.push(comfTrial2);
        if (!isNaN(fastTrial1) && fastTrial1 > 0) fastTrials.push(fastTrial1);
        if (!isNaN(fastTrial2) && fastTrial2 > 0) fastTrials.push(fastTrial2);
        
        if (comfortableTrials.length === 0) {
            this.showNotification('Please enter at least one comfortable speed trial', 'warning');
            return null;
        }
        
        formData.comfortable_trials = comfortableTrials;
        if (fastTrials.length > 0) {
            formData.fast_trials = fastTrials;
        }
        
        return formData;
    }
    
    collect5TSTSData(formData) {
        const timeSeconds = parseFloat(document.getElementById('time-seconds')?.value);
        
        if (isNaN(timeSeconds) || timeSeconds <= 0) {
            this.showNotification('Please enter a valid time in seconds', 'warning');
            return null;
        }
        
        formData.time_seconds = timeSeconds;
        return formData;
    }
    
    collect6MWTData(formData) {
        const distance = parseFloat(document.getElementById('distance-meters')?.value);
        
        if (isNaN(distance) || distance < 0) {
            this.showNotification('Please enter a valid distance', 'warning');
            return null;
        }
        
        formData.distance_meters = distance;
        
        // Check if test was completed early
        const testCompletion = document.querySelector('input[name="test_completion"]:checked')?.value;
        if (testCompletion === 'early') {
            const actualTime = parseFloat(document.getElementById('actual-time')?.value);
            if (!isNaN(actualTime) && actualTime > 0) {
                formData.actual_time_minutes = actualTime;
            }
        } else {
            formData.actual_time_minutes = 6.0;
        }
        
        return formData;
    }
    
    // Utility functions
    async refreshOutcomesList() {
        if (this.currentTreatmentNoteId) {
            try {
                const response = await fetch(`/api/treatment-notes/${this.currentTreatmentNoteId}/outcome-entries`);
                if (response.ok) {
                    const data = await response.json();
                    this.renderOutcomesList(data.entries);
                }
            } catch (error) {
                console.error('Error refreshing outcomes list:', error);
            }
        }
    }
    
    renderOutcomesList(outcomes) {
        const container = document.getElementById('outcome-measures-list');
        if (!container) return;
        
        container.innerHTML = outcomes.map(outcome => this.renderOutcomeEntry(outcome)).join('');
    }
    
    renderOutcomeEntry(outcome) {
        return `
            <div class="outcome-entry" data-entry-id="${outcome.id}">
                <div class="outcome-header">
                    <span class="measure-name">${outcome.measure_name} (${outcome.measure_abbreviation})</span>
                    <span class="timestamp">${this.formatTime(outcome.timestamp)}</span>
                    <div class="entry-actions">
                        <button onclick="outcomeMgr.editOutcome(${outcome.id})" class="btn-edit">Edit</button>
                        <button onclick="outcomeMgr.removeOutcome(${outcome.id})" class="btn-remove">Remove</button>
                    </div>
                </div>
                <div class="outcome-details">
                    <div class="score-display">
                        <strong>${outcome.calculated_result}</strong>
                    </div>
                    ${outcome.assistive_device || outcome.additional_notes ? 
                        `<div class="additional-info">
                            ${outcome.assistive_device ? `<span class="assistive-device">Device: ${outcome.assistive_device}</span>` : ''}
                            ${outcome.additional_notes ? `<span class="notes">Notes: ${outcome.additional_notes}</span>` : ''}
                        </div>` : ''}
                </div>
            </div>
        `;
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    }
    
    async removeOutcome(entryId) {
        const outcomeElement = document.querySelector(`[data-entry-id="${entryId}"]`);
        const measureName = outcomeElement.querySelector('.measure-name').textContent;
        const timestamp = outcomeElement.querySelector('.timestamp').textContent;
        
        this.showCustomConfirmation({
            title: 'Remove Outcome Measure',
            message: 'Are you sure you want to remove this outcome measure?',
            details: `${measureName} - ${timestamp}`,
            confirmText: 'Remove',
            cancelText: 'Cancel',
            onConfirm: () => this.executeRemove(entryId),
            onCancel: () => {}
        });
    }
    
    async executeRemove(entryId) {
        try {
            const outcomeElement = document.querySelector(`[data-entry-id="${entryId}"]`);
            outcomeElement.style.opacity = '0.5';
            outcomeElement.style.pointerEvents = 'none';
            
            const response = await fetch(`/api/outcome-entries/${entryId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                outcomeElement.style.transition = 'all 0.3s ease';
                outcomeElement.style.transform = 'translateX(-100%)';
                outcomeElement.style.opacity = '0';
                
                setTimeout(() => {
                    outcomeElement.remove();
                    this.showNotification('Outcome measure removed successfully', 'success');
                }, 300);
            } else {
                throw new Error('Failed to remove outcome measure');
            }
            
        } catch (error) {
            const outcomeElement = document.querySelector(`[data-entry-id="${entryId}"]`);
            outcomeElement.style.opacity = '1';
            outcomeElement.style.pointerEvents = 'auto';
            this.showNotification('Error removing outcome measure', 'error');
            console.error('Remove error:', error);
        }
    }
    
    showCustomConfirmation(options) {
        const confirmModal = document.createElement('div');
        confirmModal.className = 'modal-overlay confirmation-modal';
        confirmModal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h4>⚠️ ${options.title}</h4>
                    </div>
                    <div class="modal-body">
                        <p>${options.message}</p>
                        ${options.details ? `<div class="confirmation-details">${options.details}</div>` : ''}
                    </div>
                    <div class="modal-footer">
                        <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                            ${options.cancelText || 'Cancel'}
                        </button>
                        <button class="btn-danger" onclick="this.closest('.modal-overlay').remove(); window.confirmCallback()">
                            ${options.confirmText || 'Confirm'}
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        confirmModal.addEventListener('click', (e) => {
            if (e.target === confirmModal) {
                confirmModal.remove();
            }
        });
        
        document.body.appendChild(confirmModal);
        window.confirmCallback = options.onConfirm;
    }
    
    showValidationErrors(errors) {
        const errorText = errors.join('\n');
        this.showNotification(`Validation errors:\n${errorText}`, 'error');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize the manager when the page loads
let outcomeMgr;
document.addEventListener('DOMContentLoaded', () => {
    outcomeMgr = new OutcomeMeasuresManager();
});

// Global functions for onclick handlers
function openOutcomeModal(treatmentNoteId) {
    if (outcomeMgr) {
        outcomeMgr.openOutcomeModal(treatmentNoteId);
    }
}

function editOutcome(entryId) {
    if (outcomeMgr) {
        outcomeMgr.editOutcome(entryId);
    }
}

function removeOutcome(entryId) {
    if (outcomeMgr) {
        outcomeMgr.removeOutcome(entryId);
    }
}