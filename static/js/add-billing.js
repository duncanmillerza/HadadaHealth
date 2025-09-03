


// Add a new billing row by cloning the first row and resetting its values
function addBillingRow() {
  const tableBody = document.getElementById("billing-modal-table-body");
  const firstRow = tableBody.querySelector(".billing-modal-entry");
  if (!firstRow) return;
  const newRow = firstRow.cloneNode(true);
  newRow.querySelectorAll("input").forEach(input => {
    if (input.type === "number") input.value = 1;
    else input.value = "";
  });
  newRow.querySelector(".description-cell").textContent = "—";
  newRow.querySelector(".rate-cell").textContent = "—";
  newRow.querySelector(".total-cell").textContent = "—";
  // Remove any data attributes
  newRow.removeAttribute("data-base-rate");
  // Reset modifier select
  const select = newRow.querySelector("select[name='billing_modifier[]']");
  if (select) {
    select.innerHTML = '<option value="">None</option>';
    loadModifiers(select);
  }
  tableBody.appendChild(newRow);
}

// Remove billing row (if more than one row remains)
function removeBillingRow(button) {
  const row = button.closest("tr");
  const table = document.getElementById("billing-modal-table-body");
  if (table.rows.length > 1) table.removeChild(row);
  updateOverallTotal();
}

// Populate description and rate when code is entered
async function populateBillingRow(input) {
  const codeInput = input.value.split(" - ")[0];
  try {
    const response = await fetch("/api/billing_codes");
    const codes = await response.json();
    const match = codes.find(c => c.code === codeInput);
    if (match) {
      const row = input.closest("tr");
      row.dataset.baseRate = match.base_fee;
      row.querySelector(".description-cell").textContent = match.description;
      row.querySelector(".rate-cell").textContent = match.base_fee.toFixed(2);
      const quantity = parseInt(row.querySelector("input[name='number[]']").value) || 1;
      row.querySelector(".total-cell").textContent = (match.base_fee * quantity).toFixed(2);
      updateOverallTotal();
    }
  } catch (err) {
    console.error("Error populating billing row:", err);
  }
}

// Load billing modifiers into a select element
async function loadModifiers(selectElement) {
  try {
    // Use currentProfession if available, otherwise fallback to no filter
    const profession = window.currentProfession || "";
    const response = await fetch(`/api/billing_modifiers?profession=${encodeURIComponent(profession)}`);
    const billing_modifiers = await response.json();
    billing_modifiers.forEach(mod => {
      const option = document.createElement("option");
      option.value = mod.modifier_code;
      option.textContent = `${mod.modifier_code} - ${mod.modifier_description}`;
      option.dataset.factor = mod.modifier_multiplier;
      selectElement.appendChild(option);
    });
  } catch (err) {
    console.error("Failed to load billing_modifiers", err);
  }
}

// Apply selected modifier to recalculate rate and total
function applyModifier(select) {
  const row = select.closest("tr");
  const baseRate = parseFloat(row.dataset.baseRate || 0);
  const factor = parseFloat(select.selectedOptions[0].dataset.factor || 1);
  const adjustedRate = baseRate * factor;
  row.querySelector(".rate-cell").textContent = adjustedRate.toFixed(2);
  const quantity = parseInt(row.querySelector("input[name='number[]']").value) || 1;
  row.querySelector(".total-cell").textContent = (adjustedRate * quantity).toFixed(2);
  updateOverallTotal();
}

// Recalculate row total when number changes
function recalculateTotal(input) {
  const row = input.closest("tr");
  const rateText = row.querySelector(".rate-cell").textContent;
  const rate = parseFloat(rateText);
  const quantity = parseInt(input.value) || 1;
  if (!isNaN(rate)) {
    row.querySelector(".total-cell").textContent = (rate * quantity).toFixed(2);
  }
  updateOverallTotal();
}

// Update the overall total for all billing entries
function updateOverallTotal() {
  const totalCells = document.querySelectorAll("#billing-modal-table-body .total-cell");
  let sum = 0;
  totalCells.forEach(cell => {
    const value = parseFloat(cell.textContent);
    if (!isNaN(value)) sum += value;
  });
  document.getElementById("overall-total").textContent = sum.toFixed(2);
}
// Save Billing button handler for billing modal
async function submitBillingModal() {
  const tableBody = document.getElementById("billing-modal-table-body");
  const rows = tableBody.querySelectorAll(".billing-modal-entry");
  const bookingId = window.currentBookingId;

  const entries = Array.from(rows).map(row => ({
    code_id: row.querySelector("input[name='code_id[]']").value.split(" - ")[0],
    billing_modifier: row.querySelector("select[name='billing_modifier[]']").value || "",
    final_fee: parseFloat(row.querySelector(".total-cell").textContent) || 0
  })).filter(e => e.code_id);

  const payload = {
    session: {
      id: bookingId,
      patient_id: window.currentPatientId,
      therapist_id: window.currentTherapistId,
      session_date: new Date().toISOString().split("T")[0],
      notes: "",
      total_amount: parseFloat(document.getElementById("overall-total").textContent) || 0
    },
    entries
  };

  try {
    const res = await fetch("/billing-sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to save billing");
    alert("Billing saved successfully.");
    document.getElementById("billing-modal").style.display = "none";
  } catch (err) {
    console.error(err);
    alert("Error saving billing.");
  }
}

// Load existing billing entries for this appointment
async function loadExistingBillingEntries(bookingId) {
    try {
      const res = await fetch(`/billing-sessions/${window.currentPatientId}`);
      if (!res.ok) throw new Error("Failed to load billing sessions");
      const sessions = await res.json();
      const session = sessions.find(s => s.id === bookingId);
      if (!session) return; // No billing saved for this appointment
  
      const tableBody = document.getElementById("billing-modal-table-body");
      tableBody.innerHTML = ""; // Clear existing rows
  
      for (const entry of session.entries) {
        const row = document.createElement("tr");
        row.className = "billing-modal-entry";
        row.dataset.baseRate = entry.final_fee;
  
        row.innerHTML = `
          <td><input name="code_id[]" value="${entry.code_id}" oninput="populateBillingRow(this)" style="width:100%;"></td>
          <td class="description-cell">—</td>
          <td><input type="number" name="number[]" value="1" min="1" onchange="recalculateTotal(this)" style="width:60px;"></td>
          <td><select name="billing_modifier[]" onchange="applyModifier(this)" style="width:100%;"><option value="">None</option></select></td>
          <td class="rate-cell">${entry.final_fee.toFixed(2)}</td>
          <td class="total-cell">${entry.final_fee.toFixed(2)}</td>
          <td><button type="button" class="remove-row-btn" onclick="removeBillingRow(this)">✕</button></td>
        `;
        tableBody.appendChild(row);
  
        // Load modifiers
        const select = row.querySelector("select[name='billing_modifier[]']");
        await loadModifiers(select);
        if (entry.billing_modifier) {
          select.value = entry.billing_modifier;
        }
  
        // Load description and rate
        await populateBillingRow(row.querySelector("input[name='code_id[]']"));
      }
      updateOverallTotal();
    } catch (err) {
      console.error("Error loading billing entries:", err);
    }
  }

  // Make functions globally accessible
window.loadExistingBillingEntries = loadExistingBillingEntries;
window.addBillingRow = addBillingRow;
window.removeBillingRow = removeBillingRow;
window.populateBillingRow = populateBillingRow;
window.loadModifiers = loadModifiers;
window.applyModifier = applyModifier;
window.recalculateTotal = recalculateTotal;
window.updateOverallTotal = updateOverallTotal;
window.submitBillingModal = submitBillingModal;