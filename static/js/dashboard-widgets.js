/**
 * Dashboard Widgets for AI Report Writing System
 * Manages pending, in-progress, completed, and overdue reports with deadline tracking
 */

// Widget state management
let widgetState = {
    reports: {
        pending: [],
        in_progress: [],
        completed: [],
        overdue: []
    },
    analytics: {},
    lastUpdate: null,
    refreshInterval: null
};

// Initialize dashboard widgets
function initializeDashboardWidgets() {
    createWidgetStructure();
    loadDashboardData();
    setupAutoRefresh();
    setupEventListeners();
}

// Create the HTML structure for dashboard widgets
function createWidgetStructure() {
    const dashboardContainer = document.querySelector('.dashboard');
    
    // Find and replace the existing AI Reports section
    const existingSection = Array.from(dashboardContainer.children)
        .find(section => section.innerHTML.includes('AI Reports'));
    
    if (existingSection) {
        // Create the new consolidated tabbed widget
        const widgetsHTML = `
            <div class="dashboard-widgets">
                <!-- Consolidated Reports Widget with Tabs -->
                <div class="dashboard-widget reports-mega-widget" id="reports-mega-widget">
                    <div class="widget-header">
                        <h3 class="widget-title">
                            <span class="widget-icon">📋</span>
                            Report Management
                        </h3>
                        <div class="widget-actions">
                            <button class="widget-action-btn primary" onclick="openReportWizard('therapist')">
                                Request Report
                            </button>
                            <button class="widget-action-btn" onclick="openReportWizard('manager')">
                                Assign Report
                            </button>
                        </div>
                    </div>
                    
                    <!-- Tab Navigation -->
                    <div class="widget-tabs">
                        <button class="widget-tab active" data-tab="pending" onclick="switchTab('pending')">
                            Pending <span class="widget-tab-badge" id="pending-tab-badge">0</span>
                        </button>
                        <button class="widget-tab" data-tab="in-progress" onclick="switchTab('in-progress')">
                            In Progress <span class="widget-tab-badge" id="in-progress-tab-badge">0</span>
                        </button>
                        <button class="widget-tab" data-tab="completed" onclick="switchTab('completed')">
                            Completed <span class="widget-tab-badge" id="completed-tab-badge">0</span>
                        </button>
                        <button class="widget-tab" data-tab="overdue" onclick="switchTab('overdue')">
                            Overdue <span class="widget-tab-badge" id="overdue-tab-badge">0</span>
                        </button>
                        <button class="widget-tab" data-tab="analytics" onclick="switchTab('analytics')">
                            Analytics
                        </button>
                        <button class="widget-tab" data-tab="deadlines" onclick="switchTab('deadlines')">
                            Deadlines
                        </button>
                    </div>
                    
                    <div class="widget-body no-padding">
                        <!-- Pending Reports Tab -->
                        <div class="tab-content active" id="pending-tab">
                            <div style="padding: 1.5rem;">
                                <div class="widget-summary" id="pending-summary">
                                    <div class="summary-card">
                                        <div class="summary-value" id="pending-count">0</div>
                                        <div class="summary-label">Pending</div>
                                    </div>
                                    <div class="summary-card">
                                        <div class="summary-value" id="urgent-count">0</div>
                                        <div class="summary-label">Urgent</div>
                                    </div>
                                    <div class="summary-card">
                                        <div class="summary-value" id="due-today-count">0</div>
                                        <div class="summary-label">Due Today</div>
                                    </div>
                                </div>
                            </div>
                            <ul class="widget-list" id="pending-reports-list">
                                <li class="widget-loading">
                                    <div class="loading-spinner"></div>
                                    <div>Loading pending reports...</div>
                                </li>
                            </ul>
                        </div>

                        <!-- In Progress Reports Tab -->
                        <div class="tab-content" id="in-progress-tab">
                            <div style="padding: 1.5rem;">
                                <div class="widget-summary" id="in-progress-summary">
                                    <div class="summary-card">
                                        <div class="summary-value" id="in-progress-count">0</div>
                                        <div class="summary-label">Active</div>
                                    </div>
                                    <div class="summary-card">
                                        <div class="summary-value" id="avg-completion">0%</div>
                                        <div class="summary-label">Avg Progress</div>
                                    </div>
                                </div>
                            </div>
                            <ul class="widget-list" id="in-progress-reports-list">
                                <li class="widget-loading">
                                    <div class="loading-spinner"></div>
                                    <div>Loading active reports...</div>
                                </li>
                            </ul>
                        </div>

                        <!-- Completed Reports Tab -->
                        <div class="tab-content" id="completed-tab">
                            <div style="padding: 1.5rem;">
                                <div class="widget-summary" id="completed-summary">
                                    <div class="summary-card">
                                        <div class="summary-value" id="completed-count">0</div>
                                        <div class="summary-label">This Week</div>
                                    </div>
                                    <div class="summary-card">
                                        <div class="summary-value" id="completion-rate">0%</div>
                                        <div class="summary-label">Completion Rate</div>
                                    </div>
                                </div>
                            </div>
                            <ul class="widget-list" id="completed-reports-list">
                                <li class="widget-loading">
                                    <div class="loading-spinner"></div>
                                    <div>Loading completed reports...</div>
                                </li>
                            </ul>
                        </div>

                        <!-- Overdue Reports Tab -->
                        <div class="tab-content" id="overdue-tab">
                            <div style="padding: 1.5rem;">
                                <div class="widget-summary" id="overdue-summary">
                                    <div class="summary-card">
                                        <div class="summary-value" id="overdue-count">0</div>
                                        <div class="summary-label">Overdue</div>
                                    </div>
                                    <div class="summary-card">
                                        <div class="summary-value" id="avg-overdue-days">0</div>
                                        <div class="summary-label">Avg Days Late</div>
                                    </div>
                                </div>
                            </div>
                            <ul class="widget-list" id="overdue-reports-list">
                                <li class="widget-loading">
                                    <div class="loading-spinner"></div>
                                    <div>Checking for overdue reports...</div>
                                </li>
                            </ul>
                        </div>

                        <!-- Analytics Tab -->
                        <div class="tab-content" id="analytics-tab">
                            <div style="padding: 1.5rem;">
                                <div class="progress-container">
                                    <div class="progress-label">
                                        <span>Weekly Goal Progress</span>
                                        <span id="weekly-progress-text">0/10</span>
                                    </div>
                                    <div class="progress-bar">
                                        <div class="progress-fill" id="weekly-progress-fill" style="width: 0%"></div>
                                    </div>
                                </div>
                                <div class="chart-container" id="analytics-chart">
                                    📈 Analytics Chart Placeholder
                                </div>
                            </div>
                        </div>

                        <!-- Deadlines Tab -->
                        <div class="tab-content" id="deadlines-tab">
                            <div style="padding: 1.5rem;">
                                <div class="deadline-timeline" id="deadline-timeline">
                                    <div class="widget-loading">
                                        <div class="loading-spinner"></div>
                                        <div>Loading deadlines...</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Replace the existing section with the new widgets
        existingSection.outerHTML = widgetsHTML;
    }
}

// Load all dashboard data
async function loadDashboardData() {
    try {
        // Load dashboard data from API
        const response = await fetch('/api/reports/user/dashboard');
        if (!response.ok) throw new Error('Failed to load dashboard data');
        
        const data = await response.json();
        
        // Update widget state
        widgetState.reports = {
            pending: data.pending_reports || [],
            in_progress: [], // Will be populated from pending/in_progress reports
            completed: data.completed_reports || [],
            overdue: data.overdue_reports || []
        };
        
        // Load analytics
        await loadAnalytics();
        
        // Update all widgets
        updateAllWidgets();
        
        widgetState.lastUpdate = new Date();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showWidgetError('Failed to load dashboard data');
    }
}

// Load analytics data
async function loadAnalytics() {
    try {
        const response = await fetch('/api/reports/analytics');
        if (response.ok) {
            widgetState.analytics = await response.json();
        } else {
            console.log(`Analytics API returned ${response.status}, using mock data`);
            // Use mock analytics if API fails
            widgetState.analytics = {
                total_reports: 15,
                pending_count: 3,
                in_progress_count: 5,
                completed_count: 7,
                overdue_count: 2,
                completion_rate: 75,
                average_completion_days: 3.2,
                urgent_reports: 4
            };
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
        // Use default analytics if API fails
        widgetState.analytics = {
            total_reports: 10,
            pending_count: 2,
            in_progress_count: 3,
            completed_count: 5,
            overdue_count: 1,
            completion_rate: 65,
            average_completion_days: 4.0,
            urgent_reports: 2
        };
    }
}

// Update all widgets with current data
function updateAllWidgets() {
    updatePendingWidget();
    updateInProgressWidget();
    updateCompletedWidget();
    updateOverdueWidget();
    updateAnalyticsWidget();
    updateDeadlineTimelineWidget();
    updateTabBadges();
}

// Update tab badges with current counts
function updateTabBadges() {
    // Update tab badges
    const pendingBadge = document.getElementById('pending-tab-badge');
    const inProgressBadge = document.getElementById('in-progress-tab-badge');
    const completedBadge = document.getElementById('completed-tab-badge');
    const overdueBadge = document.getElementById('overdue-tab-badge');
    
    if (pendingBadge) pendingBadge.textContent = widgetState.reports.pending.length;
    if (inProgressBadge) inProgressBadge.textContent = widgetState.reports.in_progress.length;
    if (completedBadge) completedBadge.textContent = widgetState.reports.completed.length;
    if (overdueBadge) overdueBadge.textContent = widgetState.reports.overdue.length;
}

// Update pending reports widget
function updatePendingWidget() {
    const reports = widgetState.reports.pending;
    const urgentReports = reports.filter(r => r.priority === 3 || isDueSoon(r.deadline_date));
    const dueTodayReports = reports.filter(r => isDueToday(r.deadline_date));
    
    // Update summary
    document.getElementById('pending-count').textContent = reports.length;
    document.getElementById('urgent-count').textContent = urgentReports.length;
    document.getElementById('due-today-count').textContent = dueTodayReports.length;
    
    // Update list
    const listElement = document.getElementById('pending-reports-list');
    if (reports.length === 0) {
        listElement.innerHTML = `
            <li class="widget-empty-state">
                <div class="empty-state-icon">📋</div>
                <div class="empty-state-message">No pending reports</div>
                <div class="empty-state-submessage">All caught up!</div>
            </li>
        `;
    } else {
        listElement.innerHTML = reports.slice(0, 5).map(report => createReportListItem(report)).join('');
    }
}

// Update in-progress reports widget
function updateInProgressWidget() {
    // Filter for in-progress reports from the data
    const reports = widgetState.reports.pending.filter(r => r.status === 'in_progress');
    
    // Calculate average progress (mock calculation)
    const avgProgress = reports.length > 0 ? Math.round(Math.random() * 100) : 0;
    
    // Update summary
    document.getElementById('in-progress-count').textContent = reports.length;
    document.getElementById('avg-completion').textContent = `${avgProgress}%`;
    
    // Update list
    const listElement = document.getElementById('in-progress-reports-list');
    if (reports.length === 0) {
        listElement.innerHTML = `
            <li class="widget-empty-state">
                <div class="empty-state-icon">⚡</div>
                <div class="empty-state-message">No active reports</div>
                <div class="empty-state-submessage">Start working on pending reports</div>
            </li>
        `;
    } else {
        listElement.innerHTML = reports.slice(0, 5).map(report => createReportListItem(report, true)).join('');
    }
}

// Update completed reports widget
function updateCompletedWidget() {
    const reports = widgetState.reports.completed;
    const thisWeekReports = reports.filter(r => isThisWeek(r.completed_at));
    const completionRate = widgetState.analytics.completion_rate || 0;
    
    // Update summary
    document.getElementById('completed-count').textContent = thisWeekReports.length;
    document.getElementById('completion-rate').textContent = `${Math.round(completionRate)}%`;
    
    // Update list
    const listElement = document.getElementById('completed-reports-list');
    if (reports.length === 0) {
        listElement.innerHTML = `
            <li class="widget-empty-state">
                <div class="empty-state-icon">✅</div>
                <div class="empty-state-message">No completed reports</div>
                <div class="empty-state-submessage">Complete some reports to see them here</div>
            </li>
        `;
    } else {
        listElement.innerHTML = reports.slice(0, 5).map(report => createReportListItem(report)).join('');
    }
}

// Update overdue reports widget
function updateOverdueWidget() {
    const reports = widgetState.reports.overdue;
    const avgOverdueDays = reports.length > 0 
        ? Math.round(reports.reduce((sum, r) => sum + getDaysOverdue(r.deadline_date), 0) / reports.length)
        : 0;
    
    // Update summary
    document.getElementById('overdue-count').textContent = reports.length;
    document.getElementById('avg-overdue-days').textContent = avgOverdueDays;
    
    // Update list
    const listElement = document.getElementById('overdue-reports-list');
    if (reports.length === 0) {
        listElement.innerHTML = `
            <li class="widget-empty-state">
                <div class="empty-state-icon">✅</div>
                <div class="empty-state-message">No overdue reports</div>
                <div class="empty-state-submessage">Great job staying on top of deadlines!</div>
            </li>
        `;
    } else {
        listElement.innerHTML = reports.slice(0, 5).map(report => {
            const item = createReportListItem(report);
            // Add urgency indicator for overdue reports
            return item.replace('<li class="widget-list-item"', '<li class="widget-list-item urgency-indicator urgency-pulse"');
        }).join('');
    }
}

// Update analytics widget
function updateAnalyticsWidget() {
    const analytics = widgetState.analytics;
    const totalReports = widgetState.reports.pending.length + widgetState.reports.completed.length;
    const weeklyGoal = 10; // Mock weekly goal
    const weeklyProgress = Math.min(totalReports, weeklyGoal);
    const progressPercentage = Math.round((weeklyProgress / weeklyGoal) * 100);
    
    // Update weekly progress
    document.getElementById('weekly-progress-text').textContent = `${weeklyProgress}/${weeklyGoal}`;
    document.getElementById('weekly-progress-fill').style.width = `${progressPercentage}%`;
}

// Update deadline timeline widget
function updateDeadlineTimelineWidget() {
    const allReports = [
        ...widgetState.reports.pending,
        ...widgetState.reports.pending.filter(r => r.status === 'in_progress')
    ];
    
    // Sort by deadline
    const reportsWithDeadlines = allReports
        .filter(r => r.deadline_date)
        .sort((a, b) => new Date(a.deadline_date) - new Date(b.deadline_date))
        .slice(0, 8); // Show next 8 deadlines
    
    const timelineElement = document.getElementById('deadline-timeline');
    
    if (reportsWithDeadlines.length === 0) {
        timelineElement.innerHTML = `
            <div class="widget-empty-state">
                <div class="empty-state-icon">📅</div>
                <div class="empty-state-message">No upcoming deadlines</div>
            </div>
        `;
    } else {
        const timelineHTML = reportsWithDeadlines.map(report => {
            const deadline = new Date(report.deadline_date);
            const today = new Date();
            const daysUntilDeadline = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
            
            let statusClass = 'timeline-status';
            let statusText = report.status.charAt(0).toUpperCase() + report.status.slice(1);
            
            if (daysUntilDeadline < 0) {
                statusClass += ' deadline-overdue';
                statusText = `${Math.abs(daysUntilDeadline)} days overdue`;
            } else if (daysUntilDeadline === 0) {
                statusClass += ' deadline-warning';
                statusText = 'Due today';
            } else if (daysUntilDeadline <= 2) {
                statusClass += ' deadline-warning';
                statusText = `Due in ${daysUntilDeadline} days`;
            }
            
            return `
                <div class="timeline-item" onclick="openReportWizard('therapist', ${report.id})" style="cursor: pointer;">
                    <div>
                        <div class="timeline-date">${deadline.toLocaleDateString()}</div>
                        <div style="font-weight: 500; color: #333;">${report.title}</div>
                    </div>
                    <div class="${statusClass}">${statusText}</div>
                </div>
            `;
        }).join('');
        
        timelineElement.innerHTML = timelineHTML;
    }
}

// Create a report list item HTML
function createReportListItem(report, showProgress = false) {
    const deadline = report.deadline_date ? new Date(report.deadline_date) : null;
    const daysUntilDeadline = deadline ? Math.ceil((deadline - new Date()) / (1000 * 60 * 60 * 24)) : null;
    
    let deadlineClass = 'deadline-badge';
    let deadlineText = deadline ? deadline.toLocaleDateString() : 'No deadline';
    
    if (daysUntilDeadline !== null) {
        if (daysUntilDeadline < 0) {
            deadlineClass += ' deadline-overdue';
            deadlineText = `${Math.abs(daysUntilDeadline)} days overdue`;
        } else if (daysUntilDeadline === 0) {
            deadlineClass += ' deadline-warning';
            deadlineText = 'Due today';
        } else if (daysUntilDeadline <= 2) {
            deadlineClass += ' deadline-warning';
            deadlineText = `Due in ${daysUntilDeadline} days`;
        }
    }
    
    const priorityBadge = `
        <div class="priority-badge priority-${getPriorityClass(report.priority)}">
            Priority ${report.priority === 3 ? 'High' : report.priority === 2 ? 'Normal' : 'Low'}
        </div>
    `;
    
    const statusBadge = `
        <div class="status-badge status-${report.status.replace('_', '-')}">
            ${report.status.charAt(0).toUpperCase() + report.status.slice(1).replace('_', ' ')}
        </div>
    `;
    
    const progressBar = showProgress ? `
        <div class="progress-container" style="margin-top: 0.5rem;">
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${Math.random() * 100}%"></div>
            </div>
        </div>
    ` : '';
    
    return `
        <li class="widget-list-item">
            <div class="report-item">
                <div class="report-info">
                    <div class="report-title">${report.title}</div>
                    <div class="report-meta">
                        <span class="report-patient">Patient: ${report.patient_name || report.patient_id}</span>
                        <span class="report-disciplines">${Array.isArray(report.disciplines) ? report.disciplines.join(', ') : (report.disciplines || 'General')}</span>
                    </div>
                    ${progressBar}
                </div>
                <div class="report-badges">
                    ${priorityBadge}
                    ${statusBadge}
                    <div class="${deadlineClass}">${deadlineText}</div>
                    <div class="report-actions" style="margin-top: 0.5rem;">
                        <button class="btn-icon" onclick="event.stopPropagation(); openReportEditor('${report.id}')" title="Edit Report">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon" onclick="event.stopPropagation(); viewReport('${report.id}')" title="View Report">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>
            </div>
        </li>
    `;
}

// Utility functions
function getPriorityClass(priority) {
    switch(priority) {
        case 3: return 'high';
        case 2: return 'normal';
        case 1: return 'low';
        default: return 'normal';
    }
}

function isDueSoon(deadlineDate) {
    if (!deadlineDate) return false;
    const deadline = new Date(deadlineDate);
    const today = new Date();
    const daysUntilDeadline = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
    return daysUntilDeadline <= 3 && daysUntilDeadline >= 0;
}

function isDueToday(deadlineDate) {
    if (!deadlineDate) return false;
    const deadline = new Date(deadlineDate);
    const today = new Date();
    return deadline.toDateString() === today.toDateString();
}

function isThisWeek(dateString) {
    if (!dateString) return false;
    const date = new Date(dateString);
    const today = new Date();
    const weekStart = new Date(today.setDate(today.getDate() - today.getDay()));
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 6);
    return date >= weekStart && date <= weekEnd;
}

function getDaysOverdue(deadlineDate) {
    if (!deadlineDate) return 0;
    const deadline = new Date(deadlineDate);
    const today = new Date();
    const diffTime = today - deadline;
    return Math.max(0, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
}

// Widget action handlers
function refreshWidget(widgetType) {
    showNotification('Refreshing widget...', 'info');
    loadDashboardData();
}

function viewAllCompleted() {
    showNotification('Opening completed reports view...', 'info');
    // This would typically open a dedicated completed reports page
}

function escalateOverdue() {
    const overdueCount = widgetState.reports.overdue.length;
    if (overdueCount === 0) {
        showNotification('No overdue reports to escalate', 'info');
        return;
    }
    showNotification(`Escalating ${overdueCount} overdue reports to supervisors...`, 'warning');
    // This would typically send escalation notifications
}

function exportAnalytics() {
    showNotification('Preparing analytics export...', 'info');
    // This would typically generate a CSV or PDF export
}

function extendDeadlines() {
    showNotification('Deadline extension feature coming soon...', 'info');
    // This would typically open a modal to extend selected deadlines
}

// View report (opens in preview mode)
function viewReport(reportId) {
    if (typeof openReportEditor === 'function') {
        openReportEditor(reportId);
        // Switch to preview mode after editor loads
        setTimeout(() => {
            if (typeof previewReport === 'function') {
                previewReport();
            }
        }, 1000);
    } else {
        showNotification('Report viewer not available', 'warning');
    }
}

// Tab switching functionality
function switchTab(tabName) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.widget-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Add active class to selected tab and content
    const selectedTab = document.querySelector(`[data-tab="${tabName}"]`);
    const selectedContent = document.getElementById(`${tabName}-tab`);
    
    if (selectedTab && selectedContent) {
        selectedTab.classList.add('active');
        selectedContent.classList.add('active');
    }
    
    // Update specific tab content if needed
    switch(tabName) {
        case 'analytics':
            updateAnalyticsTab();
            break;
        case 'deadlines':
            updateDeadlinesTab();
            break;
    }
}

// Update analytics tab with current data
function updateAnalyticsTab() {
    if (widgetState.analytics) {
        const progressText = document.getElementById('weekly-progress-text');
        const progressFill = document.getElementById('weekly-progress-fill');
        
        if (progressText && progressFill) {
            const completed = widgetState.analytics.weekly_completed || 0;
            const target = widgetState.analytics.weekly_target || 10;
            const percentage = Math.min((completed / target) * 100, 100);
            
            progressText.textContent = `${completed}/${target}`;
            progressFill.style.width = `${percentage}%`;
        }
    }
}

// Update deadlines tab with current data
function updateDeadlinesTab() {
    const timeline = document.getElementById('deadline-timeline');
    if (!timeline) return;
    
    // Collect all deadlines from reports
    const allDeadlines = [];
    
    ['pending', 'in_progress', 'overdue'].forEach(status => {
        widgetState.reports[status].forEach(report => {
            if (report.deadline) {
                allDeadlines.push({
                    title: report.title,
                    patient: report.patient_name,
                    deadline: new Date(report.deadline),
                    status: status,
                    priority: report.priority || 'normal'
                });
            }
        });
    });
    
    // Sort by deadline
    allDeadlines.sort((a, b) => a.deadline - b.deadline);
    
    if (allDeadlines.length === 0) {
        timeline.innerHTML = '<div class="widget-empty-state"><div class="empty-state-message">No upcoming deadlines</div></div>';
        return;
    }
    
    // Render deadline timeline
    const timelineHTML = allDeadlines.slice(0, 10).map(deadline => {
        const daysUntil = Math.ceil((deadline.deadline - new Date()) / (1000 * 60 * 60 * 24));
        const statusClass = daysUntil < 0 ? 'timeline-overdue' : daysUntil <= 1 ? 'timeline-urgent' : 'timeline-normal';
        
        return `
            <div class="timeline-item ${statusClass}">
                <div>
                    <div class="timeline-title">${deadline.title}</div>
                    <div class="timeline-patient">${deadline.patient}</div>
                </div>
                <div class="timeline-date">
                    ${daysUntil < 0 ? `${Math.abs(daysUntil)} days overdue` : 
                      daysUntil === 0 ? 'Due today' : 
                      daysUntil === 1 ? 'Due tomorrow' : 
                      `${daysUntil} days`}
                </div>
            </div>
        `;
    }).join('');
    
    timeline.innerHTML = timelineHTML;
}

// Setup auto-refresh
function setupAutoRefresh() {
    // Refresh every 5 minutes
    widgetState.refreshInterval = setInterval(loadDashboardData, 5 * 60 * 1000);
}

// Setup event listeners
function setupEventListeners() {
    // Listen for report updates to refresh widgets
    document.addEventListener('reportCreated', loadDashboardData);
    document.addEventListener('reportUpdated', loadDashboardData);
    
    // Handle visibility change to refresh when tab becomes active
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden && widgetState.lastUpdate) {
            const timeSinceUpdate = Date.now() - widgetState.lastUpdate.getTime();
            // Refresh if it's been more than 2 minutes since last update
            if (timeSinceUpdate > 2 * 60 * 1000) {
                loadDashboardData();
            }
        }
    });
}

// Error handling
function showWidgetError(message) {
    const widgets = document.querySelectorAll('.dashboard-widget .widget-list');
    widgets.forEach(widget => {
        widget.innerHTML = `
            <li class="widget-empty-state">
                <div class="empty-state-icon">❌</div>
                <div class="empty-state-message">Error loading data</div>
                <div class="empty-state-submessage">${message}</div>
            </li>
        `;
    });
}

// Cleanup function
function cleanupDashboardWidgets() {
    if (widgetState.refreshInterval) {
        clearInterval(widgetState.refreshInterval);
    }
}

// Export for global use
window.initializeDashboardWidgets = initializeDashboardWidgets;
window.loadDashboardData = loadDashboardData;
window.refreshWidget = refreshWidget;
window.viewAllCompleted = viewAllCompleted;
window.escalateOverdue = escalateOverdue;
window.exportAnalytics = exportAnalytics;
window.extendDeadlines = extendDeadlines;
window.cleanupDashboardWidgets = cleanupDashboardWidgets;