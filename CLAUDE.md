# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
HadadaHealth is a comprehensive healthcare practice management system built with FastAPI, designed for physiotherapists and allied health professionals in South Africa. It handles appointment scheduling, patient management, billing, outcome measures tracking, and clinical documentation with POPIA/GDPR compliance.

## Technology Stack
- **Backend**: FastAPI with Python 3.12+
- **Database**: SQLite with migration system
- **Frontend**: HTML/CSS/JavaScript (Jinja2 templates)
- **Testing**: pytest with asyncio support
- **Architecture**: Modular MVC-like structure with controllers, models, and business logic modules

## Available Agents

### Development Agents (`.claude/agents/`)

#### Architect Agent (`.claude/agents/architect.md`)
Use for system design and architectural decisions. Never writes implementation code.
- Analyzes requirements and designs solutions
- Defines component boundaries and data flow
- Provides architectural recommendations
- Requires user confirmation for complex changes

#### Developer Agent (`.claude/agents/developer.md`)
Use for implementation tasks with strict quality standards.
- Implements features with comprehensive testing
- Follows zero-linting-violation rule
- Handles errors appropriately
- Never makes architectural decisions

#### Debugger Agent (`.claude/agents/debugger.md`)
Use for systematic bug analysis and root cause identification.
- Adds debug statements with specific format
- Collects extensive evidence before analysis
- Removes all debug changes before reporting
- Provides clear root cause and fix strategy

#### Quality Reviewer Agent (`.claude/agents/quality-reviewer.md`)
Use for production-focused code review.
- Focuses on critical production issues
- Flags security vulnerabilities and performance problems
- Ignores style preferences
- Provides actionable feedback

#### Technical Writer Agent (`.claude/agents/technical-writer.md`)
Use for creating concise documentation after feature completion.
- Strict token limits (150 for modules, 100 for functions)
- Focuses on practical usage and working examples
- Documents actual behavior, not aspirations

### Agent OS Workflow Agents

#### Test Runner Agent (`.claude/agents/test-runner.md`)
Specialized for running tests and analyzing failures without making fixes.
- Executes specific tests or full test suites
- Provides detailed failure analysis
- Returns control without attempting fixes

#### Project Manager Agent (`.claude/agents/project-manager.md`)
Tracks task completion and maintains project documentation.
- Verifies task implementation against requirements  
- Updates roadmap and tracking documents
- Documents completed work in recaps

#### Context Fetcher Agent (`.claude/agents/context-fetcher.md`)
Retrieves information from documentation while avoiding duplication.
- Checks if information is already in context
- Extracts specific sections efficiently
- Uses grep for targeted information retrieval

#### File Creator Agent (`.claude/agents/file-creator.md`)
Creates files, directories, and applies templates for workflows.
- Handles batch file creation with proper structure
- Applies boilerplate templates
- Manages directory structures

#### Git Workflow Agent (`.claude/agents/git-workflow.md`)
Handles git operations, branch management, and PR creation.
- Manages git operations and branch workflows
- Creates pull requests with proper formatting
- Handles commits and repository management

#### Date Checker Agent (`.claude/agents/date-checker.md`)
Determines and outputs current date information.
- Provides current date, year, month, and day
- Checks if date content is already in context
- Used proactively for date-dependent operations

## Application Architecture

### High-Level Architecture
The application follows a layered architecture pattern:
1. **FastAPI Routes** (main.py) - HTTP request handling and routing
2. **Controllers** - Business logic coordination and API response formatting
3. **Models** - Data validation, sanitization, and ORM-like functionality
4. **Modules** - Domain-specific business logic (appointments, billing, etc.)
5. **Database Layer** - SQLite with custom connection management and migrations

### Key Architectural Patterns
- **Modular Design**: Business logic is separated into domain-specific modules (appointments, billing, patients, etc.)
- **Input Validation**: Comprehensive Pydantic models with sanitization for security
- **Database Migrations**: Versioned SQL migrations with tracking
- **MVC-like Structure**: Controllers handle request/response, models handle data, modules contain business logic
- **Security-First**: Input sanitization, SQL injection prevention, healthcare data protection

### Critical Components
- **Database Connection**: `modules/database.py` - Centralized connection management with Row factory
- **Validation Models**: `models/validation.py` - Input sanitization and Pydantic validation models  
- **Migration System**: `migrations/migration_runner.py` - Database schema versioning
- **Security**: South African ID validation, input sanitization, secure database permissions

### Module Organization
The `modules/` directory contains domain-specific business logic:
- **appointments.py** - Appointment scheduling and management
- **auth.py** - Authentication and session management
- **billing.py** - Medical billing and invoicing
- **patients.py** - Patient record management
- **treatment_notes.py** - Clinical documentation
- **outcome_measures.py** - Assessment tools and measurements
- **medical_aids.py** - Insurance and medical aid integration
- **reminders.py** - Automated notifications and alerts
- **reports.py** - AI-powered report generation and workflow management
- **ai_content.py** - AI content generation for medical reports
- **data_aggregation.py** - Patient data aggregation for report generation
- **reports_analytics.py** - Data analysis and reporting
- **settings_configuration.py** - System configuration management

### Controllers Pattern
Controllers in `controllers/` directory follow a consistent pattern:
- Handle HTTP request/response formatting
- Use Pydantic models for input validation
- Delegate business logic to appropriate modules
- Return structured API responses with proper error handling

### Database Patterns
- **Connection Management**: Use `get_db_connection()` from `modules/database.py`
- **Query Execution**: Use `execute_query()` helper with parameterized queries
- **Migrations**: Sequential numbered SQL files (001_*, 002_*, etc.)
- **Data Access**: Row factory enables dict-like access to query results

## Testing Patterns

### Test Structure
Tests are organized into multiple categories:
- **Unit Tests**: `tests/test_*.py` - Module-specific functionality testing
- **Integration Tests**: `test_*_integration.py` - Cross-module functionality
- **API Tests**: `test_api_*.py` - HTTP endpoint testing  
- **End-to-End Tests**: `test_end_to_end_*.py` - Complete workflow testing

### Test Execution Patterns
- Tests use direct module imports and controller method calls
- Database tests typically use the existing SQLite database
- API tests may use FastAPI's test client or direct HTTP calls
- Integration tests verify cross-module functionality

### Test Configuration
- **pytest.ini**: Configures test discovery and execution options
- **Test Discovery**: Looks for `test_*.py` files with `test_*` functions
- **Async Support**: Uses pytest-asyncio for FastAPI endpoint testing

## Development Commands

### Server Management
- **Start development server**: `python main.py`
- **Start with uvicorn**: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

### Testing
- **Run all tests**: `pytest`
- **Run with verbose output**: `pytest -v`
- **Run specific test file**: `pytest test_api_simple.py`
- **Run wizard tests**: `pytest test_report_wizard_ui.py -v`
- **Run with coverage**: `pytest --tb=short -v`

### Database Management
- **Run migrations**: `python -m migrations.migration_runner`
- **Secure database permissions**: `./secure_database.sh`

### Dependencies
- **Install requirements**: `pip install -r requirements.txt`
- **Update dependencies**: Update `requirements.txt` and reinstall

## Brand System & UI Standards

### Comprehensive Brand Guidelines
The complete HadadaHealth brand system is documented in `Branding/` directory with modular files optimized for Claude Code usage:

- **[Brand README](Branding/README.md)** - Complete navigation and quick start guide
- **[CSS Variables](Branding/implementation/css-variables.md)** - Design token system for consistent theming
- **[Dark Mode](Branding/dark-mode.md)** - Professional healthcare dark theme implementation
- **[Clinical Components](Branding/components/clinical-components.md)** - Patient cards, discipline tags, progress indicators

### UI Development Standards
When creating or modifying UI code, always reference the brand system:

1. **Colors**: Use CSS variables from `css-variables.md` - Never hardcode colors
2. **Typography**: Follow hierarchy from `typography.md` - System fonts for UI, serif for print
3. **Spacing**: Use 4px grid system from `layout-spacing.md` - Always use spacing variables
4. **Components**: Reference component files in `components/` directory for consistent patterns
5. **Accessibility**: Follow guidelines in `accessibility.md` - WCAG 2.1 AA compliance required
6. **Mobile**: Use patterns from `responsive-design.md` - Mobile-first approach mandatory

### Healthcare-Specific UI Requirements
- **Professional appearance**: Maintain clinical credibility in all interfaces
- **POPIA compliance**: Include privacy messaging where patient data is displayed
- **Multi-disciplinary support**: Use inclusive language and discipline-neutral patterns
- **Touch optimization**: 44px minimum touch targets for clinical environments
- **Clear information hierarchy**: Support efficient clinical workflows

### Implementation Priority
1. **Foundation**: CSS variables, color system, typography
2. **Core Components**: Buttons, forms, navigation  
3. **Clinical Features**: Patient cards, clinical components
4. **Enhanced Interactions**: Dark mode, animations, touch feedback

**Always reference the brand system files before implementing any UI changes to ensure consistency with healthcare practice management standards.**

## AI Report Creation Wizard

### Overview
The system includes a sophisticated 5-step report creation wizard that streamlines the clinical report generation process with AI assistance.

### Key Features
- **Booking-Based Recommendations**: Suggests disciplines and therapists based on patient history
- **Progressive Workflow**: 5 guided steps from patient selection to report creation
- **AI Content Generation**: Automatically generates medical history and treatment summaries
- **Multi-Disciplinary Support**: Handles physiotherapy, occupational therapy, speech therapy, psychology
- **Notification System**: Alerts assigned therapists of new report requests

### Implementation Files
- **Frontend**: `static/js/report_wizard.js` - Main wizard class and logic
- **Templates**: `static/fragments/report_wizard_modal.html` - UI markup
- **Styling**: `static/css/report_wizard.css` - Wizard-specific styles  
- **Backend**: `controllers/report_controller.py` - API endpoints and business logic
- **Tests**: `test_report_wizard_ui.py` - Comprehensive UI and workflow tests

### Usage
```javascript
// Open wizard for therapist workflow
openReportWizard('therapist');

// Open wizard for manager workflow  
openReportWizard('manager');
```

### API Endpoints
- **GET /api/reports/wizard/options** - Get wizard configuration and recommendations
- **POST /api/reports/create** - Create report from wizard payload
- **GET /api/patients/recent** - Get recent patients for step 1
- **GET /api/patients/search** - Search patients by name

### Documentation
- **User Guide**: `docs/report-wizard-guide.md` - Complete user documentation
- **Technical Guide**: `docs/report-wizard-technical.md` - Developer documentation

## Healthcare Data Security
- **POPIA/GDPR Compliance**: Patient data protection is built into the system
- **Input Sanitization**: All user inputs are sanitized in `models/validation.py`
- **Database Security**: Use `./secure_database.sh` to set proper file permissions
- **South African ID Validation**: Built-in validation for SA ID numbers
- **Audit Trails**: System maintains logs for healthcare data access