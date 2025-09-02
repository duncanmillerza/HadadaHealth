/**
 * Discipline Selector with Auto-Detection
 * Manages discipline selection and automatic discipline detection based on patient data
 */

// Discipline selector state
let disciplineState = {
    availableDisciplines: [],
    selectedDisciplines: [],
    autoDetectedDisciplines: [],
    filteredDisciplines: [],
    currentCategory: 'all',
    currentPatientId: null,
    onSelectionConfirmed: null
};

// Discipline definitions with categories and descriptions
const DISCIPLINE_DEFINITIONS = {
    // Therapy Disciplines
    'physiotherapy': {
        name: 'Physiotherapy',
        description: 'Physical therapy focusing on movement, function, and rehabilitation',
        category: 'therapy',
        keywords: ['muscle', 'joint', 'movement', 'pain', 'mobility', 'exercise', 'strength', 'balance', 'gait']
    },
    'occupational_therapy': {
        name: 'Occupational Therapy',
        description: 'Therapy focusing on daily living skills and adaptive techniques',
        category: 'therapy',
        keywords: ['activities', 'daily living', 'ADL', 'adaptive', 'cognitive', 'hand function', 'fine motor']
    },
    'speech_therapy': {
        name: 'Speech Language Therapy',
        description: 'Treatment of communication and swallowing disorders',
        category: 'therapy',
        keywords: ['speech', 'language', 'communication', 'swallowing', 'voice', 'articulation', 'dysphagia']
    },
    'biokinetics': {
        name: 'Biokinetics',
        description: 'Exercise-based rehabilitation and health promotion',
        category: 'therapy',
        keywords: ['exercise', 'fitness', 'conditioning', 'performance', 'injury prevention', 'athletic']
    },
    
    // Medical Disciplines
    'general_medicine': {
        name: 'General Medicine',
        description: 'General medical assessment and treatment',
        category: 'medical',
        keywords: ['medical', 'diagnosis', 'medication', 'treatment', 'symptoms', 'condition']
    },
    'orthopedics': {
        name: 'Orthopedics',
        description: 'Musculoskeletal system disorders and injuries',
        category: 'medical',
        keywords: ['bone', 'fracture', 'orthopedic', 'surgery', 'joint replacement', 'spine', 'musculoskeletal']
    },
    'neurology': {
        name: 'Neurology',
        description: 'Nervous system disorders and conditions',
        category: 'medical',
        keywords: ['neurological', 'brain', 'nervous system', 'stroke', 'seizure', 'cognitive', 'memory']
    },
    'cardiology': {
        name: 'Cardiology',
        description: 'Heart and cardiovascular system conditions',
        category: 'medical',
        keywords: ['heart', 'cardiac', 'cardiovascular', 'blood pressure', 'chest pain', 'circulation']
    },
    
    // Allied Health
    'psychology': {
        name: 'Psychology',
        description: 'Mental health and behavioral therapy',
        category: 'allied',
        keywords: ['mental health', 'psychology', 'anxiety', 'depression', 'behavioral', 'emotional', 'stress']
    },
    'dietetics': {
        name: 'Dietetics',
        description: 'Nutrition counseling and dietary management',
        category: 'allied',
        keywords: ['nutrition', 'diet', 'food', 'eating', 'weight', 'dietary', 'nutritional']
    },
    'social_work': {
        name: 'Social Work',
        description: 'Psychosocial support and resource coordination',
        category: 'allied',
        keywords: ['social', 'family', 'support', 'resources', 'discharge planning', 'psychosocial']
    },
    'podiatry': {
        name: 'Podiatry',
        description: 'Foot and ankle care and treatment',
        category: 'allied',
        keywords: ['foot', 'ankle', 'podiatry', 'walking', 'gait', 'diabetic foot', 'wound care']
    },
    
    // Specialist
    'pain_management': {
        name: 'Pain Management',
        description: 'Specialized pain assessment and treatment',
        category: 'specialist',
        keywords: ['pain', 'chronic pain', 'pain management', 'analgesic', 'nerve block', 'pain relief']
    },
    'wound_care': {
        name: 'Wound Care',
        description: 'Specialized wound assessment and management',
        category: 'specialist',
        keywords: ['wound', 'ulcer', 'pressure sore', 'healing', 'dressing', 'infection', 'tissue']
    },
    'respiratory_therapy': {
        name: 'Respiratory Therapy',
        description: 'Breathing and lung function support',
        category: 'specialist',
        keywords: ['respiratory', 'breathing', 'lung', 'oxygen', 'ventilation', 'pulmonary', 'airway']
    }
};

// Initialize discipline selector
function initializeDisciplineSelector() {
    console.log('🏥 Starting discipline selector initialization...');
    try {
        setupDisciplineEventListeners();
        loadDisciplineFragments();
        initializeDisciplineData();
        console.log('✅ Discipline selector initialized successfully');
    } catch (error) {
        console.error('❌ Error initializing discipline selector:', error);
    }
}

// Load discipline selector fragments
function loadDisciplineFragments() {
    console.log('🔄 Loading discipline selector fragments...');
    
    fetch('/static/fragments/discipline-selector.html')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            // Add modal to body
            const modal = tempDiv.querySelector('#discipline-selector-modal');
            if (modal) {
                document.body.appendChild(modal);
                console.log('✅ Discipline selector modal loaded');
            }
            
            // Add template to body  
            const template = tempDiv.querySelector('#discipline-item-template');
            if (template) {
                document.body.appendChild(template);
                console.log('✅ Discipline item template loaded');
            }
            
            // Add inline selector template (for use in forms)
            const inlineSelector = tempDiv.querySelector('#inline-discipline-selector');
            if (inlineSelector) {
                document.body.appendChild(inlineSelector);
                console.log('✅ Inline discipline selector loaded');
            }
            
            console.log('🏥 All discipline selector fragments loaded successfully');
        })
        .catch(error => {
            console.error('❌ Failed to load discipline selector fragments:', error);
        });
}

// Initialize discipline data
function initializeDisciplineData() {
    disciplineState.availableDisciplines = Object.entries(DISCIPLINE_DEFINITIONS).map(([id, data]) => ({
        id,
        name: data.name,
        description: data.description,
        category: data.category,
        keywords: data.keywords
    }));
}

// Open discipline selector modal
function openDisciplineSelector(patientId = null, preSelected = [], callback = null) {
    disciplineState.currentPatientId = patientId;
    disciplineState.selectedDisciplines = [...preSelected];
    disciplineState.onSelectionConfirmed = callback;
    
    const modal = document.getElementById('discipline-selector-modal');
    if (!modal) {
        console.log('🔄 Discipline selector modal not ready, loading fragments...');
        // Wait for fragments to load, then retry
        setTimeout(() => openDisciplineSelector(patientId, preSelected, callback), 1000);
        return;
    }
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    console.log('🏥 Opening discipline selector...');
    
    // Render available disciplines
    renderAvailableDisciplines();
    updateSelectedDisciplinesDisplay();
    updateSelectedCount();
    
    // Auto-detect if patient ID is provided
    if (patientId) {
        autoDetectDisciplines(patientId);
    }
    
    // Focus search input
    setTimeout(() => {
        const searchInput = document.getElementById('discipline-search');
        if (searchInput) searchInput.focus();
    }, 100);
}

// Close discipline selector
function closeDisciplineSelector() {
    const modal = document.getElementById('discipline-selector-modal');
    modal.style.display = 'none';
    document.body.style.overflow = '';
    
    // Clear state
    disciplineState.selectedDisciplines = [];
    disciplineState.autoDetectedDisciplines = [];
    disciplineState.currentPatientId = null;
    disciplineState.onSelectionConfirmed = null;
    
    // Hide sections
    document.getElementById('auto-detected-section').style.display = 'none';
    document.getElementById('recommendations-section').style.display = 'none';
}

// Auto-detect disciplines based on patient data
async function autoDetectDisciplines(patientId = null) {
    const targetPatientId = patientId || disciplineState.currentPatientId;
    if (!targetPatientId) {
        showNotification('No patient ID available', 'warning');
        return;
    }
    
    try {
        console.log('🔄 Loading disciplines from patient booking history...');
        showAutoDetectionLoading(true);
        
        // Get patient bookings to see which disciplines/professions have treated them
        const bookingsResponse = await fetch(`/api/patient/${targetPatientId}/bookings`);
        if (!bookingsResponse.ok) {
            throw new Error('Failed to fetch patient bookings');
        }
        
        const bookings = await bookingsResponse.json();
        console.log('📋 Patient bookings:', bookings);
        
        // Extract unique professions from bookings and their therapists
        const patientProfessions = [...new Set(bookings.map(b => b.profession).filter(p => p))];
        const patientTherapists = [...new Set(bookings.map(b => ({
            name: b.therapist_name,
            profession: b.profession
        })).filter(t => t.name && t.profession))];
        
        console.log('🏥 Patient professions:', patientProfessions);
        console.log('👩‍⚕️ Patient therapists:', patientTherapists);
        
        // Map professions to our discipline system
        const availableDisciplines = mapProfessionsToDisciplines(patientProfessions);
        
        // Store therapist data for later use in assignment
        disciplineState.patientTherapists = patientTherapists;
        
        // Update the discipline selector to only show these disciplines
        disciplineState.availableDisciplines = availableDisciplines;
        disciplineState.autoDetectedDisciplines = availableDisciplines;
        
        if (availableDisciplines.length > 0) {
            // Show in patient history section (renamed from auto-detected)
            renderAutoDetectedDisciplines(availableDisciplines);
            document.getElementById('auto-detected-section').style.display = 'block';
        }
        
        // Update available disciplines display
        renderAvailableDisciplines()
        
        showAutoDetectionLoading(false);
        showNotification(`Found ${availableDisciplines.length} disciplines from patient history`, 'success');
        
    } catch (error) {
        console.error('Error loading patient disciplines:', error);
        showAutoDetectionLoading(false);
        showNotification('Failed to load patient history. Showing all disciplines.', 'error');
        
        // Fall back to all disciplines
        disciplineState.availableDisciplines = Object.entries(DISCIPLINE_DEFINITIONS).map(([id, data]) => ({
            id,
            name: data.name,
            description: data.description,
            category: data.category,
            keywords: data.keywords
        }));
        
        renderAvailableDisciplines();
        
        const section = document.getElementById('auto-detected-section');
        if (section) section.style.display = 'none';
    }
}

// Map booking professions to discipline IDs
function mapProfessionsToDisciplines(professions) {
    const disciplineMapping = {
        'Physiotherapy': 'physiotherapy',
        'Physiotherapist': 'physiotherapy',
        'Occupational Therapy': 'occupational_therapy',
        'Occupational Therapist': 'occupational_therapy',
        'Speech Therapy': 'speech_therapy',
        'Speech Language Therapy': 'speech_therapy',
        'Speech Therapist': 'speech_therapy',
        'Biokinetics': 'biokinetics',
        'Biokineticist': 'biokinetics',
        'Psychology': 'psychology',
        'Psychologist': 'psychology',
        'Dietetics': 'dietitian',
        'Dietitian': 'dietitian',
        'Social Work': 'social_work',
        'Social Worker': 'social_work'
    };
    
    const mappedDisciplines = [];
    
    professions.forEach(profession => {
        const disciplineId = disciplineMapping[profession];
        if (disciplineId && DISCIPLINE_DEFINITIONS[disciplineId]) {
            const disciplineData = DISCIPLINE_DEFINITIONS[disciplineId];
            mappedDisciplines.push({
                id: disciplineId,
                name: disciplineData.name,
                description: disciplineData.description,
                category: disciplineData.category,
                keywords: disciplineData.keywords,
                fromBookings: true
            });
        }
    });
    
    return mappedDisciplines;
}

// Analyze patient data and reports to detect discipline needs
function analyzeDisciplineNeeds(patientData, reports) {
    const detectedDisciplines = [];
    const analysisText = buildAnalysisText(patientData, reports);
    
    // Score disciplines based on keyword matching
    const disciplineScores = {};
    
    Object.entries(DISCIPLINE_DEFINITIONS).forEach(([disciplineId, disciplineInfo]) => {
        let score = 0;
        const keywords = disciplineInfo.keywords;
        
        keywords.forEach(keyword => {
            const regex = new RegExp(keyword, 'gi');
            const matches = (analysisText.match(regex) || []).length;
            score += matches * (keyword.length > 5 ? 2 : 1); // Longer keywords get higher weight
        });
        
        if (score > 0) {
            disciplineScores[disciplineId] = score;
        }
    });
    
    // Sort by score and return top disciplines
    const sortedDisciplines = Object.entries(disciplineScores)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6); // Limit to top 6 matches
    
    sortedDisciplines.forEach(([disciplineId, score]) => {
        const disciplineInfo = DISCIPLINE_DEFINITIONS[disciplineId];
        detectedDisciplines.push({
            id: disciplineId,
            name: disciplineInfo.name,
            description: disciplineInfo.description,
            category: disciplineInfo.category,
            confidence: Math.min(score * 10, 100), // Convert to percentage, max 100%
            autoDetected: true
        });
    });
    
    return detectedDisciplines;
}

// Build text for analysis from patient data and reports
function buildAnalysisText(patientData, reports) {
    let analysisText = '';
    
    // Add patient demographic info
    if (patientData.age) analysisText += ` age ${patientData.age}`;
    if (patientData.medical_conditions) analysisText += ` ${patientData.medical_conditions}`;
    if (patientData.current_medications) analysisText += ` ${patientData.current_medications}`;
    if (patientData.diagnosis) analysisText += ` ${patientData.diagnosis}`;
    
    // Add report content
    reports.forEach(report => {
        if (report.content) {
            if (typeof report.content === 'string') {
                analysisText += ` ${report.content}`;
            } else if (report.content.sections) {
                report.content.sections.forEach(section => {
                    analysisText += ` ${section.title} ${section.content}`;
                });
            }
        }
        if (report.diagnosis) analysisText += ` ${report.diagnosis}`;
        if (report.treatment_summary) analysisText += ` ${report.treatment_summary}`;
    });
    
    return analysisText.toLowerCase();
}

// Render auto-detected disciplines
function renderAutoDetectedDisciplines(disciplines) {
    const container = document.getElementById('auto-detected-disciplines');
    
    if (disciplines.length === 0) {
        container.innerHTML = '<p class="empty-state">No disciplines auto-detected</p>';
        return;
    }
    
    const html = disciplines.map(discipline => {
        const template = document.getElementById('discipline-item-template');
        const element = template.content.cloneNode(true);
        
        const item = element.querySelector('.discipline-item');
        item.setAttribute('data-discipline-id', discipline.id);
        item.setAttribute('data-category', discipline.category);
        item.classList.add('auto-detected-item');
        
        const checkbox = element.querySelector('.discipline-check');
        checkbox.checked = disciplineState.selectedDisciplines.includes(discipline.id);
        
        element.querySelector('.discipline-name').textContent = discipline.name;
        element.querySelector('.discipline-description').textContent = 
            `${discipline.description} (${Math.round(discipline.confidence)}% confidence)`;
        
        const autoDetectedBadge = element.querySelector('.badge.auto-detected');
        autoDetectedBadge.style.display = 'inline';
        
        if (discipline.confidence >= 80) {
            const priorityBadge = element.querySelector('.badge.priority');
            priorityBadge.style.display = 'inline';
        }
        
        return element.outerHTML;
    }).join('');
    
    container.innerHTML = html;
}

// Render available disciplines
function renderAvailableDisciplines() {
    const container = document.getElementById('available-disciplines');
    const searchTerm = document.getElementById('discipline-search')?.value.toLowerCase() || '';
    
    let filteredDisciplines = disciplineState.availableDisciplines;
    
    // Filter by category
    if (disciplineState.currentCategory !== 'all') {
        filteredDisciplines = filteredDisciplines.filter(d => d.category === disciplineState.currentCategory);
    }
    
    // Filter by search term
    if (searchTerm) {
        filteredDisciplines = filteredDisciplines.filter(d => 
            d.name.toLowerCase().includes(searchTerm) || 
            d.description.toLowerCase().includes(searchTerm)
        );
    }
    
    if (filteredDisciplines.length === 0) {
        container.innerHTML = '<div class="no-results">No disciplines found matching your criteria</div>';
        return;
    }
    
    const html = filteredDisciplines.map(discipline => {
        const template = document.getElementById('discipline-item-template');
        if (!template) {
            console.error('Discipline item template not found! Fragments may not be loaded yet.');
            return `<div class="discipline-item-error">Template loading error</div>`;
        }
        
        const element = template.content.cloneNode(true);
        
        const item = element.querySelector('.discipline-item');
        item.setAttribute('data-discipline-id', discipline.id);
        item.setAttribute('data-category', discipline.category);
        
        const checkbox = element.querySelector('.discipline-check');
        checkbox.checked = disciplineState.selectedDisciplines.includes(discipline.id);
        
        if (checkbox.checked) {
            item.classList.add('selected');
        }
        
        element.querySelector('.discipline-name').textContent = discipline.name;
        element.querySelector('.discipline-description').textContent = discipline.description;
        
        return element.outerHTML;
    }).join('');
    
    container.innerHTML = html;
}

// Update discipline selection
function updateDisciplineSelection(checkbox) {
    const disciplineItem = checkbox.closest('.discipline-item');
    const disciplineId = disciplineItem.getAttribute('data-discipline-id');
    
    if (checkbox.checked) {
        if (!disciplineState.selectedDisciplines.includes(disciplineId)) {
            disciplineState.selectedDisciplines.push(disciplineId);
        }
        disciplineItem.classList.add('selected');
    } else {
        disciplineState.selectedDisciplines = disciplineState.selectedDisciplines.filter(id => id !== disciplineId);
        disciplineItem.classList.remove('selected');
    }
    
    updateSelectedDisciplinesDisplay();
    updateDisciplineCheckboxes();
    generateRecommendations();
}

// Update selected disciplines display
function updateSelectedDisciplinesDisplay() {
    const container = document.getElementById('selected-disciplines');
    
    if (disciplineState.selectedDisciplines.length === 0) {
        container.innerHTML = '<p class="empty-state">No disciplines selected</p>';
        updateSelectedCount();
        return;
    }
    
    const html = disciplineState.selectedDisciplines.map(disciplineId => {
        const discipline = disciplineState.availableDisciplines.find(d => d.id === disciplineId);
        if (!discipline) return '';
        
        return `
            <span class="selected-item">
                ${discipline.name}
                <button class="remove-btn" onclick="removeDiscipline('${disciplineId}')">&times;</button>
            </span>
        `;
    }).join('');
    
    container.innerHTML = html;
    updateSelectedCount();
}

// Remove discipline from selection
function removeDiscipline(disciplineId) {
    disciplineState.selectedDisciplines = disciplineState.selectedDisciplines.filter(id => id !== disciplineId);
    updateSelectedDisciplinesDisplay();
    updateDisciplineCheckboxes();
}

// Update discipline checkboxes to reflect current selection
function updateDisciplineCheckboxes() {
    document.querySelectorAll('.discipline-check').forEach(checkbox => {
        const disciplineItem = checkbox.closest('.discipline-item');
        const disciplineId = disciplineItem.getAttribute('data-discipline-id');
        const isSelected = disciplineState.selectedDisciplines.includes(disciplineId);
        
        checkbox.checked = isSelected;
        disciplineItem.classList.toggle('selected', isSelected);
    });
}

// Update selected count badge
function updateSelectedCount() {
    const countBadge = document.getElementById('selected-count');
    const count = disciplineState.selectedDisciplines.length;
    countBadge.textContent = `${count} selected`;
}

// Filter disciplines by category
function filterByCategory(category) {
    disciplineState.currentCategory = category;
    
    // Update active tab
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.classList.toggle('active', tab.getAttribute('data-category') === category);
    });
    
    renderAvailableDisciplines();
}

// Toggle select all disciplines
function toggleSelectAll() {
    const button = document.getElementById('select-all-text');
    const isSelectingAll = button.textContent === 'Select All';
    
    if (isSelectingAll) {
        // Select all visible disciplines
        const visibleDisciplines = document.querySelectorAll('#available-disciplines .discipline-item:not(.filtered-out)');
        visibleDisciplines.forEach(item => {
            const disciplineId = item.getAttribute('data-discipline-id');
            if (!disciplineState.selectedDisciplines.includes(disciplineId)) {
                disciplineState.selectedDisciplines.push(disciplineId);
            }
        });
        button.textContent = 'Deselect All';
    } else {
        // Deselect all
        disciplineState.selectedDisciplines = [];
        button.textContent = 'Select All';
    }
    
    updateSelectedDisciplinesDisplay();
    updateDisciplineCheckboxes();
}

// Reset selection
function resetSelection() {
    disciplineState.selectedDisciplines = [];
    disciplineState.autoDetectedDisciplines = [];
    
    updateSelectedDisciplinesDisplay();
    updateDisciplineCheckboxes();
    
    document.getElementById('auto-detected-section').style.display = 'none';
    document.getElementById('recommendations-section').style.display = 'none';
}

// Load patient history for context
async function loadPatientHistory() {
    if (!disciplineState.currentPatientId) {
        showNotification('No patient selected for history loading', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/patients/${disciplineState.currentPatientId}/history`);
        if (!response.ok) throw new Error('Failed to load patient history');
        
        const history = await response.json();
        
        // Show patient history in a simple alert for now
        // In a real implementation, this might open a separate modal
        const historyText = `
Patient History:
- Previous appointments: ${history.appointment_count || 0}
- Last visit: ${history.last_visit || 'Never'}
- Conditions: ${history.conditions || 'None recorded'}
- Previous disciplines: ${(history.previous_disciplines || []).join(', ') || 'None'}
        `;
        
        alert(historyText);
        
    } catch (error) {
        console.error('Error loading patient history:', error);
        showNotification('Failed to load patient history', 'error');
    }
}

// Generate recommendations based on selected disciplines
function generateRecommendations() {
    if (disciplineState.selectedDisciplines.length === 0) {
        document.getElementById('recommendations-section').style.display = 'none';
        return;
    }
    
    const recommendations = [];
    const selectedCategories = new Set();
    
    // Analyze selected disciplines
    disciplineState.selectedDisciplines.forEach(disciplineId => {
        const discipline = disciplineState.availableDisciplines.find(d => d.id === disciplineId);
        if (discipline) {
            selectedCategories.add(discipline.category);
        }
    });
    
    // Generate recommendations based on common co-occurrences
    if (selectedCategories.has('therapy') && !disciplineState.selectedDisciplines.includes('psychology')) {
        recommendations.push({
            disciplineId: 'psychology',
            reason: 'Often beneficial alongside physical therapy for holistic care'
        });
    }
    
    if (disciplineState.selectedDisciplines.includes('physiotherapy') && !disciplineState.selectedDisciplines.includes('biokinetics')) {
        recommendations.push({
            disciplineId: 'biokinetics',
            reason: 'Complementary exercise-based approach to physiotherapy'
        });
    }
    
    if (selectedCategories.has('medical') && !disciplineState.selectedDisciplines.includes('social_work')) {
        recommendations.push({
            disciplineId: 'social_work',
            reason: 'Helpful for discharge planning and resource coordination'
        });
    }
    
    if (recommendations.length > 0) {
        renderRecommendations(recommendations);
        document.getElementById('recommendations-section').style.display = 'block';
    }
}

// Render recommendations
function renderRecommendations(recommendations) {
    const container = document.getElementById('recommendations-content');
    
    const html = recommendations.map(rec => {
        const discipline = disciplineState.availableDisciplines.find(d => d.id === rec.disciplineId);
        if (!discipline) return '';
        
        return `
            <div class="recommendation-item">
                <div>
                    <div class="recommendation-text">${discipline.name}</div>
                    <div class="recommendation-reason">${rec.reason}</div>
                </div>
                <button class="add-recommendation" onclick="addRecommendation('${rec.disciplineId}')">
                    Add
                </button>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

// Add recommendation to selection
function addRecommendation(disciplineId) {
    if (!disciplineState.selectedDisciplines.includes(disciplineId)) {
        disciplineState.selectedDisciplines.push(disciplineId);
        updateSelectedDisciplinesDisplay();
        updateDisciplineCheckboxes();
        
        showNotification('Discipline added to selection', 'success');
        
        // Regenerate recommendations
        generateRecommendations();
    }
}

// Confirm selection and close modal
function confirmSelection() {
    const selectedDisciplines = disciplineState.selectedDisciplines.map(disciplineId => {
        const discipline = disciplineState.availableDisciplines.find(d => d.id === disciplineId);
        return discipline ? {
            id: disciplineId,
            name: discipline.name,
            category: discipline.category,
            autoDetected: disciplineState.autoDetectedDisciplines.some(ad => ad.id === disciplineId)
        } : null;
    }).filter(Boolean);
    
    // Call callback if provided
    if (typeof disciplineState.onSelectionConfirmed === 'function') {
        disciplineState.onSelectionConfirmed(selectedDisciplines);
    }
    
    // Update inline preview if exists
    updateInlinePreview(selectedDisciplines);
    
    closeDisciplineSelector();
    
    showNotification(`Selected ${selectedDisciplines.length} disciplines`, 'success');
}

// Update inline discipline preview
function updateInlinePreview(selectedDisciplines) {
    const preview = document.getElementById('selected-disciplines-preview');
    if (!preview) return;
    
    if (selectedDisciplines.length === 0) {
        preview.innerHTML = '<p class="empty-preview">No disciplines selected. Click "Add Disciplines" to choose.</p>';
        return;
    }
    
    const html = selectedDisciplines.map(discipline => 
        `<span class="preview-item">${discipline.name}</span>`
    ).join('');
    
    preview.innerHTML = html;
}

// Search functionality
function setupDisciplineEventListeners() {
    // Search input
    document.addEventListener('input', function(event) {
        if (event.target.id === 'discipline-search') {
            renderAvailableDisciplines();
        }
    });
}

// Show auto-detection loading state
function showAutoDetectionLoading(show) {
    const section = document.getElementById('auto-detected-section');
    const container = document.getElementById('auto-detected-disciplines');
    
    if (show) {
        section.style.display = 'block';
        container.innerHTML = `
            <div class="discipline-loading">
                <div class="loading-spinner"></div>
                <span>Analyzing patient data for relevant disciplines...</span>
            </div>
        `;
    }
}

// Show notification
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

// Export functions to window for global access
window.initializeDisciplineSelector = initializeDisciplineSelector;
window.openDisciplineSelector = openDisciplineSelector;
window.closeDisciplineSelector = closeDisciplineSelector;
window.autoDetectDisciplines = autoDetectDisciplines;

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDisciplineSelector);
} else {
    initializeDisciplineSelector();
}