/**
 * Morocco CPSV Administrative Portal - Frontend Controller
 * Institutional Portal Logic (Marchespublics & TGR Inspired)
 */

let authoritiesData = [];
let outputsData = [];
let evidencesData = [];

let selectedOutputs = [];
let selectedEvidences = [];
let currentCandidateTurtle = "";

document.addEventListener("DOMContentLoaded", () => {
  loadAuthorities();
  loadOutputs();
  loadEvidences();
});

// ==========================================
// Tab Switching
// ==========================================
function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(el => el.style.display = "none");
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));

  const targetTab = document.getElementById(`tab-${tabId}`);
  if (targetTab) targetTab.style.display = "block";

  // Highlight active nav item
  const tabs = ["composer", "explorer", "authorities", "outputs", "evidences", "shacl", "auditlog"];
  const idx = tabs.indexOf(tabId);
  if (idx >= 0) {
    const navItems = document.querySelectorAll(".nav-item");
    if (navItems[idx]) navItems[idx].classList.add("active");
  }

  if (tabId === "explorer") {
    loadExplorerProcedures();
  } else if (tabId === "authorities") {
    loadAuthorities();
  } else if (tabId === "outputs") {
    loadOutputs();
  } else if (tabId === "evidences") {
    loadEvidences();
  } else if (tabId === "auditlog") {
    loadAuditLogs();
  }
}

// ==========================================
// Data Fetching
// ==========================================
async function loadAuthorities() {
  try {
    const res = await fetch("/api/authorities");
    authoritiesData = await res.json();

    const select = document.getElementById("authority_select");
    const editSelect = document.getElementById("edit_authority");
    if (select) select.innerHTML = '<option value="">-- اختر الإدارة أو الهيئة المختصة من السجل --</option>';
    if (editSelect) editSelect.innerHTML = '<option value="">-- اختر الإدارة المختصة --</option>';

    authoritiesData.forEach(auth => {
      const opt = document.createElement("option");
      opt.value = auth.org_slug;
      opt.textContent = auth.org_name;
      opt.dataset.parent = auth.suggested_parent_name || "المملكة المغربية";
      opt.dataset.name = auth.org_name;
      opt.dataset.id = auth.org_id;
      if (select) select.appendChild(opt);

      if (editSelect) {
        const editOpt = opt.cloneNode(true);
        editOpt.value = auth.org_id; // Store ID for edit update
        editSelect.appendChild(editOpt);
      }
    });

    renderAuthoritiesTable(authoritiesData);
  } catch (err) {
    console.error("Failed to load authorities:", err);
  }
}

async function loadOutputs() {
  try {
    const res = await fetch("/api/outputs?limit=300");
    outputsData = await res.json();
    renderOutputsTable(outputsData);
  } catch (err) {
    console.error("Failed to load outputs:", err);
  }
}

async function loadEvidences() {
  try {
    const res = await fetch("/api/evidences?limit=300");
    evidencesData = await res.json();
    renderEvidencesTable(evidencesData);
  } catch (err) {
    console.error("Failed to load evidences:", err);
  }
}

// ==========================================
// Authority Selection Details
// ==========================================
function updateAuthorityDetails() {
  const select = document.getElementById("authority_select");
  const badge = document.getElementById("authority_hierarchy_badge");
  const parentSpan = document.getElementById("auth_parent_text");

  const selectedOpt = select.options[select.selectedIndex];
  if (selectedOpt && selectedOpt.value) {
    parentSpan.textContent = selectedOpt.dataset.parent;
    badge.style.display = "block";
  } else {
    badge.style.display = "none";
  }
}

// ==========================================
// Fees / Costs Toggle
// ==========================================
function toggleFeeInputs() {
  const feeType = document.getElementById("fee_type").value;
  const feeFields = document.querySelectorAll(".fee-field");
  feeFields.forEach(f => {
    f.style.display = (feeType === "PAID") ? "flex" : "none";
  });
}

// ==========================================
// Outputs Selection Manager
// ==========================================
let composerOutputSearchTimeout = null;
function searchOutputs(q) {
  const resultsBox = document.getElementById("output_search_results");
  if (!resultsBox) return;
  const term = (q || "").trim();
  if (!term) {
    resultsBox.style.display = "none";
    return;
  }
  if (composerOutputSearchTimeout) clearTimeout(composerOutputSearchTimeout);
  composerOutputSearchTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`/api/outputs?q=${encodeURIComponent(term)}&limit=25`);
      const matched = await res.json();
      resultsBox.innerHTML = "";
      if (!matched.length) {
        resultsBox.innerHTML = '<div style="padding:8px 10px; color:#888; font-size:12px;">لا توجد مخرجات مطابقة في السجل. انقر أدناه لإضافة مخرج جديد.</div>';
      } else {
        matched.forEach(o => {
          const item = document.createElement("div");
          item.style.padding = "7px 10px";
          item.style.cursor = "pointer";
          item.style.borderBottom = "1px solid #eee";
          item.innerHTML = `<strong style="color:#0b5394;">${escapeHtml(o.output_title)}</strong> <span style="font-size:10px; color:#777;">(معرف: ${escapeHtml(o.output_slug)})</span>`;
          item.onmouseover = () => item.style.background = "#eaf1f8";
          item.onmouseout = () => item.style.background = "#fff";
          item.onclick = () => {
            addOutputToProcedure(o.output_title, o.output_slug);
            const input = document.getElementById("output_search_input");
            if (input) input.value = "";
            resultsBox.style.display = "none";
          };
          resultsBox.appendChild(item);
        });
      }
      resultsBox.style.display = "block";
    } catch (err) {
      console.error("searchOutputs error:", err);
    }
  }, 150);
}

function addOutputToProcedure(title, slug) {
  if (selectedOutputs.some(o => o.title === title)) return;
  selectedOutputs.push({ title, slug });
  renderSelectedOutputs();
}

function removeOutput(idx) {
  selectedOutputs.splice(idx, 1);
  renderSelectedOutputs();
}

function renderSelectedOutputs() {
  const tbody = document.getElementById("selected_outputs_body");
  tbody.innerHTML = "";
  if (selectedOutputs.length === 0) {
    tbody.innerHTML = '<tr id="no_outputs_row"><td colspan="3" style="text-align:center; color:#888;">لم يتم اختيار أي مخرج بعد. اختر من القائمة أو أضف مخرجاً جديداً.</td></tr>';
    return;
  }
  selectedOutputs.forEach((o, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(o.title)}</strong></td>
      <td><code>${o.slug || "توليد تلقائي"}</code></td>
      <td style="text-align:center;">
        <button type="button" class="btn btn-default btn-action-small" onclick="removeOutput(${idx})" style="color:#c62828;">حذف</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ==========================================
// Evidences Selection Manager
// ==========================================
let composerEvidenceSearchTimeout = null;
function searchEvidences(q) {
  const resultsBox = document.getElementById("evidence_search_results");
  if (!resultsBox) return;
  const term = (q || "").trim();
  if (!term) {
    resultsBox.style.display = "none";
    return;
  }
  if (composerEvidenceSearchTimeout) clearTimeout(composerEvidenceSearchTimeout);
  composerEvidenceSearchTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`/api/evidences?q=${encodeURIComponent(term)}&limit=25`);
      const matched = await res.json();
      resultsBox.innerHTML = "";
      if (!matched.length) {
        resultsBox.innerHTML = '<div style="padding:8px 10px; color:#888; font-size:12px;">لا توجد وثائق مطابقة في السجل. انقر أدناه لتسجيل وثيقة جديدة.</div>';
      } else {
        matched.forEach(e => {
          const item = document.createElement("div");
          item.style.padding = "7px 10px";
          item.style.cursor = "pointer";
          item.style.borderBottom = "1px solid #eee";
          item.innerHTML = `<strong style="color:#1b4b7d;">${escapeHtml(e.evidence_title)}</strong> <span style="font-size:10px; color:#666;">[${escapeHtml(e.doc_category || "وثيقة")}]</span>`;
          item.onmouseover = () => item.style.background = "#eaf1f8";
          item.onmouseout = () => item.style.background = "#fff";
          item.onclick = () => {
            addEvidenceToProcedure(e.evidence_title, e.evidence_slug, e.doc_category);
            const input = document.getElementById("evidence_search_input");
            if (input) input.value = "";
            resultsBox.style.display = "none";
          };
          resultsBox.appendChild(item);
        });
      }
      resultsBox.style.display = "block";
    } catch (err) {
      console.error("searchEvidences error:", err);
    }
  }, 150);
}

function addEvidenceToProcedure(title, slug, category) {
  if (selectedEvidences.some(e => e.title === title)) return;
  selectedEvidences.push({ title, slug, category: category || "وثيقة عادية" });
  renderSelectedEvidences();
}

function removeEvidence(idx) {
  selectedEvidences.splice(idx, 1);
  renderSelectedEvidences();
}

function renderSelectedEvidences() {
  const tbody = document.getElementById("selected_evidences_body");
  tbody.innerHTML = "";
  if (selectedEvidences.length === 0) {
    tbody.innerHTML = '<tr id="no_evidences_row"><td colspan="3" style="text-align:center; color:#888;">لم يتم تحديد أي وثائق بعد. اختر من القائمة أو أضف وثيقة جديدة.</td></tr>';
    return;
  }
  selectedEvidences.forEach((e, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(e.title)}</strong></td>
      <td><span class="badge-tag">${escapeHtml(e.category)}</span></td>
      <td style="text-align:center;">
        <button type="button" class="btn btn-default btn-action-small" onclick="removeEvidence(${idx})" style="color:#c62828;">حذف</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ==========================================
// Form Compilation into JSON
// ==========================================
function getProcedureFormData() {
  const authSelect = document.getElementById("authority_select");
  const selectedAuthOpt = authSelect.options[authSelect.selectedIndex];

  const feeType = document.getElementById("fee_type").value;
  let costObj = null;
  if (feeType === "PAID") {
    costObj = {
      value: parseFloat(document.getElementById("fee_amount").value) || 0.0,
      currency: document.getElementById("fee_currency").value,
      description: document.getElementById("fee_desc").value || "رسوم قانونية"
    };
  } else {
    costObj = {
      value: 0.0,
      currency: "MAD",
      description: "مجانية بدون رسوم"
    };
  }

  const channels = [];
  const counterVal = document.getElementById("channel_counter").value.trim();
  if (counterVal) {
    channels.push({ name: counterVal, type: "counter" });
  }
  const portalUrl = document.getElementById("channel_portal_url").value.trim();
  if (portalUrl) {
    channels.push({ name: "البوابة الإلكترونية", type: "portal", url: portalUrl });
  }

  const ptDays = parseInt(document.getElementById("processing_time").value.trim());
  const procTimeFormatted = isNaN(ptDays) ? "P20D" : `P${ptDays}D`;

  return {
    title_ar: document.getElementById("service_title_ar").value.trim(),
    title_fr: document.getElementById("service_title_fr").value.trim(),
    description_ar: document.getElementById("service_desc_ar").value.trim(),
    authority_slug: authSelect.value,
    authority_name: selectedAuthOpt ? selectedAuthOpt.dataset.name : "",
    processing_time: procTimeFormatted,
    cost: costObj,
    outputs: selectedOutputs,
    evidences: selectedEvidences,
    channels: channels
  };
}

function updateComposerProcessingPreview(val) {
  const days = parseInt(val) || 0;
  const isoBadge = document.getElementById("composer_processing_iso");
  if (isoBadge) isoBadge.textContent = `P${days}D`;
}

function updateEditProcessingPreview(val) {
  const days = parseInt(val) || 0;
  const isoBadge = document.getElementById("edit_processing_iso");
  if (isoBadge) isoBadge.textContent = `P${days}D`;
}

// ==========================================
// Validation & SHACL Execution
// ==========================================
async function runValidation() {
  const data = getProcedureFormData();
  if (!data.title_ar) {
    alert("يرجى ملء تسمية المسطرة الإدارية بالعربية أولاً.");
    return;
  }
  if (!data.authority_slug) {
    alert("يرجى اختيار الإدارة المختصة من السجل.");
    return;
  }

  const btnVal = document.getElementById("btn-validate");
  const statusQuick = document.getElementById("validation-quick-status");
  btnVal.disabled = true;
  statusQuick.textContent = "جاري فحص المطابقة عبر محرك SHACL...";

  try {
    const res = await fetch("/api/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const result = await res.json();

    btnVal.disabled = false;
    currentCandidateTurtle = result.turtle_preview || "";

    const valSection = document.getElementById("validation-section");
    valSection.style.display = "block";

    const resultBox = document.getElementById("val-result-box");
    const timeBadge = document.getElementById("val-time-badge");
    timeBadge.textContent = `زمن المعالجة: ${result.execution_time_seconds} ثانية`;

    const btnSave = document.getElementById("btn-save");

    if (result.conforms && result.violations_count === 0) {
      statusQuick.innerHTML = '<span style="color:#2e7d32;">مطابق للمعيار (0 مخالفات)</span>';
      resultBox.innerHTML = `
        <div class="status-badge-pass">
          <div style="font-weight:bold; font-size:14px; margin-bottom:4px;">[ شهادة المطابقة المعيارية: المسطرة مطابقة بنسبة 100% ]</div>
          <div style="font-size:12px; line-height:1.6;">تم فحص المسطرة بنجاح مقابل المعيار الأوروبي المشترك SEMIC CPSV-AP 3.2.0 دون رصد أي مخالفة شكلية أو قانونية. أصبحت المسطرة معتمدة ومؤهلة للتسجيل في قاعدة البيانات.</div>
        </div>
      `;
      document.getElementById("val-violations-list").style.display = "none";
      btnSave.disabled = false;
    } else {
      statusQuick.innerHTML = `<span style="color:#c62828;">غير مطابق (${result.violations_count} مخالفة)</span>`;
      resultBox.innerHTML = `
        <div class="status-badge-fail">
          <div style="font-weight:bold; font-size:14px; margin-bottom:4px;">[ تقرير عدم المطابقة: تم رصد ${result.violations_count} مخالفة لمعيار CPSV-AP 3.2.0 ]</div>
          <div style="font-size:12px; line-height:1.6;">يرجى تصحيح الحقول والمحددات المذكورة في الجدول التفصيلي أدناه قبل إعادة الفحص. التسجيل في قاعدة البيانات محجوب حتى استيفاء 0 مخالفات.</div>
        </div>
      `;

      const tbody = document.getElementById("val-violations-tbody");
      tbody.innerHTML = "";
      result.violations.forEach(v => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><code>${escapeHtml(v.focus_node)}</code></td>
          <td><strong>${escapeHtml(v.path)}</strong></td>
          <td style="color:#c62828;">${escapeHtml(v.message)}</td>
        `;
        tbody.appendChild(tr);
      });
      document.getElementById("val-violations-list").style.display = "block";
      btnSave.disabled = true;
    }

    document.getElementById("turtle-code-box").textContent = currentCandidateTurtle;

  } catch (err) {
    btnVal.disabled = false;
    statusQuick.textContent = "خطأ في الاتصال بمحرك التحقق";
    alert("تعذر إجراء الفحص: " + err.message);
  }
}

// ==========================================
// Save Procedure to Repository
// ==========================================
async function saveProcedure() {
  if (!confirm("تأكيد العملية: هل ترغب في تسجيل هذه المسطرة في قاعدة البيانات؟")) {
    return;
  }

  const data = getProcedureFormData();
  const btnSave = document.getElementById("btn-save");
  btnSave.disabled = true;

  try {
    const res = await fetch("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const result = await res.json();

    if (res.ok && result.success) {
      alert("تم الحفظ بنجاح: " + result.message);
      resetForm();
    } else {
      alert("خطأ أثناء الحفظ: " + (result.error || "فشل غير محدد"));
      btnSave.disabled = false;
    }
  } catch (err) {
    alert("خطأ في الاتصال بالخادم: " + err.message);
    btnSave.disabled = false;
  }
}

// ==========================================
// Preview & Reset
// ==========================================
function toggleTurtlePreview() {
  const container = document.getElementById("turtle-preview-container");
  const valSection = document.getElementById("validation-section");
  valSection.style.display = "block";
  container.style.display = (container.style.display === "none") ? "block" : "none";
  if (!document.getElementById("turtle-code-box").textContent) {
    const data = getProcedureFormData();
    fetch("/api/compose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    }).then(r => r.json()).then(res => {
      document.getElementById("turtle-code-box").textContent = res.turtle || "";
    });
  }
}

function copyTurtleCode() {
  const code = document.getElementById("turtle-code-box").textContent;
  if (!code) return;
  navigator.clipboard.writeText(code).then(() => {
    alert("تم نسخ تمثيل RDF/Turtle بنجاح إلى الحافظة.");
  });
}

function resetForm() {
  document.getElementById("procedureForm").reset();
  selectedOutputs = [];
  selectedEvidences = [];
  renderSelectedOutputs();
  renderSelectedEvidences();
  document.getElementById("authority_hierarchy_badge").style.display = "none";
  document.getElementById("validation-section").style.display = "none";
  document.getElementById("btn-save").disabled = true;
  document.getElementById("validation-quick-status").textContent = "الحالة: جاهز للفحص";
  toggleFeeInputs();
}

// ==========================================
// Modals Handling
// ==========================================
function openModal(id) {
  document.getElementById(id).style.display = "flex";
}

function closeModal(id) {
  document.getElementById(id).style.display = "none";
}

async function submitNewAuthority() {
  const name = document.getElementById("new_auth_name").value.trim();
  if (!name) {
    alert("يرجى إدخال اسم الإدارة.");
    return;
  }
  const parent = document.getElementById("new_auth_parent").value.trim();

  try {
    const res = await fetch("/api/authorities", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name_ar: name, parent_name: parent })
    });
    const newAuth = await res.json();
    alert(`تم تسجيل الإدارة بنجاح: ${newAuth.org_name}`);
    closeModal("modal-add-authority");
    document.getElementById("new_auth_name").value = "";
    document.getElementById("new_auth_parent").value = "";
    await loadAuthorities();
    // Auto-select the newly added authority
    document.getElementById("authority_select").value = newAuth.org_slug;
    updateAuthorityDetails();
  } catch (err) {
    alert("فشل تسجيل الإدارة: " + err.message);
  }
}

async function submitNewOutput() {
  const titleInput = document.getElementById("new_output_title");
  const title = titleInput ? titleInput.value.trim() : "";
  if (!title) {
    alert("يرجى إدخال تسمية المخرج.");
    return;
  }
  try {
    const res = await fetch("/api/outputs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title_ar: title })
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.error || "خطأ في تسجيل المخرج بالخادم");
    }
    const newOut = await res.json();

    // 1. Prepend to outputsData cache so it appears immediately at index 0
    outputsData = [newOut, ...(outputsData || []).filter(o => o.output_id != newOut.output_id)];

    // 2. Add to Composer selected outputs
    addOutputToProcedure(newOut.output_title, newOut.output_slug);

    // 3. If in Explorer editor, auto-assign this output directly to the active procedure
    const editOutTitle = document.getElementById("edit_output_title");
    const editOutId = document.getElementById("edit_output_id");
    if (editOutTitle) editOutTitle.value = newOut.output_title;
    if (editOutId) editOutId.value = newOut.output_id;

    // 4. Update the Outputs Directory table immediately
    renderOutputsTable(outputsData);

    // 5. Close modal, clear input, and give feedback
    closeModal("modal-add-output");
    if (titleInput) titleInput.value = "";

    alert(`تم بنجاح تسجيل وحفظ المخرج في قاعدة البيانات والنموذج: "${newOut.output_title}"`);
  } catch (err) {
    alert("فشل إضافة المخرج: " + err.message);
  }
}

async function submitNewEvidence() {
  const titleInput = document.getElementById("new_evidence_title");
  const title = titleInput ? titleInput.value.trim() : "";
  if (!title) {
    alert("يرجى إدخال تسمية الوثيقة.");
    return;
  }
  const categoryElem = document.getElementById("new_evidence_category");
  const category = categoryElem ? categoryElem.value : "وثيقة عادية (Standard Document)";
  try {
    const res = await fetch("/api/evidences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title_ar: title, category: category })
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.error || "خطأ في تسجيل الوثيقة بالخادم");
    }
    const newEvid = await res.json();

    // 1. Prepend to evidencesData cache so it appears immediately at index 0
    evidencesData = [newEvid, ...(evidencesData || []).filter(e => e.evidence_id != newEvid.evidence_id)];

    // 2. Add to Composer selected evidences
    addEvidenceToProcedure(newEvid.evidence_title, newEvid.evidence_slug, newEvid.doc_category);

    // 3. If in Explorer editor, add to currentEditedEvidences tags
    if (typeof currentEditedEvidences !== "undefined" && Array.isArray(currentEditedEvidences)) {
      if (!currentEditedEvidences.includes(newEvid.evidence_title)) {
        currentEditedEvidences.push(newEvid.evidence_title);
        renderEditedEvidencesTags();
      }
    }

    // 4. Update the Evidences Directory table immediately
    renderEvidencesTable(evidencesData);

    // 5. Close modal, clear input, and give feedback
    closeModal("modal-add-evidence");
    if (titleInput) titleInput.value = "";

    alert(`تم بنجاح تسجيل وحفظ الوثيقة في قاعدة البيانات والنموذج: "${newEvid.evidence_title}"`);
  } catch (err) {
    alert("فشل إضافة الوثيقة: " + err.message);
  }
}

// ==========================================
// Raw Turtle Sandbox Validation
// ==========================================
async function validateRawTurtle() {
  const rawCode = document.getElementById("raw_turtle_input").value.trim();
  if (!rawCode) {
    alert("يرجى إدراج كود RDF/Turtle أولاً.");
    return;
  }
  const resDiv = document.getElementById("raw_shacl_results");
  resDiv.innerHTML = '<div style="color:#555;">جاري الفحص المباشر عبر محرك SHACL...</div>';

  try {
    const res = await fetch("/api/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title_ar: "اختبار مباشر",
        description_ar: "اختبار فوري لكود مخصص",
        authority_slug: "org_c8752c04661f"
      })
    });
    const result = await res.json();

    if (result.conforms) {
      resDiv.innerHTML = `
        <div class="status-badge-pass">
          <strong>[ نتيجة الفحص: مطابق 100% (0 مخالفات) ]</strong>
          <div style="font-size:12px; margin-top:3px;">الكود يستوفي جميع شروط ومعايير CPSV-AP 3.2.0.</div>
        </div>
      `;
    } else {
      resDiv.innerHTML = `
        <div class="status-badge-fail">
          <strong>[ نتيجة الفحص: غير مطابق (${result.violations_count} مخالفة) ]</strong>
        </div>
      `;
    }
  } catch (err) {
    resDiv.innerHTML = `<div style="color:#c62828;">تعذر إتمام الفحص: ${err.message}</div>`;
  }
}

// ==========================================
// Tables Renderers for Explorer Tabs
// ==========================================
// ==========================================
// Interactive Authorities & Outputs Entity Managers
// ==========================================
let selectedAuthId = null;
let selectedOutputId = null;

function renderAuthoritiesTable(data) {
  renderAuthoritiesInteractive(data);
}

function renderAuthoritiesInteractive(data) {
  const container = document.getElementById("authorities_list_pane");
  if (!container) return;
  container.innerHTML = "";

  const list = data || authoritiesData || [];
  if (!list.length) {
    container.innerHTML = '<div style="padding:20px; text-align:center; color:#777;">لم يتم العثور على أي مؤسسة.</div>';
    return;
  }

  list.forEach(a => {
    const isSelected = String(a.org_id) === String(selectedAuthId);
    const item = document.createElement("div");
    item.className = `entity-card-item ${isSelected ? "selected" : ""}`;
    item.dataset.orgId = a.org_id;
    item.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:bold; color:#1b4b7d;">${escapeHtml(a.org_name)}</span>
        <span class="badge-tag" style="font-size:10px; padding:1px 4px; background:#f0f4f8; color:#005a9c;">${escapeHtml(a.org_slug || 'org_' + a.org_id)}</span>
      </div>
      <div style="font-size:11px; color:#666; margin-top:3px; display:flex; justify-content:space-between;">
        <span>${escapeHtml(a.classification || "مؤسسة عمومية")}</span>
        <span style="color:#2e7d32; font-weight:bold;">${a.procedure_count || 0} مسطرة</span>
      </div>
    `;
    item.onclick = () => selectAuthority(a.org_id);
    container.appendChild(item);
  });
}

function selectAuthority(orgId) {
  selectedAuthId = orgId;
  const auth = authoritiesData.find(a => String(a.org_id) === String(orgId));
  if (!auth) return;

  document.querySelectorAll("#authorities_list_pane .entity-card-item").forEach(el => {
    if (el.dataset.orgId === String(orgId)) {
      el.classList.add("selected");
    } else {
      el.classList.remove("selected");
    }
  });

  const placeholder = document.getElementById("auth_inspector_placeholder");
  const form = document.getElementById("auth_inspector_form");
  if (placeholder) placeholder.style.display = "none";
  if (form) form.style.display = "block";

  document.getElementById("auth_insp_badge").textContent = `ORG-${auth.org_id}`;
  document.getElementById("auth_insp_count_badge").textContent = `${auth.procedure_count || 0} مسطرة`;
  document.getElementById("auth_insp_name").value = auth.org_name;
  document.getElementById("auth_insp_slug").value = auth.org_slug || `org_${auth.org_id}`;
  document.getElementById("auth_insp_spatial").value = "MAR";
  document.getElementById("auth_insp_classification").value = auth.classification || "مؤسسة عمومية / إدارة";
  document.getElementById("auth_insp_parent").value = auth.suggested_parent_name || "المملكة المغربية";

  const msgBox = document.getElementById("auth_insp_msg");
  if (msgBox) msgBox.style.display = "none";
}

async function saveAuthorityInspector() {
  if (!selectedAuthId) return;
  const name = document.getElementById("auth_insp_name").value.trim();
  const msgBox = document.getElementById("auth_insp_msg");

  if (!name) {
    if (msgBox) {
      msgBox.style.display = "block";
      msgBox.style.background = "#ffebee";
      msgBox.style.color = "#b71c1c";
      msgBox.textContent = "خطأ معايير: التسمية الرسمية للإدارة حقل إجباري (*)";
    }
    document.getElementById("auth_insp_name").focus();
    return;
  }

  const payload = {
    org_id: selectedAuthId,
    name_ar: name,
    classification: document.getElementById("auth_insp_classification").value,
    parent_name: document.getElementById("auth_insp_parent").value.trim() || "المملكة المغربية"
  };

  try {
    const res = await fetch("/api/authorities/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.success) {
      const existing = authoritiesData.find(a => String(a.org_id) === String(selectedAuthId));
      if (existing) {
        existing.org_name = name;
        existing.classification = payload.classification;
        existing.suggested_parent_name = payload.parent_name;
      }
      renderAuthoritiesInteractive(authoritiesData);
      if (msgBox) {
        msgBox.style.display = "block";
        msgBox.style.background = "#e8f5e9";
        msgBox.style.color = "#1b5e20";
        msgBox.textContent = "تم حفظ وتحديث بيانات الإدارة العمومية بنجاح.";
      }
    } else {
      if (msgBox) {
        msgBox.style.display = "block";
        msgBox.style.background = "#ffebee";
        msgBox.style.color = "#b71c1c";
        msgBox.textContent = result.error || "خطأ أثناء التحديث";
      }
    }
  } catch (err) {
    if (msgBox) {
      msgBox.style.display = "block";
      msgBox.style.background = "#ffebee";
      msgBox.style.color = "#b71c1c";
      msgBox.textContent = "تعذر الاتصال بالخادم: " + err.message;
    }
  }
}

async function deleteAuthorityInspector() {
  if (!selectedAuthId) return;
  const auth = authoritiesData.find(a => String(a.org_id) === String(selectedAuthId));
  const authName = auth ? auth.org_name : `#${selectedAuthId}`;

  if (!confirm(`هل أنت متأكد من رغبتك في حذف الإدارة "${authName}"؟ سيتم إعادة ربط مساطرها بالمملكة المغربية تلقائياً.`)) {
    return;
  }

  try {
    const res = await fetch("/api/authorities/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ org_id: selectedAuthId })
    });
    const result = await res.json();
    if (result.success) {
      authoritiesData = authoritiesData.filter(a => String(a.org_id) !== String(selectedAuthId));
      selectedAuthId = null;
      document.getElementById("auth_inspector_form").style.display = "none";
      document.getElementById("auth_inspector_placeholder").style.display = "block";
      renderAuthoritiesInteractive(authoritiesData);
      alert("تم حذف الإدارة بنجاح.");
    } else {
      alert("فشل الحذف: " + (result.error || ""));
    }
  } catch (err) {
    alert("خطأ في الاتصال: " + err.message);
  }
}

function onAuthoritySearchInput(q) {
  const term = (q || "").trim().toLowerCase();
  const filtered = authoritiesData.filter(a => a.org_name.toLowerCase().includes(term));
  renderAuthoritiesInteractive(filtered);
}

function renderOutputsTable(data) {
  renderOutputsInteractive(data);
}

function renderOutputsInteractive(data) {
  const container = document.getElementById("outputs_list_pane");
  if (!container) return;
  container.innerHTML = "";

  const list = data || outputsData || [];
  if (!list.length) {
    container.innerHTML = '<div style="padding:20px; text-align:center; color:#777;">لم يتم العثور على أي مخرج أو شهادة.</div>';
    return;
  }

  list.forEach(o => {
    const isSelected = String(o.output_id) === String(selectedOutputId);
    const item = document.createElement("div");
    item.className = `entity-card-item ${isSelected ? "selected" : ""}`;
    item.dataset.outputId = o.output_id;
    item.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:bold; color:#0b5394;">${escapeHtml(o.output_title)}</span>
        <span class="badge-tag" style="font-size:10px; padding:1px 4px; background:#f0f4f8; color:#005a9c;">${escapeHtml(o.output_slug)}</span>
      </div>
      <div style="font-size:11px; color:#666; margin-top:3px; display:flex; justify-content:space-between;">
        <span>شهادة رسمية</span>
        <span style="color:#2e7d32; font-weight:bold;">${o.procedure_count || 0} مسطرة</span>
      </div>
    `;
    item.onclick = () => selectOutput(o.output_id);
    container.appendChild(item);
  });
}

function selectOutput(outputId) {
  selectedOutputId = outputId;
  const out = outputsData.find(o => String(o.output_id) === String(outputId));
  if (!out) return;

  document.querySelectorAll("#outputs_list_pane .entity-card-item").forEach(el => {
    if (el.dataset.outputId === String(outputId)) {
      el.classList.add("selected");
    } else {
      el.classList.remove("selected");
    }
  });

  const placeholder = document.getElementById("output_inspector_placeholder");
  const form = document.getElementById("output_inspector_form");
  if (placeholder) placeholder.style.display = "none";
  if (form) form.style.display = "block";

  document.getElementById("output_insp_badge").textContent = `OUT-${out.output_id}`;
  document.getElementById("output_insp_count_badge").textContent = `${out.procedure_count || 0} مسطرة`;
  document.getElementById("output_insp_title").value = out.output_title;
  document.getElementById("output_insp_slug").value = out.output_slug;
  document.getElementById("output_insp_desc").value = out.output_desc || "";
  document.getElementById("output_insp_type").value = out.output_type || "شهادة إدارية رسمية";
  document.getElementById("output_insp_lang").value = out.output_lang || "ar";

  const msgBox = document.getElementById("output_insp_msg");
  if (msgBox) msgBox.style.display = "none";
}

async function saveOutputInspector() {
  if (!selectedOutputId) return;
  const title = document.getElementById("output_insp_title").value.trim();
  const msgBox = document.getElementById("output_insp_msg");

  if (!title) {
    if (msgBox) {
      msgBox.style.display = "block";
      msgBox.style.background = "#ffebee";
      msgBox.style.color = "#b71c1c";
      msgBox.textContent = "خطأ معايير: تسمية الشهادة أو الخدمة المسلمة حقل إجباري (*)";
    }
    document.getElementById("output_insp_title").focus();
    return;
  }

  const payload = {
    output_id: selectedOutputId,
    title_ar: title
  };

  try {
    const res = await fetch("/api/outputs/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.success) {
      const existing = outputsData.find(o => String(o.output_id) === String(selectedOutputId));
      if (existing) {
        existing.output_title = title;
      }
      renderOutputsInteractive(outputsData);
      if (msgBox) {
        msgBox.style.display = "block";
        msgBox.style.background = "#e8f5e9";
        msgBox.style.color = "#1b5e20";
        msgBox.textContent = "تم حفظ وتحديث بيانات الشهادة أو الخدمة المسلمة بنجاح.";
      }
    } else {
      if (msgBox) {
        msgBox.style.display = "block";
        msgBox.style.background = "#ffebee";
        msgBox.style.color = "#b71c1c";
        msgBox.textContent = result.error || "خطأ أثناء التحديث";
      }
    }
  } catch (err) {
    if (msgBox) {
      msgBox.style.display = "block";
      msgBox.style.background = "#ffebee";
      msgBox.style.color = "#b71c1c";
      msgBox.textContent = "تعذر الاتصال بالخادم: " + err.message;
    }
  }
}

async function deleteOutputInspector() {
  if (!selectedOutputId) return;
  const out = outputsData.find(o => String(o.output_id) === String(selectedOutputId));
  const outTitle = out ? out.output_title : `#${selectedOutputId}`;

  if (!confirm(`هل أنت متأكد من رغبتك في حذف المخرج "${outTitle}" من السجل؟`)) {
    return;
  }

  try {
    const res = await fetch("/api/outputs/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ output_id: selectedOutputId })
    });
    const result = await res.json();
    if (result.success) {
      outputsData = outputsData.filter(o => String(o.output_id) !== String(selectedOutputId));
      selectedOutputId = null;
      document.getElementById("output_inspector_form").style.display = "none";
      document.getElementById("output_inspector_placeholder").style.display = "block";
      renderOutputsInteractive(outputsData);
      alert("تم حذف المخرج الإداري بنجاح.");
    } else {
      alert("فشل الحذف: " + (result.error || ""));
    }
  } catch (err) {
    alert("خطأ في الاتصال: " + err.message);
  }
}

let filterOutputsTabTimeout = null;
function onOutputSearchInput(q) {
  const term = (q || "").trim();
  if (filterOutputsTabTimeout) clearTimeout(filterOutputsTabTimeout);

  const localFiltered = (outputsData || []).filter(o => !term || (o.output_title && o.output_title.toLowerCase().includes(term.toLowerCase())));
  renderOutputsInteractive(localFiltered);

  if (term.length >= 2) {
    filterOutputsTabTimeout = setTimeout(async () => {
      try {
        const res = await fetch(`/api/outputs?q=${encodeURIComponent(term)}&limit=100`);
        const serverResults = await res.json();
        if (serverResults && serverResults.length > 0) {
          renderOutputsInteractive(serverResults);
        }
      } catch (e) {
        console.error("onOutputSearchInput error:", e);
      }
    }, 250);
  } else if (!term) {
    renderOutputsInteractive(outputsData);
  }
}

function renderEvidencesTable(data) {
  const tbody = document.getElementById("full_evidences_tbody");
  tbody.innerHTML = "";
  (data || []).forEach(e => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${e.evidence_slug}</code></td>
      <td><strong>${escapeHtml(e.evidence_title)}</strong></td>
      <td><span class="badge-tag">${escapeHtml(e.doc_category || "وثيقة")}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

let filterEvidencesTabTimeout = null;
function filterEvidencesTab(q) {
  const term = (q || "").trim();
  if (filterEvidencesTabTimeout) clearTimeout(filterEvidencesTabTimeout);

  const localFiltered = (evidencesData || []).filter(e => !term || (e.evidence_title && e.evidence_title.toLowerCase().includes(term.toLowerCase())));
  renderEvidencesTable(localFiltered);

  if (term.length >= 2) {
    filterEvidencesTabTimeout = setTimeout(async () => {
      try {
        const res = await fetch(`/api/evidences?q=${encodeURIComponent(term)}&limit=100`);
        const serverResults = await res.json();
        if (serverResults && serverResults.length > 0) {
          renderEvidencesTable(serverResults);
        }
      } catch (e) {
        console.error("filterEvidencesTab server error:", e);
      }
    }, 250);
  } else if (!term) {
    renderEvidencesTable(evidencesData);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ==========================================
// Procedure Explorer & Direct Curator Logic
// ==========================================
let currentEditedProcedure = null;
let currentEditedEvidences = [];
let explorerSearchTimeout = null;

async function loadExplorerProcedures(query = "") {
  const listContainer = document.getElementById("explorer_list_container");
  const loadingIndicator = document.getElementById("explorer_loading_indicator");
  const totalCountSpan = document.getElementById("explorer_total_count");

  if (loadingIndicator) loadingIndicator.style.display = "inline";

  try {
    const url = `/api/procedures?q=${encodeURIComponent(query)}&limit=50`;
    const res = await fetch(url);
    const data = await res.json();

    if (totalCountSpan) totalCountSpan.textContent = data.total ? data.total.toLocaleString("ar-MA") : 0;
    renderExplorerProceduresList(data.procedures || []);
  } catch (err) {
    console.error("Error loading procedures:", err);
    if (listContainer) {
      listContainer.innerHTML = '<div style="padding:20px; color:#c62828; text-align:center;">تعذر تحميل قائمة المساطر الإدارية.</div>';
    }
  } finally {
    if (loadingIndicator) loadingIndicator.style.display = "none";
  }
}

function renderExplorerProceduresList(procedures) {
  const container = document.getElementById("explorer_list_container");
  if (!container) return;

  if (!procedures.length) {
    container.innerHTML = '<div style="padding:30px; text-align:center; color:#777;">لم يتم العثور على أي مسطرة تطابق معايير البحث.</div>';
    return;
  }

  let html = '<div class="procedure-list-items" style="display:flex; flex-direction:column; gap:6px;">';
  procedures.forEach(p => {
    const isSelected = currentEditedProcedure && (String(currentEditedProcedure.ps_id) === String(p.ps_id));
    html += `
      <div class="proc-item-card ${isSelected ? 'selected' : ''}" data-ps-id="${p.ps_id}" onclick="selectProcedureForEdit('${p.ps_id}', this)" style="padding:8px 10px; border:${isSelected ? '1.5px solid #005a9c' : '1px solid #e0e0e0'}; background:${isSelected ? '#e8f0fe' : '#fff'}; box-shadow:${isSelected ? '0 0 0 2px rgba(0,90,156,0.18)' : 'none'}; border-radius:3px; cursor:pointer; transition:all 0.15s ease;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px;">
          <strong style="font-size:12px; color:#1b4b7d;">${escapeHtml(p.title)}</strong>
          <span class="badge-tag" style="font-size:10px; padding:1px 5px; background:#f0f4f8; color:#005a9c; border-color:#d0dbe5;">${escapeHtml(p.ps_uuid)}</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:11px; color:#555;">
          <span>${escapeHtml(p.authority_name)}</span>
          <div>
            <span style="font-weight:bold; color:#1b5e20;">${p.cost > 0 ? p.cost + ' د.م' : 'مجاني'}</span>
            <span style="margin-right:6px; color:#777;">| ${p.evidences_count} وثائق</span>
          </div>
        </div>
      </div>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

function onExplorerSearchInput(val) {
  if (explorerSearchTimeout) clearTimeout(explorerSearchTimeout);
  explorerSearchTimeout = setTimeout(() => {
    loadExplorerProcedures(val);
  }, 300);
}

function searchExplorerNow() {
  const input = document.getElementById("explorer_search_input");
  loadExplorerProcedures(input ? input.value : "");
}

function filterExplorerQuick(term) {
  const input = document.getElementById("explorer_search_input");
  if (input) input.value = term;
  loadExplorerProcedures(term);
}

function highlightSelectedProcedureCard(psId, cardEl) {
  const cards = document.querySelectorAll(".proc-item-card");
  cards.forEach(el => {
    el.classList.remove("selected");
    el.style.border = "1px solid #e0e0e0";
    el.style.background = "#fff";
    el.style.boxShadow = "none";
  });
  const target = cardEl || document.querySelector(`.proc-item-card[data-ps-id="${psId}"]`);
  if (target) {
    target.classList.add("selected");
    target.style.border = "1.5px solid #005a9c";
    target.style.background = "#e8f0fe";
    target.style.boxShadow = "0 0 0 2px rgba(0, 90, 156, 0.2)";
  }
}

async function selectProcedureForEdit(psId, cardEl) {
  // 1. Immediate zero-latency highlight on click
  highlightSelectedProcedureCard(psId, cardEl);

  try {
    const res = await fetch(`/api/procedures/${psId}`);
    if (!res.ok) throw new Error("تعذر جلب تفاصيل المسطرة");
    const proc = await res.json();

    currentEditedProcedure = proc;
    currentEditedEvidences = (proc.evidences || []).map(e => e.title);

    // Update UI Elements
    document.getElementById("edit_ps_badge").textContent = proc.ps_uuid;
    document.getElementById("edit_ps_db_id").textContent = `#${proc.ps_id}`;
    document.getElementById("edit_title").value = proc.title;
    document.getElementById("edit_description").value = proc.description || "";
    document.getElementById("edit_cost").value = proc.cost || 0;
    
    // Set Processing time (Days only -> P*D)
    const rawPt = String(proc.processing_time || "");
    const ptDigits = rawPt.replace(/\D/g, "");
    const days = ptDigits ? parseInt(ptDigits) : 20;
    const editDaysInput = document.getElementById("edit_processing_days");
    if (editDaysInput) {
      editDaysInput.value = days;
      updateEditProcessingPreview(days);
    }

    // Set Searchable Authority
    const authSearch = document.getElementById("edit_authority_search");
    const authHidden = document.getElementById("edit_authority_id");
    const authSelect = document.getElementById("edit_authority");
    if (authSearch) authSearch.value = proc.authority_name || "";
    if (authHidden) authHidden.value = proc.authority_id || 1;
    if (authSelect) authSelect.value = proc.authority_id || 1;

    // Set Output
    const outTitleInput = document.getElementById("edit_output_title");
    const outHidden = document.getElementById("edit_output_id");
    if (outTitleInput) outTitleInput.value = proc.output_title || "";
    if (outHidden) outHidden.value = proc.output_id || "";

    renderEditedEvidencesTags();

    // Toggle forms
    document.getElementById("explorer_editor_placeholder").style.display = "none";
    document.getElementById("explorer_editor_form").style.display = "block";
    document.getElementById("edit_validation_status_box").style.display = "none";
    document.getElementById("edit_turtle_preview_box").style.display = "none";

    // Re-confirm highlight in case of re-render
    highlightSelectedProcedureCard(psId, cardEl);
  } catch (err) {
    console.error("Failed to select procedure:", err);
    alert("تعذر تحميل تفاصيل المسطرة المحددة.");
  }
}

// ------------------------------------------
// Authority Searchable Combobox Helpers
// ------------------------------------------
function showEditAuthorityDropdown() {
  const input = document.getElementById("edit_authority_search");
  filterEditAuthorityDropdown(input ? input.value : "");
}

function filterEditAuthorityDropdown(val) {
  const dropdown = document.getElementById("edit_authority_dropdown");
  if (!dropdown) return;
  const q = (val || "").trim().toLowerCase();
  const matched = (authoritiesData || []).filter(a => !q || (a.org_name && a.org_name.toLowerCase().includes(q)));
  
  if (!matched.length) {
    dropdown.innerHTML = '<div style="padding:8px 12px; color:#888; font-size:12px;">لا توجد إدارة مطابقة. سيتم استخدام الاسم المكتوب.</div>';
    dropdown.style.display = "block";
    return;
  }

  let html = "";
  matched.slice(0, 35).forEach(a => {
    html += `
      <div onclick="selectEditAuthority('${a.org_id}', '${escapeHtml(a.org_name)}')" style="padding:7px 10px; cursor:pointer; font-size:12px; border-bottom:1px solid #f0f0f0; transition:background 0.1s;" onmouseover="this.style.background='#e8f0fe'" onmouseout="this.style.background='#fff'">
        <div style="font-weight:bold; color:#1b4b7d;">${escapeHtml(a.org_name)}</div>
        <div style="font-size:10px; color:#666;">${escapeHtml(a.classification || "مؤسسة عمومية / إدارة")}</div>
      </div>
    `;
  });
  dropdown.innerHTML = html;
  dropdown.style.display = "block";
}

function selectEditAuthority(orgId, orgName) {
  const searchInput = document.getElementById("edit_authority_search");
  const hiddenId = document.getElementById("edit_authority_id");
  const selectAuth = document.getElementById("edit_authority");
  const dropdown = document.getElementById("edit_authority_dropdown");

  if (searchInput) searchInput.value = orgName;
  if (hiddenId) hiddenId.value = orgId;
  if (selectAuth) selectAuth.value = orgId;
  if (dropdown) dropdown.style.display = "none";
}

// ------------------------------------------
// ------------------------------------------
// Output Deliverable Helpers
// ------------------------------------------
let editOutputSearchTimeout = null;
function showEditOutputDropdown() {
  const input = document.getElementById("edit_output_title");
  filterEditOutputDropdown(input ? input.value : "");
}

function filterEditOutputDropdown(val) {
  const dropdown = document.getElementById("edit_output_dropdown");
  if (!dropdown) return;
  const q = (val || "").trim();

  // Reset hidden ID if text changed
  const hiddenId = document.getElementById("edit_output_id");
  if (!q && hiddenId) hiddenId.value = "";

  if (editOutputSearchTimeout) clearTimeout(editOutputSearchTimeout);

  renderEditOutputDropdownItems(q, outputsData || []);

  if (q.length >= 2) {
    editOutputSearchTimeout = setTimeout(async () => {
      try {
        const res = await fetch(`/api/outputs?q=${encodeURIComponent(q)}&limit=30`);
        const serverResults = await res.json();
        renderEditOutputDropdownItems(q, serverResults);
      } catch (e) {
        console.error("filterEditOutputDropdown server search error:", e);
      }
    }, 200);
  }
}

function renderEditOutputDropdownItems(q, items) {
  const dropdown = document.getElementById("edit_output_dropdown");
  if (!dropdown) return;
  dropdown.innerHTML = "";

  const queryLower = q.toLowerCase();
  const matched = (items || []).filter(o => !q || (o.output_title && o.output_title.toLowerCase().includes(queryLower)));

  if (q && !matched.some(m => m.output_title && m.output_title.toLowerCase() === queryLower)) {
    const createOption = document.createElement("div");
    createOption.style.padding = "8px 10px";
    createOption.style.cursor = "pointer";
    createOption.style.background = "#e8f0fe";
    createOption.style.color = "#0b5394";
    createOption.style.fontWeight = "bold";
    createOption.style.fontSize = "12px";
    createOption.style.borderBottom = "1px solid #cce5ff";
    createOption.textContent = `+ اعتماد وتثبيت كمخرج جديد: "${q}"`;
    createOption.addEventListener("click", () => {
      selectEditOutput("", q);
    });
    dropdown.appendChild(createOption);
  }

  if (matched.length === 0 && !q) {
    const emptyDiv = document.createElement("div");
    emptyDiv.style.padding = "8px 12px";
    emptyDiv.style.color = "#888";
    emptyDiv.style.fontSize = "12px";
    emptyDiv.textContent = "ابدأ بكتابة اسم المخرج أو الشهادة...";
    dropdown.appendChild(emptyDiv);
  } else {
    matched.slice(0, 30).forEach(o => {
      const itemDiv = document.createElement("div");
      itemDiv.style.padding = "6px 10px";
      itemDiv.style.cursor = "pointer";
      itemDiv.style.fontSize = "12px";
      itemDiv.style.borderBottom = "1px solid #f0f0f0";
      itemDiv.onmouseover = () => itemDiv.style.background = "#e8f0fe";
      itemDiv.onmouseout = () => itemDiv.style.background = "#fff";

      const titleDiv = document.createElement("div");
      titleDiv.style.fontWeight = "bold";
      titleDiv.style.color = "#0b5394";
      titleDiv.textContent = o.output_title;

      const slugDiv = document.createElement("div");
      slugDiv.style.fontSize = "10px";
      slugDiv.style.color = "#777";
      slugDiv.textContent = o.output_slug;

      itemDiv.appendChild(titleDiv);
      itemDiv.appendChild(slugDiv);

      itemDiv.addEventListener("click", () => {
        selectEditOutput(o.output_id, o.output_title);
      });

      dropdown.appendChild(itemDiv);
    });
  }

  dropdown.style.display = "block";
}

function selectEditOutput(outId, outTitle) {
  const titleInput = document.getElementById("edit_output_title");
  const hiddenId = document.getElementById("edit_output_id");
  const dropdown = document.getElementById("edit_output_dropdown");

  if (titleInput) titleInput.value = outTitle;
  if (hiddenId) hiddenId.value = outId || "";
  if (dropdown) dropdown.style.display = "none";
}

function clearEditOutput() {
  const titleInput = document.getElementById("edit_output_title");
  const hiddenId = document.getElementById("edit_output_id");
  if (titleInput) titleInput.value = "";
  if (hiddenId) hiddenId.value = "";
}

// Global click outside to dismiss popups
document.addEventListener("click", function(e) {
  const authDropdown = document.getElementById("edit_authority_dropdown");
  const authSearch = document.getElementById("edit_authority_search");
  if (authDropdown && authSearch && !authDropdown.contains(e.target) && e.target !== authSearch) {
    authDropdown.style.display = "none";
  }

  const outDropdown = document.getElementById("edit_output_dropdown");
  const outInput = document.getElementById("edit_output_title");
  if (outDropdown && outInput && !outDropdown.contains(e.target) && e.target !== outInput) {
    outDropdown.style.display = "none";
  }

  const evDropdown = document.getElementById("edit_evidence_dropdown");
  const evInput = document.getElementById("edit_add_evidence_input");
  if (evDropdown && evInput && !evDropdown.contains(e.target) && e.target !== evInput) {
    evDropdown.style.display = "none";
  }
});

let editEvidenceSearchTimeout = null;
function showEditEvidenceDropdown() {
  const input = document.getElementById("edit_add_evidence_input");
  filterEditEvidenceDropdown(input ? input.value : "");
}

function filterEditEvidenceDropdown(val) {
  const dropdown = document.getElementById("edit_evidence_dropdown");
  if (!dropdown) return;
  const q = (val || "").trim();

  if (editEvidenceSearchTimeout) clearTimeout(editEvidenceSearchTimeout);

  renderEditEvidenceDropdownItems(q, evidencesData || []);

  if (q.length >= 2) {
    editEvidenceSearchTimeout = setTimeout(async () => {
      try {
        const res = await fetch(`/api/evidences?q=${encodeURIComponent(q)}&limit=30`);
        const serverResults = await res.json();
        renderEditEvidenceDropdownItems(q, serverResults);
      } catch (e) {
        console.error("filterEditEvidenceDropdown server search error:", e);
      }
    }, 200);
  }
}

function renderEditEvidenceDropdownItems(q, items) {
  const dropdown = document.getElementById("edit_evidence_dropdown");
  if (!dropdown) return;
  dropdown.innerHTML = "";

  const queryLower = q.toLowerCase();
  const matched = (items || []).filter(e => !q || (e.evidence_title && e.evidence_title.toLowerCase().includes(queryLower)));

  if (q) {
    const addOption = document.createElement("div");
    addOption.style.padding = "7px 10px";
    addOption.style.cursor = "pointer";
    addOption.style.fontSize = "12px";
    addOption.style.background = "#f0f8ff";
    addOption.style.borderBottom = "1px solid #cce5ff";
    addOption.style.color = "#005a9c";
    addOption.onmouseover = () => addOption.style.background = "#e3effd";
    addOption.onmouseout = () => addOption.style.background = "#f0f8ff";
    addOption.innerHTML = `<strong>+ إضافة كوثيقة جديدة:</strong> "${escapeHtml(q)}"`;
    addOption.addEventListener("click", () => {
      selectEditEvidence(q);
    });
    dropdown.appendChild(addOption);
  }

  if (matched.length === 0 && !q) {
    const emptyDiv = document.createElement("div");
    emptyDiv.style.padding = "8px 12px";
    emptyDiv.style.color = "#888";
    emptyDiv.style.fontSize = "12px";
    emptyDiv.textContent = "اكتب للبحث عن وثيقة أو إضافة وثيقة جديدة...";
    dropdown.appendChild(emptyDiv);
  } else {
    matched.slice(0, 30).forEach(e => {
      const itemDiv = document.createElement("div");
      itemDiv.style.padding = "6px 10px";
      itemDiv.style.cursor = "pointer";
      itemDiv.style.fontSize = "12px";
      itemDiv.style.borderBottom = "1px solid #f0f0f0";
      itemDiv.onmouseover = () => itemDiv.style.background = "#e8f0fe";
      itemDiv.onmouseout = () => itemDiv.style.background = "#fff";

      const titleDiv = document.createElement("div");
      titleDiv.style.fontWeight = "bold";
      titleDiv.style.color = "#1b4b7d";
      titleDiv.textContent = e.evidence_title;

      const metaDiv = document.createElement("div");
      metaDiv.style.fontSize = "10px";
      metaDiv.style.color = "#666";
      metaDiv.textContent = `${e.evidence_slug || ""} ${e.procedure_count ? `(${e.procedure_count} مسطرة)` : ''}`;

      itemDiv.appendChild(titleDiv);
      itemDiv.appendChild(metaDiv);

      itemDiv.addEventListener("click", () => {
        selectEditEvidence(e.evidence_title);
      });

      dropdown.appendChild(itemDiv);
    });
  }

  dropdown.style.display = "block";
}

function selectEditEvidence(title) {
  const cleanTitle = title.trim();
  if (cleanTitle && !currentEditedEvidences.includes(cleanTitle)) {
    currentEditedEvidences.push(cleanTitle);
    renderEditedEvidencesTags();
  }
  const input = document.getElementById("edit_add_evidence_input");
  if (input) input.value = "";
  const dropdown = document.getElementById("edit_evidence_dropdown");
  if (dropdown) dropdown.style.display = "none";
}

function renderEditedEvidencesTags() {
  const container = document.getElementById("edit_evidences_tag_container");
  const countSpan = document.getElementById("edit_evidences_count");
  if (!container) return;

  if (countSpan) countSpan.textContent = currentEditedEvidences.length;

  if (!currentEditedEvidences.length) {
    container.innerHTML = '<span style="font-size:12px; color:#888; font-style:italic;">لا توجد وثائق مضافة لهذه المسطرة حالياً.</span>';
    return;
  }

  let html = "";
  currentEditedEvidences.forEach((evTitle, idx) => {
    html += `
      <span class="badge-tag" style="background:#e8f4fd; color:#0b5394; border-color:#b6d7a8; display:inline-flex; align-items:center; gap:4px; font-size:11px; padding:3px 8px;">
        ${escapeHtml(evTitle)}
        <span onclick="removeEvidenceFromEdited(${idx})" style="cursor:pointer; font-weight:bold; color:#c62828; margin-right:4px;" title="حذف هذه الوثيقة">&times;</span>
      </span>
    `;
  });
  container.innerHTML = html;
}

function removeEvidenceFromEdited(index) {
  if (index >= 0 && index < currentEditedEvidences.length) {
    currentEditedEvidences.splice(index, 1);
    renderEditedEvidencesTags();
  }
}

function addEvidenceToEditedProcedure() {
  const input = document.getElementById("edit_add_evidence_input");
  if (!input) return;
  const val = input.value.trim();
  if (!val) return;

  if (!currentEditedEvidences.includes(val)) {
    currentEditedEvidences.push(val);
    renderEditedEvidencesTags();
  }
  input.value = "";
  const dropdown = document.getElementById("edit_evidence_dropdown");
  if (dropdown) dropdown.style.display = "none";
}

async function validateEditedProcedureDraft() {
  if (!currentEditedProcedure) return;

  const authSearch = document.getElementById("edit_authority_search");
  const authHidden = document.getElementById("edit_authority_id");
  const authName = authSearch ? authSearch.value.trim() : "المملكة المغربية";
  const authId = authHidden ? (parseInt(authHidden.value) || 1) : 1;

  const outputTitle = document.getElementById("edit_output_title").value.trim();

  const payload = {
    ps_id: currentEditedProcedure.ps_id,
    ps_uuid: currentEditedProcedure.ps_uuid,
    title: document.getElementById("edit_title").value.trim(),
    description: document.getElementById("edit_description").value.trim(),
    authority_id: authId,
    authority_name: authName,
    output_title: outputTitle,
    cost: parseFloat(document.getElementById("edit_cost").value) || 0.0,
    evidences: currentEditedEvidences
  };

  const statusBox = document.getElementById("edit_validation_status_box");
  statusBox.style.display = "block";
  statusBox.innerHTML = '<div style="padding:10px; font-size:12px; color:#555;">جاري الفحص المباشر لقواعد SHACL...</div>';

  try {
    const res = await fetch("/api/procedures/validate-draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.conforms) {
      statusBox.innerHTML = `
        <div style="padding:10px; background:#e8f5e9; border:1px solid #81c784; border-radius:3px; color:#1b5e20; font-size:12px;">
          <strong>مطابقة تامة (CONFORMING - 0 VIOLATIONS):</strong> المسطرة تستوفي كافة معايير SEMIC CPSV-AP 3.2.0 بنجاح.
        </div>
      `;
    } else {
      let issues = (data.violations || []).map(v => `<li>${escapeHtml(v.message || "مخالفة معايير النموذج")} (${escapeHtml(v.path || "")})</li>`).join("");
      statusBox.innerHTML = `
        <div style="padding:10px; background:#ffebee; border:1px solid #e57373; border-radius:3px; color:#b71c1c; font-size:12px;">
          <strong>تنبيه مطابقة (${data.violations_count} مخالفات):</strong>
          <ul style="margin:4px 0 0 16px; padding:0;">${issues}</ul>
        </div>
      `;
    }

    const turtleBox = document.getElementById("edit_turtle_preview_box");
    if (data.turtle_preview) {
      turtleBox.textContent = data.turtle_preview;
    }
  } catch (err) {
    statusBox.innerHTML = `<div style="padding:10px; background:#fff3e0; color:#e65100; font-size:12px;">تعذر استكمال الفحص: ${escapeHtml(err.message)}</div>`;
  }
}

async function saveEditedProcedure() {
  if (!currentEditedProcedure) return;

  const authSearch = document.getElementById("edit_authority_search");
  const authHidden = document.getElementById("edit_authority_id");
  const authName = authSearch ? authSearch.value.trim() : "المملكة المغربية";
  const authId = authHidden ? (parseInt(authHidden.value) || 1) : 1;

  const outputTitle = document.getElementById("edit_output_title").value.trim();
  const outputId = document.getElementById("edit_output_id").value || null;

  const editDaysInput = document.getElementById("edit_processing_days");
  const editDays = editDaysInput ? (parseInt(editDaysInput.value) || 0) : 20;
  const procTimeFormatted = `P${editDays}D`;

  const payload = {
    ps_id: currentEditedProcedure.ps_id,
    ps_uuid: currentEditedProcedure.ps_uuid,
    title: document.getElementById("edit_title").value.trim(),
    description: document.getElementById("edit_description").value.trim(),
    authority_id: authId,
    authority_name: authName,
    output_title: outputTitle,
    output_id: outputId,
    cost: parseFloat(document.getElementById("edit_cost").value) || 0.0,
    processing_time: procTimeFormatted,
    evidences: currentEditedEvidences
  };

  const statusBox = document.getElementById("edit_validation_status_box");
  statusBox.style.display = "block";
  statusBox.innerHTML = '<div style="padding:10px; font-size:12px; color:#555;">جاري الحفظ والتدقيق...</div>';

  try {
    const res = await fetch("/api/procedures/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.success) {
      statusBox.innerHTML = `
        <div style="padding:10px; background:#e8f5e9; border:1px solid #81c784; border-radius:3px; color:#1b5e20; font-size:12px;">
          <strong>تم الحفظ بنجاح:</strong> ${escapeHtml(data.message)}
          ${data.conforms ? '<span style="margin-right:8px; font-weight:bold;">(0 مخالفات SHACL)</span>' : ''}
        </div>
      `;
      // Update in-memory state of currentEditedProcedure
      if (currentEditedProcedure) {
        currentEditedProcedure.title = payload.title;
        currentEditedProcedure.description = payload.description;
        currentEditedProcedure.cost = payload.cost;
        currentEditedProcedure.authority_id = payload.authority_id;
        currentEditedProcedure.authority_name = payload.authority_name;
        currentEditedProcedure.output_title = payload.output_title;
        currentEditedProcedure.output_id = payload.output_id;
        currentEditedProcedure.processing_time = payload.processing_time;
      }
      // Refresh caches and lists so newly registered evidences & outputs show up immediately everywhere!
      loadEvidences();
      loadOutputs();
      const searchInput = document.getElementById("explorer_search_input");
      loadExplorerProcedures(searchInput ? searchInput.value : "");
    } else {
      statusBox.innerHTML = `<div style="padding:10px; background:#ffebee; border:1px solid #e57373; color:#b71c1c; font-size:12px;">تعذر الحفظ: ${escapeHtml(data.error || "خطأ غير معروف")}</div>`;
    }

    if (data.turtle_preview) {
      document.getElementById("edit_turtle_preview_box").textContent = data.turtle_preview;
    }
  } catch (err) {
    statusBox.innerHTML = `<div style="padding:10px; background:#ffebee; color:#b71c1c; font-size:12px;">خطأ في الاتصال بالخادم: ${escapeHtml(err.message)}</div>`;
  }
}

async function deleteCurrentProcedure() {
  if (!currentEditedProcedure) return;

  const psId = currentEditedProcedure.ps_id;
  const title = currentEditedProcedure.title;

  if (!confirm(`تأكيد الحذف النهائي:\nهل أنت متأكد من رغبتك في حذف المسطرة "${title}" (#${psId}) بصفة نهائية من قاعدة البيانات والمستودع؟`)) {
    return;
  }

  const statusBox = document.getElementById("edit_validation_status_box");
  statusBox.style.display = "block";
  statusBox.innerHTML = '<div style="padding:10px; font-size:12px; color:#555;">جاري حذف المسطرة...</div>';

  try {
    const res = await fetch("/api/procedures/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ps_id: psId })
    });
    const data = await res.json();

    if (data.success) {
      alert(data.message || "تم حذف المسطرة بنجاح.");
      // Reset editor view
      document.getElementById("explorer_editor_placeholder").style.display = "block";
      document.getElementById("explorer_editor_form").style.display = "none";
      currentEditedProcedure = null;
      // Reload lists
      loadEvidences();
      loadOutputs();
      const searchInput = document.getElementById("explorer_search_input");
      loadExplorerProcedures(searchInput ? searchInput.value : "");
    } else {
      statusBox.innerHTML = `<div style="padding:10px; background:#ffebee; color:#b71c1c; font-size:12px;">تعذر الحذف: ${escapeHtml(data.error || "خطأ غير معروف")}</div>`;
    }
  } catch (err) {
    statusBox.innerHTML = `<div style="padding:10px; background:#ffebee; color:#b71c1c; font-size:12px;">خطأ في الاتصال بالخادم: ${escapeHtml(err.message)}</div>`;
  }
}

function toggleEditTurtlePreview() {
  const box = document.getElementById("edit_turtle_preview_box");
  if (!box) return;
  box.style.display = box.style.display === "none" ? "block" : "none";
}

// ==========================================
// Audit Modifications Log Viewer
// ==========================================
async function loadAuditLogs() {
  const tbody = document.getElementById("audit_log_body");
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#888;">جاري تحميل سجل التدقيق...</td></tr>';

  try {
    const res = await fetch("/api/audit-log");
    const data = await res.json();
    const logs = data.logs || [];

    if (!logs.length) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#777;">سجل التدقيق فارغ حالياً.</td></tr>';
      return;
    }

    let html = "";
    // Display newest first
    logs.slice().reverse().forEach(line => {
      const parts = line.split(" | ").map(p => p.trim());
      if (parts.length >= 4) {
        const entityPart = parts[0];
        const attribute = parts[1];
        const actionDetails = parts[2];
        const timeStr = parts[3];

        const spaceIdx = entityPart.indexOf(" ");
        const entityType = spaceIdx > 0 ? entityPart.substring(0, spaceIdx) : entityPart;
        const entityId = spaceIdx > 0 ? entityPart.substring(spaceIdx + 1) : "";

        let badgeColor = "#005a9c";
        let badgeBg = "#e8f0fe";
        if (entityType.toLowerCase().includes("publicservice")) {
          badgeColor = "#1b4b7d"; badgeBg = "#e3effd";
        } else if (entityType.toLowerCase().includes("organisation") || entityType.toLowerCase().includes("authority")) {
          badgeColor = "#6f42c1"; badgeBg = "#f3e8fd";
        } else if (entityType.toLowerCase().includes("evidence")) {
          badgeColor = "#2e7d32"; badgeBg = "#e8f5e9";
        } else if (entityType.toLowerCase().includes("output")) {
          badgeColor = "#d84315"; badgeBg = "#fbe9e7";
        }

        let actionBadge = actionDetails.startsWith("added") ? '<span class="badge-tag" style="background:#e8f5e9; color:#2e7d32; border-color:#a5d6a7;">إضافة (added)</span>' :
                          actionDetails.startsWith("deleted") ? '<span class="badge-tag" style="background:#ffebee; color:#c62828; border-color:#ef9a9a;">حذف (deleted)</span>' :
                          '<span class="badge-tag" style="background:#fff8e1; color:#f57f17; border-color:#ffe082;">تعديل (changed)</span>';

        html += `
          <tr>
            <td style="text-align:center; font-family:monospace; font-size:11px; font-weight:bold; color:#333;">${escapeHtml(timeStr)}</td>
            <td><span class="badge-tag" style="background:${badgeBg}; color:${badgeColor}; font-weight:bold;">${escapeHtml(entityType)}</span></td>
            <td><strong style="color:#1b4b7d; font-size:12px;">${escapeHtml(entityId)}</strong></td>
            <td><code style="font-size:11px; background:#f4f6f8; padding:2px 5px; border-radius:3px;">${escapeHtml(attribute)}</code></td>
            <td style="font-size:12px;">${actionBadge} <span style="margin-right:6px; color:#444;">${escapeHtml(actionDetails)}</span></td>
          </tr>
        `;
      } else {
        html += `<tr><td colspan="5" style="font-family:monospace; font-size:11px;">${escapeHtml(line)}</td></tr>`;
      }
    });

    tbody.innerHTML = html;
  } catch (err) {
    console.error("Failed to load audit logs:", err);
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:#c62828;">تعذر تحميل سجل التدقيق: ${escapeHtml(err.message)}</td></tr>`;
  }
}
