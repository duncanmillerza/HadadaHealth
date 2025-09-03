// --- Save/Cancel Patient Edits Logic moved from patients.html ---

async function savePatientEdits() {
  const updatedData = {};
  document.querySelectorAll('#patient-modal input, #patient-modal select').forEach(input => {
    if (input.dataset.originalId) {
      const cleanKey = input.dataset.originalId.replace('modal-', '');
      updatedData[cleanKey] = input.value.trim();
    }
  });

  const selectedICDCodes = Array.from(document.querySelectorAll('#selected-icd10-codes .selected-icd10')).map(div => div.dataset.code);
  updatedData.icd10_codes = JSON.stringify(selectedICDCodes);

  const validationMessages = document.getElementById('icd10-validation-message').innerText.trim();
  if (validationMessages) {
    alert("ICD-10 validation failed:\n\n" + validationMessages);
    return;
  }

  try {
    const res = await fetch(`/update-patient/${currentPatientId}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(updatedData)
    });
    if (!res.ok) throw new Error('Failed to update patient');
    alert('Patient updated successfully!');
    const patientIndex = allPatients.findIndex(p => p.id === currentPatientId);
    if (patientIndex !== -1) {
      Object.assign(allPatients[patientIndex], updatedData);
    }
    closePatientModal();
    openPatientModal(allPatients[patientIndex]);
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

function cancelPatientEditing() {
  closePatientModal();
  loadPatients();
}
let currentPatientId = null;
let allICD10Codes = [];

function openPatientModal(patient) {
  currentPatientId = patient.id;
  // Default to Personal tab on open
  showTab('personal');

  // Populate generic fields
  for (const key in patient) {
    const el = document.getElementById('modal-' + key);
    if (el) {
      el.textContent = patient[key] || "-";
    }
  }

  // Hide blank fields in Funding and Consent tabs (view mode)
  ['funding', 'consent'].forEach(tab => {
    document.querySelectorAll(`#tab-${tab} p`).forEach(p => {
      const span = p.querySelector('span');
      if (!span || !span.textContent.trim() || span.textContent.trim() === '-') {
        p.style.display = 'none';
      } else {
        p.style.display = 'block';
      }
    });
  });

  // Header name
  const nameEl = document.getElementById('modal-name');
  if (nameEl) {
    nameEl.textContent = `${patient.first_name || "-"} ${patient.surname || "-"}`;
  }

  // Signature
  const sig = document.getElementById('signature-display');
  if (sig) {
    if (patient.signature_data) {
      sig.innerHTML = `
        <img src="${patient.signature_data}" alt="Signature"
          style="max-width: 100%; height: auto; border: 1px solid #ccc; padding: 0.5rem; border-radius: 6px;">
      `;
    } else {
      sig.innerHTML = '<p>No signature available.</p>';
    }
  }

  // Buttons
  const editBtn = document.getElementById('edit-btn');
  if (editBtn) {
    editBtn.textContent = 'Edit';
    editBtn.onclick = enablePatientEditing;
    editBtn.style.display = 'inline-block';
  }

  const cancelBtn = document.getElementById('cancel-edit-btn');
  if (cancelBtn) cancelBtn.style.display = 'none';

  const closeBtn = document.getElementById('close-btn');
  if (closeBtn) closeBtn.style.display = 'inline-block';

  // Modal visibility
  const modal = document.getElementById('patient-modal');
  if (modal) modal.style.display = 'block';

  const backdrop = document.getElementById('modal-backdrop');
  if (backdrop) backdrop.style.display = 'block';

  // ICD-10 load
  const icdContainer = document.getElementById('selected-icd10-codes');
  if (icdContainer) icdContainer.innerHTML = '';

  if (patient.icd10_codes) {
    try {
        const codes = Array.isArray(patient.icd10_codes)
            ? patient.icd10_codes
            : JSON.parse(patient.icd10_codes);
      codes.forEach(code => {
        const div = document.createElement('div');
        div.textContent = code;
        div.style.border = '1px solid #ccc';
        div.style.borderRadius = '6px';
        div.style.padding = '0.25rem 0.5rem';
        div.style.marginBottom = '0.25rem';
        div.style.background = '#f4f4f4';
        icdContainer.appendChild(div);
      });
    } catch (e) {
      console.error("Failed to parse ICD-10 codes");
    }
  }

  // Populate view-mode ICD-10 list
  const codeList = document.getElementById('icd10-code-list');
  const emptyMsg = document.getElementById('icd10-code-empty');
  if (codeList && emptyMsg) {
    codeList.innerHTML = '';
    if (patient.icd10_codes) {
      try {
        const codes = Array.isArray(patient.icd10_codes)
          ? patient.icd10_codes
          : JSON.parse(patient.icd10_codes);
        if (codes.length === 0) {
          emptyMsg.style.display = 'block';
        } else {
          emptyMsg.style.display = 'none';
          codes.forEach(code => {
            const li = document.createElement('li');
            li.textContent = code;
            codeList.appendChild(li);
          });
        }
      } catch (e) {
        console.error("Failed to parse ICD-10 codes for view-mode list", e);
        emptyMsg.style.display = 'block';
      }
    } else {
      emptyMsg.style.display = 'block';
    }
  }

  waitForICD10CodesAndLoad(patient);
  showICD10ViewMode();
}

function closePatientModal() {
  const modal = document.getElementById('patient-modal');
  const backdrop = document.getElementById('modal-backdrop');
  if (modal) modal.style.display = 'none';
  if (backdrop) backdrop.style.display = 'none';
  location.reload(); // Optional refresh to re-sync
}

function showTab(tab) {
  document.querySelectorAll('.tab-content').forEach(div => div.style.display = 'none');
  const active = document.getElementById('tab-' + tab);
  if (active) active.style.display = 'block';
}

function showICD10EditMode() {
  document.getElementById('icd10-view-mode').style.display = 'none';
  document.getElementById('icd10-edit-mode').style.display = 'block';
}

function showICD10ViewMode() {
  document.getElementById('icd10-view-mode').style.display = 'block';
  document.getElementById('icd10-edit-mode').style.display = 'none';
}

function loadSavedICD10Codes(patient) {
  const codeList = document.getElementById('icd10-code-list');
  const emptyMsg = document.getElementById('icd10-code-empty');
  codeList.innerHTML = '';
  const selectedContainer = document.getElementById('selected-icd10-codes');
  selectedContainer.innerHTML = '';
  console.log("ICD-10 codes passed to loader:", patient.icd10_codes);
  console.log("allICD10Codes available:", allICD10Codes);
  
  if (patient.icd10_codes) {
    try {
      const codes = Array.isArray(patient.icd10_codes)
        ? patient.icd10_codes
        : JSON.parse(patient.icd10_codes);

      if (codes.length === 0) {
        emptyMsg.style.display = 'block';
      } else {
        emptyMsg.style.display = 'none';
        codes.forEach(code => {
          const full = allICD10Codes.find(c => c.code === code);
          const display = full ? `${full.code}: ${full.description}` : `${code}: (Unmatched)`;

          const li = document.createElement('li');
          li.textContent = display;
          codeList.appendChild(li);

          addICD10Code(full || { code: code, description: '(Unmatched)' });
        });
      }
    } catch (e) {
      console.error("Invalid ICD-10 JSON", e);
      emptyMsg.style.display = 'block';
    }
  } else {
    emptyMsg.style.display = 'block';
  }
}

function waitForICD10CodesAndLoad(patient) {
  if (allICD10Codes.length === 0) {
    setTimeout(() => waitForICD10CodesAndLoad(patient), 100);
  } else {
    loadSavedICD10Codes(patient);
  }
}

function addICD10Code(item) {
  const selectedDiv = document.getElementById('selected-icd10-codes');
  if (Array.from(selectedDiv.querySelectorAll('.selected-icd10')).some(div => div.dataset.code === item.code)) return;

  const entry = document.createElement('div');
  entry.className = 'selected-icd10';
  entry.style.display = 'flex';
  entry.style.alignItems = 'center';
  entry.style.justifyContent = 'space-between';
  entry.style.padding = '0.25rem';
  entry.style.marginBottom = '4px';
  entry.style.border = '1px solid #ccc';
  entry.style.borderRadius = '4px';
  entry.style.background = item.is_pmb === "Y" ? '#e6ffe6' : '#f4f4f4';
  entry.dataset.code = item.code;

  const label = document.createElement('span');
  label.textContent = `${item.code}: ${item.description}`;
  label.style.flex = '1';

  const removeBtn = document.createElement('span');
  removeBtn.textContent = '❌';
  removeBtn.style.cursor = 'pointer';
  removeBtn.style.color = 'red';
  removeBtn.style.marginLeft = '12px';
  removeBtn.onclick = () => {
    selectedDiv.removeChild(entry);
    validateICD10Selection();
  };

  entry.appendChild(label);
  entry.appendChild(removeBtn);
  selectedDiv.appendChild(entry);
  validateICD10Selection();
}

function validateICD10Selection() {
  const selectedDivs = Array.from(document.querySelectorAll('#selected-icd10-codes div'));
  const selectedCodes = selectedDivs.map(div => div.textContent.split(':')[0].trim());
  const selectedDetails = allICD10Codes.filter(c => selectedCodes.includes(c.code));
  const messages = [];

  const hasPrimary = selectedDetails.some(c => c.valid_as_primary === "Y");
  if (!hasPrimary) messages.push("❗ You must include at least one primary diagnosis code.");

  selectedDetails.forEach(code => {
    if (code.is_asterisk === "Y") {
      const hasDagger = selectedDetails.some(c => c.is_dagger === "Y");
      if (!hasDagger) messages.push(`❗ ${code.code} requires a dagger (†) code.`);
    }
    if (code.is_sequelae === "Y" && selectedDetails.length === 1) {
      messages.push(`❗ ${code.code} is a sequela and cannot be used alone.`);
    }
  });

  document.getElementById('icd10-validation-message').innerHTML = messages.join('<br>');
}

// ICD10 autocomplete load
fetch("/api/icd10-codes?query=")
  .then(res => res.json())
  .then(data => {
    allICD10Codes = data;

    const icd10Search = document.getElementById('icd10-search');
    if (icd10Search) {
      icd10Search.addEventListener('input', function () {
        const query = this.value.trim().toLowerCase();
        const resultsDiv = document.getElementById('icd10-results');
        resultsDiv.innerHTML = '';
        if (query.length < 2) return;

        const filtered = allICD10Codes.filter(code =>
          code.code.toLowerCase().includes(query) ||
          code.description.toLowerCase().includes(query)
        );

        filtered.forEach(item => {
          const div = document.createElement('div');
          div.innerHTML = `<strong>${item.code}</strong>: ${item.description}` +
                          (item.is_pmb === "Y" ? ' <span style="color:green;">(PMB)</span>' : '');
          div.style.padding = '0.25rem';
          div.style.cursor = 'pointer';
          div.style.borderBottom = '1px solid #eee';
          div.addEventListener('click', () => addICD10Code(item));
          resultsDiv.appendChild(div);
        });
      });
    }
  });
// Enables patient editing mode in the modal, especially for ICD-10 tab
function enablePatientEditing() {
  // Enable editing of all fields: replace view spans with inputs
  document.querySelectorAll('#patient-modal span[id^="modal-"]').forEach(span => {
    const fieldId = span.id;
    const currentValue = span.textContent.trim() === '-' ? '' : span.textContent.trim();
    const input = document.createElement('input');
    input.type = 'text';
    input.id = fieldId;
    input.dataset.originalId = fieldId;
    input.value = currentValue;
    input.style.width = '100%';
    // Replace the span with the input
    span.parentNode.replaceChild(input, span);
  });

  const search = document.getElementById('icd10-search');
  const editSection = document.getElementById('icd10-edit-mode');
  if (search) search.style.display = 'block';
  if (editSection) editSection.style.display = 'block';

  // Toggle Edit button to Save
  const editBtn = document.getElementById('edit-btn');
  const cancelBtn = document.getElementById('cancel-edit-btn');
  const closeBtn = document.getElementById('close-btn');
  if (editBtn) {
    editBtn.textContent = 'Save';
    editBtn.onclick = savePatientEdits;
  }
  // Show Cancel, hide Close while editing
  if (cancelBtn) cancelBtn.style.display = 'inline-block';
  if (closeBtn) closeBtn.style.display = 'none';
}