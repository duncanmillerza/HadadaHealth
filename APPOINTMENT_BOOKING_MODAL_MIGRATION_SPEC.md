# Appointment Booking Modal Migration Specification

## Overview
Migrate from the current separate appointment-type selection and booking modals to a unified booking experience that integrates appointment type selection with comprehensive booking details.

## Current State Analysis

### Current Booking Modal (week-calendar.html)
**Fields:**
- Date
- Patient Name (with search functionality)
- Profession (filters therapist selection)
- Therapist
- Duration (minutes)
- Start Time
- End Time
- Notes
- Color
- Billing Code (single selection with description/fee display)
- Hidden: editing-appt-id

**Features:**
- Patient search modal integration
- Profession-based therapist filtering
- Real-time billing code info display
- Color picker with hex display
- Auto-calculation of end time

### Current Appointment Type Modal (appointment-type-modal.html)
**Features:**
- Hierarchical appointment type tree display
- Category-based organization
- Type preview with color, duration, description
- Loading states and error handling
- Search functionality (hidden/future enhancement)

### Current Booking Modal Fragment (booking-modal.html)
**Fields (Simplified):**
- Patient
- Therapist
- Name
- Date
- Time
- Duration
- End (readonly)
- Notes
- Hidden: editing-appt-id, booking-colour

## Proposed Solution

### Unified Modal Structure
Create a multi-step modal that combines appointment type selection with comprehensive booking details:

```
┌─ Step 1: Appointment Type Selection ─┐
│  - Hierarchical type tree             │
│  - Search/filter functionality        │
│  - Type preview                       │
│  - Selected type confirmation         │
└─────────────────────────────────────┘
           ↓ (Continue)
┌─ Step 2: Booking Details ─────────────┐
│  - Patient selection (w/ search)      │
│  - Therapist selection (w/ profession)│
│  - Date & time scheduling             │
│  - Duration (pre-filled, editable)    │
│  - Notes                              │
│  - Billing codes (from appointment)   │
│  - Color (from appointment type)      │
└─────────────────────────────────────┘
```

## Technical Requirements

### 1. Modal Navigation
- **Forward Navigation**: Step 1 → Step 2 on appointment type selection
- **Backward Navigation**: "Back" button to return to Step 1 from Step 2
- **Progress Indicator**: Visual indication of current step
- **Validation**: Step 1 requires appointment type selection

### 2. Data Integration
- **Appointment Type Defaults**: Step 2 fields auto-populate from selected appointment type:
  - Duration from `effective_duration`
  - Color from appointment type color
  - Billing codes from `default_billing_codes` array
  - Notes template from `default_notes`
- **User Context Defaults**: Auto-populate from current logged-in user:
  - Profession from user's profession
  - Therapist pre-selected to current user
- **Override Permissions**: 
  - Regular users: Can modify all fields except therapist (locked to themselves)
  - Admin users: Can change therapist to any therapist in the system
- **State Persistence**: Maintain selections when navigating between steps

### 3. Enhanced Features
- **Multiple Billing Codes**: Support for multiple billing codes per appointment (from appointment type defaults)
- **Smart Defaults**: Auto-populate profession and therapist from current logged-in user
- **User Override**: Allow changing therapist/profession if user has admin permissions
- **Validation**: Comprehensive validation before submission
- **Loading States**: Smooth transitions and loading indicators

### 4. Modal Structure (Updated for Confirmed Requirements)
```html
<div id="unified-booking-modal" class="modal">
  <div class="modal-content large-modal">
    <!-- Modal Header with Progress -->
    <div class="modal-header">
      <h3 id="modal-title">Select Appointment Type</h3>
      <div class="progress-indicator">
        <span class="step active" data-step="1">1</span>
        <span class="step" data-step="2">2</span>
      </div>
      <span class="close-button">&times;</span>
    </div>
    
    <!-- Step 1: Appointment Type Selection -->
    <div id="appointment-type-step" class="modal-step active">
      <!-- Hierarchical appointment type tree -->
      <!-- Search functionality -->
      <!-- Type preview with selection confirmation -->
    </div>
    
    <!-- Step 2: Booking Details -->
    <div id="booking-details-step" class="modal-step">
      <!-- Selected Appointment Type Display with Change Option -->
      <div class="selected-appointment-type">
        <span class="appointment-type-display"></span>
        <button type="button" class="change-type-btn">Change Type</button>
      </div>
      
      <!-- Comprehensive Booking Form -->
      
      <!-- Billing Codes Table with Modifiers -->
      <div class="billing-codes-section">
        <h4>Billing Codes</h4>
        <table id="booking-billing-table" class="billing-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Description</th>
              <th>Qty</th>
              <th>Modifier</th>
              <th>Rate</th>
              <th>Total</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="booking-billing-table-body">
            <!-- Dynamic rows example:
            <tr class="billing-code-row">
              <td><select class="billing-code-select"><option value="72501">72501</option></select></td>
              <td class="billing-description">Rehabilitation requiring undivided attention...</td>
              <td><input type="number" class="billing-quantity" value="1" min="1"></td>
              <td>
                <select class="billing-modifier-select">
                  <option value="">No Modifier</option>
                  <option value="0001" data-multiplier="1">0001 - Late Cancellation Fee</option>
                  <option value="0003" data-multiplier="0.85">0003 - External Equipment Use Discount</option>
                </select>
              </td>
              <td class="billing-rate">R336.40</td>
              <td class="billing-line-total">R336.40</td>
              <td><button type="button" class="remove-billing-row">×</button></td>
            </tr>
            -->
          </tbody>
          <tfoot>
            <tr>
              <td colspan="5"><strong>Grand Total:</strong></td>
              <td id="billing-grand-total">R0.00</td>
              <td>
                <button type="button" class="add-billing-row-btn">+ Add Code</button>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
      
      <!-- All Other Override-able Fields -->
    </div>
    
    <!-- Modal Footer with Sequential Navigation -->
    <div class="modal-footer">
      <button id="back-to-step1-button" style="display: none;">← Back</button>
      <button id="continue-to-step2-button" disabled>Continue →</button>
      <button id="save-booking-button" style="display: none;">Save Booking</button>
      <button id="cancel-button">Cancel</button>
    </div>
  </div>
</div>
```

### 5. Enhanced Features for Confirmed Requirements

#### A. Sequential Flow Navigation
- **Step 1**: Must select appointment type before proceeding
- **Step 2**: Shows selected type with option to change (returns to Step 1)
- **Existing Appointments**: Direct to Step 2 with type change option
- **Validation**: Enforce appointment type selection before Step 2

#### B. Field Override System
- **Appointment Type Auto-Population**: Duration, color, billing codes, notes from selected type
- **User Context Auto-Population**: Profession and therapist from logged-in user
- **Permission-Based Control**: 
  - Regular users: Can edit all fields except therapist (locked to self)
  - Admin users: Can change therapist to anyone, edit all fields
- **Visual Indicators**: Show which fields are auto-populated vs. user-modified
- **Reset Options**: 
  - "Use Appointment Type Defaults" - revert type-specific fields
  - "Reset to My Defaults" - revert to user's profession/therapist

#### C. Multiple Billing Codes with Database-Driven Modifiers
- **Dynamic Table**: Add/remove billing codes beyond appointment type defaults
- **Full Billing Code Support**:
  - Code selection with description lookup from billing codes database
  - Quantity field (default: 1)
  - Modifier dropdown populated from `billing_modifiers` table
  - Rate display (auto-populated from code database)
  - Line total calculation (quantity × rate × modifier_multiplier)
- **Database Integration**:
  - **Modifiers Source**: Load from `billing_modifiers` table
  - **Profession Filtering**: Filter modifiers by user's profession where applicable
  - **Modifier Data**: Display `modifier_code`, `modifier_name`, and `modifier_description`
  - **Multiplier Application**: Apply `modifier_multiplier` to rate calculations
  - **Validation**: Use actual modifier codes from database
- **Table Features**:
  - Drag & drop reordering
  - Duplicate row functionality
  - Delete individual rows
  - Validation: Prevent duplicate code+modifier combinations
- **Calculations**:
  - Real-time line totals with modifier multipliers applied
  - Grand total of all billing codes
  - Total quantity count
  - Visual indication when modifiers affect pricing
- **Default Population**: Start with appointment type's `default_billing_codes` array
- **Manual Override**: Users can add/remove/modify any billing codes and modifiers

#### D. Large Modal Design
- **Dimensions**: max-width: 900px, max-height: 95vh
- **Layout**: Two-column layout for Step 2 (form on left, preview on right)
- **Responsive**: Collapse to single column on mobile
- **Scrolling**: Smooth scrolling within modal body

#### E. User Context Integration
- **Session Data**: Retrieve current user's profession and ID from session/auth
- **Default Behavior**: 
  - Profession dropdown pre-selected to user's profession
  - Therapist dropdown pre-selected to current user
  - Show "(You)" indicator next to user's name in therapist dropdown
- **Permission Checks**:
  - Check if user has admin/manager role
  - Lock therapist field for regular users
  - Show permission-based UI hints
- **Fallback Handling**:
  - If user profession not found, show all professions
  - If user not in therapist list, allow selection of any therapist
- **Visual Cues**:
  - Locked fields show lock icon
  - Auto-populated fields have subtle background color
  - Tooltip explaining why field is locked/auto-populated

## Implementation Task List

### Phase 1: Modal Structure & Navigation
- [ ] Create unified modal HTML structure
- [ ] Implement step-based navigation system
- [ ] Add progress indicator component
- [ ] Create CSS for multi-step layout
- [ ] Implement modal state management

### Phase 2: Appointment Type Integration
- [ ] Move appointment type tree into Step 1
- [ ] Implement appointment type selection handling
- [ ] Add type preview functionality
- [ ] Handle loading and error states
- [ ] Create continue button validation

### Phase 3: Enhanced Booking Form
- [ ] Migrate comprehensive booking fields to Step 2
- [ ] Implement auto-population from appointment type
- [ ] Add user context auto-population (profession/therapist)
- [ ] Implement permission-based field locking
- [ ] Add multiple billing codes table with modifiers support
- [ ] Implement billing code lookup with description/rate auto-population
- [ ] Add quantity and modifier fields for each billing code
- [ ] Implement real-time calculation (line totals and grand total)
- [ ] Integrate patient search functionality
- [ ] Add visual indicators for auto-populated fields

### Phase 4: Data Flow & Integration
- [ ] Connect appointment type selection to booking form
- [ ] Implement field pre-population logic
- [ ] Create API endpoint for loading billing modifiers by profession
- [ ] Integrate billing_modifiers table data into modifier dropdowns
- [ ] Implement modifier multiplier calculations
- [ ] Add form validation for all fields (including modifier validation)
- [ ] Handle form submission with combined data (codes + modifiers + multipliers)
- [ ] Maintain editing functionality for existing appointments

### Phase 5: Enhanced Features
- [ ] Add billing codes drag & drop reordering
- [ ] Implement duplicate row functionality
- [ ] Add billing code validation (prevent duplicate code+modifier)
- [ ] Implement smart therapist filtering and user context
- [ ] Add auto-calculation features (end time, billing totals)
- [ ] Enhance color picker integration
- [ ] Add keyboard navigation support
- [ ] Add field locking and permission-based UI

### Phase 6: Testing & Integration
- [ ] Test modal on different screen sizes (ensure scrolling works)
- [ ] Test appointment type selection flow
- [ ] Test booking creation and editing
- [ ] Integration testing with calendar system
- [ ] Cross-browser compatibility testing

### Phase 7: Migration & Cleanup
- [ ] Update calendar click handlers to use new modal
- [ ] Remove old modal implementations
- [ ] Update related JavaScript files
- [ ] Clean up unused CSS
- [ ] Update documentation

## Requirements Confirmed ✅

1. **Step Navigation**: Sequential flow (Step 1 → Step 2) - users must select appointment type first
2. **Field Override**: Users can edit all auto-populated fields (duration, billing codes, color, etc.)
3. **Multiple Billing Codes**: Support multiple billing codes per appointment beyond appointment type defaults
4. **Existing Appointments**: Jump to Step 2 but allow changing appointment type which updates defaults
5. **Modal Size**: Larger modal to accommodate more content comfortably
6. **Integration Points**: Calendar booking workflow integration

## Success Criteria

- [ ] Single modal handles both appointment type selection and booking details
- [ ] Seamless data flow from appointment type to booking form
- [ ] All existing booking functionality preserved and enhanced
- [ ] Improved user experience with guided workflow
- [ ] Mobile-responsive design with proper scrolling
- [ ] No regression in calendar integration
- [ ] Clean code architecture with reusable components

## API Requirements

### New Endpoints Needed:
1. **GET `/api/billing/modifiers`** - Load all billing modifiers
   - Optional query param: `profession` to filter by profession
   - Response format:
   ```json
   [
     {
       "modifier_code": "0001",
       "modifier_name": "Late Cancellation Fee", 
       "modifier_description": "Applied when an appointment is not cancelled...",
       "modifier_effect": "Full fee may be charged for missed appointment",
       "modifier_multiplier": 1,
       "profession": "Physiotherapy"
     }
   ]
   ```

2. **Enhanced appointment booking endpoints** to handle:
   - Multiple billing codes with modifiers
   - Modifier multipliers in calculations
   - User context (profession/therapist auto-population)

## Files to Modify

### Create New:
- `/static/fragments/unified-booking-modal.html`
- `/static/css/unified-booking-modal.css`
- `/static/js/unified-booking-modal.js`
- **API controller for billing modifiers** (if not exists)

### Modify Existing:
- `/templates/week-calendar.html` (remove inline modal)
- `/templates/week-calendar-page.html` (integration)
- Calendar JavaScript files for modal invocation
- Appointment management JavaScript

### Remove/Deprecate:
- `/static/fragments/booking-modal.html` (replaced)
- `/static/fragments/appointment-type-modal.html` (integrated)
- Related CSS and JavaScript files