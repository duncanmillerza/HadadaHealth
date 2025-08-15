function openMedicalHistoryModal(patientId) {
    const modal = document.getElementById("medical-history-modal");
    if (!modal) {
      fetch("/static/fragments/medical-history.html")
        .then(response => response.text())
        .then(html => {
          document.body.insertAdjacentHTML("beforeend", html);
          openMedicalHistoryModal(patientId); // Recall after loading
        });
      return;
    }
  
    modal.style.display = "block";
  
    fetch(`/api/patient/${patientId}/medical-history`)
      .then(response => response.json())
      .then(data => {
        document.getElementById("ai-history-content").innerHTML = data.summary || "No summary available.";
        document.getElementById("ai-history-date").innerText = data.generated_at || "Unknown";
      })
      .catch(error => {
        console.error("Error loading medical history:", error);
        document.getElementById("ai-history-content").innerText = "Error loading summary.";
        document.getElementById("ai-history-date").innerText = "—";
      });
  }
  
  function closeMedicalHistoryModal() {
    const modal = document.getElementById("medical-history-modal");
    if (modal) modal.style.display = "none";
  }
  
  function regenerateMedicalHistory(patientId) {
    fetch(`/api/patient/${patientId}/medical-history/regenerate`, {
      method: 'POST'
    })
      .then(() => {
        openMedicalHistoryModal(patientId); // Refresh after regenerate
      })
      .catch(error => {
        console.error("Error regenerating medical history:", error);
      });
  }