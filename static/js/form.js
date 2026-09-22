// ---------------------------------------------------------------------
// form.js — interaksi form input prediksi.
// PENTING: JS di sini HANYA membangun UI & mengirim RAW input apa
// adanya ke /api/preprocess. TIDAK ADA agregasi h_* (h_nmale, h_nage04,
// h_ngrad_*, dst) dilakukan di sini — semua itu tugas preprocessing
// existing di backend (preprocessing/transformer.py).
// ---------------------------------------------------------------------

const MAPPINGS = JSON.parse(document.getElementById('form-mappings').textContent);

let memberCount = 1;
let memberData = {}; // simpan input yang sudah diisi per index, supaya tidak hilang saat count berubah

const memberCardsEl = document.getElementById('member-cards');
const memberCountEl = document.getElementById('member-count');

function optionsHtml(list, selectedValue) {
  return list.map(o => {
    const v = o.value === null ? '' : o.value;
    const sel = String(v) === String(selectedValue ?? '') ? 'selected' : '';
    return `<option value="${v}" ${sel}>${o.label}</option>`;
  }).join('');
}

function renderMemberCard(index) {
  const d = memberData[index] || {};
  const isHeadChecked = (d.is_head || index === 0 && !(Object.values(memberData).some(m => m && m.is_head))) ? 'checked' : '';
  const wrap = document.createElement('div');
  wrap.className = 'member-card';
  wrap.dataset.index = index;
  wrap.innerHTML = `
    <div class="member-card-head">
      <h4>Anggota ${index + 1}</h4>
      <label class="head-toggle">
        <input type="radio" name="head_selector" value="${index}" ${isHeadChecked}>
        Kepala rumah tangga
      </label>
    </div>
    <div class="field-grid">
      <div class="field">
        <label>Jenis kelamin</label>
        <div class="radio-row">
          ${MAPPINGS.gender.map(o => `
            <label class="radio-chip">
              <input type="radio" name="gender_${index}" value="${o.value}" ${d.gender === o.value ? 'checked' : (!d.gender && o.value === 'h_nmale' ? 'checked' : '')}>
              <span>${o.label}</span>
            </label>`).join('')}
        </div>
      </div>
      <div class="field">
        <label>Umur</label>
        <input type="number" min="0" max="120" class="m-age" placeholder="cth. 30" value="${d.age ?? ''}" required>
      </div>
      <div class="field">
        <label>Pendidikan terakhir</label>
        <select class="m-education">${optionsHtml(MAPPINGS.education, d.education)}</select>
      </div>
      <div class="field">
        <label>Status sekolah</label>
        <select class="m-school">${optionsHtml(MAPPINGS.school_status, d.school_status)}</select>
      </div>
      <div class="field">
        <label>Status perkawinan</label>
        <select class="m-marital">${optionsHtml(MAPPINGS.marital_status, d.marital_status)}</select>
      </div>
      <div class="field">
        <label>Status bekerja</label>
        <select class="m-employment">${optionsHtml(MAPPINGS.employment_status, d.employment_status)}</select>
      </div>
      <div class="field m-sector-field" style="display:${d.employment_status ? 'flex' : 'none'};">
        <label>Sektor pekerjaan</label>
        <select class="m-sector">${optionsHtml(MAPPINGS.sector, d.employment_sector)}</select>
      </div>
    </div>
  `;

  const empSelect = wrap.querySelector('.m-employment');
  const sectorField = wrap.querySelector('.m-sector-field');
  const sectorSelect = wrap.querySelector('.m-sector');

  const ageInput = wrap.querySelector('.m-age');
  const schoolSelect = wrap.querySelector('.m-school');
  const schoolField = schoolSelect.closest('.field');
  const educationSelect = wrap.querySelector('.m-education');

  function updateSchoolVisibility() {
    const age = parseInt(ageInput.value, 10);
    const showSchool = Number.isFinite(age) && age >= 5; 

    schoolField.style.display = showSchool ? '' : 'none';
    schoolSelect.disabled = !showSchool;

    if (!showSchool) {
      schoolSelect.value = '';
      educationSelect.value = 'h_notgrad';
      educationSelect.disabled = true;
    } else {
      educationSelect.disabled = false;
    }
  }

  ageInput.addEventListener('input', updateSchoolVisibility);
  ageInput.addEventListener('change', updateSchoolVisibility);

  updateSchoolVisibility();

  function updateSectorVisibility() {
    const notWorking =
      empSelect.value === '0' ||
      empSelect.value === '';

    if (notWorking) {
      sectorField.style.display = 'none';
      sectorSelect.value = '';
    } else {
      sectorField.style.display = 'flex';
    }
  }

  empSelect.addEventListener('change', updateSectorVisibility);

  updateSectorVisibility();

  return wrap;
}

function renderAllMembers() {
  memberCardsEl.innerHTML = '';
  for (let i = 0; i < memberCount; i++) {
    memberCardsEl.appendChild(renderMemberCard(i));
  }
  memberCountEl.textContent = memberCount;
}

function collectMemberDataFromDOM() {
  const cards = memberCardsEl.querySelectorAll('.member-card');
  cards.forEach(card => {
    const idx = parseInt(card.dataset.index, 10);
    const genderInput = card.querySelector(`input[name="gender_${idx}"]:checked`);
    memberData[idx] = {
      is_head: false,
      gender: genderInput ? genderInput.value : null,
      age: card.querySelector('.m-age').value,
      education: card.querySelector('.m-education').value,
      school_status: card.querySelector('.m-school').value,
      marital_status: card.querySelector('.m-marital').value,
      employment_status: card.querySelector('.m-employment').value || null,
      employment_sector: card.querySelector('.m-sector').value || null,
    };
  });
  const headSelector = document.querySelector('input[name="head_selector"]:checked');
  if (headSelector) {
    const headIdx = parseInt(headSelector.value, 10);
    if (memberData[headIdx]) memberData[headIdx].is_head = true;
  }
}

document.getElementById('member-plus').addEventListener('click', () => {
  collectMemberDataFromDOM();
  memberCount += 1;
  renderAllMembers();
});

document.getElementById('member-minus').addEventListener('click', () => {
  collectMemberDataFromDOM();
  if (memberCount <= 1) return;
  const removedHasData = memberData[memberCount - 1] && (memberData[memberCount - 1].age || memberData[memberCount - 1].gender);
  if (removedHasData && !confirm(`Data Anggota ${memberCount} sudah diisi. Yakin ingin menghapusnya?`)) {
    return;
  }
  delete memberData[memberCount - 1];
  memberCount -= 1;
  renderAllMembers();
});

renderAllMembers();

// ---------------------------------------------------------------------
// Submit
// ---------------------------------------------------------------------
const form = document.getElementById('prediksi-form');
const errorBox = document.getElementById('form-error');
const debugPanel = document.getElementById('debug-panel');
const summaryCard = document.getElementById('summary-card');
const summaryBody = document.getElementById('summary-body');
const submitBtn = document.getElementById('submit-btn');

function buildPayload() {
  collectMemberDataFromDOM();
  const fd = new FormData(form);

  const members = [];
  for (let i = 0; i < memberCount; i++) {
    const d = memberData[i] || {};
    members.push({
      is_head: !!d.is_head,
      gender: d.gender,
      age: parseInt(d.age, 10),
      education: d.education,
      school_status: d.school_status,
      marital_status: d.marital_status,
      employment_status:
        !d.employment_status || d.employment_status === '0'
          ? null
          : parseInt(d.employment_status, 10),
      employment_sector: d.employment_sector ? parseInt(d.employment_sector, 10) : null,
    });
  }

  const assets = fd.getAll('assets');
  const regionVal = fd.get('region');

  return {
    region: regionVal ? parseInt(regionVal, 10) : null,
    household_count: memberCount,
    members,
    housing: {
      floor_area: parseFloat(fd.get('floor_area')),
      family_count: parseInt(fd.get('family_count'), 10),
      house_type: fd.get('house_type'),
      floor_type: fd.get('floor_type'),
      wall_type: fd.get('wall_type'),
      roof_type: fd.get('roof_type'),
      water_source: fd.get('water_source'),
      lighting_source: fd.get('lighting_source'),
      electric_power: fd.get('electric_power'),
      cooking_fuel: fd.get('cooking_fuel'),
      toilet_type: fd.get('toilet_type'),
      septic_type: fd.get('septic_type'),
    },
    assets: { owned: assets },
  };
}

function labelFor(mappingKey, value) {
  const list = MAPPINGS[mappingKey] || [];
  const found = list.find(o => String(o.value) === String(value));
  return found ? found.label : value;
}

function renderSummary(payload) {
  const nMale = payload.members.filter(m => m.gender === 'h_nmale').length;
  const nFemale = payload.members.filter(m => m.gender === 'h_nfemale').length;
  const head = payload.members.find(m => m.is_head);
  const rows = [
    ['Jumlah anggota', payload.household_count],
    ['Kepala rumah tangga', head ? (head.gender === 'h_nfemale' ? 'Perempuan' : 'Laki-laki') : '-'],
    ['Komposisi jenis kelamin', `${nMale} laki-laki, ${nFemale} perempuan`],
    ['Kondisi tempat tinggal', `${labelFor('house_type', payload.housing.house_type)}, lantai ${labelFor('floor_type', payload.housing.floor_type)}`],
    ['Aset yang dimiliki', payload.assets.owned.length ? payload.assets.owned.map(a => labelFor('assets', a)).join(', ') : 'Tidak ada'],
  ];
  summaryBody.innerHTML = rows.map(([k, v]) => `<div class="summary-row"><span>${k}</span><b>${v}</b></div>`).join('');
  summaryCard.style.display = 'block';
}

document.getElementById('btn-review').addEventListener('click', () => {
  const payload = buildPayload();
  renderSummary(payload);
  summaryCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  errorBox.style.display = 'none';
  debugPanel.style.display = 'none';

  const payload = buildPayload();
  renderSummary(payload);

  submitBtn.disabled = true;
  submitBtn.textContent = 'Memproses...';

  try {
    const res = await fetch('/api/preprocess', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) {
      console.error("=== PAYLOAD YANG DIKIRIM ===");
      console.log(JSON.stringify(payload, null, 2));

      console.error("=== RESPONSE SERVER ===");
      console.log(data);

      errorBox.textContent =
        'Terdapat masalah dalam memproses data.\n\n' +
        JSON.stringify(data.detail ?? data, null, 2);

      errorBox.style.display = 'block';
      errorBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }

    document.getElementById('debug-n-features').textContent = data.n_features;
    const tbody = document.getElementById('debug-table-body');
    tbody.innerHTML = Object.entries(data.features).map(([k, v]) => `
      <tr><td class="feat">${k}</td><td class="val">${typeof v === 'number' ? v.toFixed(4).replace(/\.?0+$/, '') : v}</td></tr>
    `).join('');
    debugPanel.style.display = 'block';
    debugPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const predictRes = await fetch('/api/predict/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const predictData = await predictRes.json();

  if (!predictRes.ok) {
    console.error("=== RESPONSE PREDICT ===");
    console.error(predictData);

    errorBox.textContent =
      'Preprocessing berhasil, tetapi prediksi gagal.\n\n' +
      JSON.stringify(predictData.detail ?? predictData, null, 2);

    errorBox.style.display = 'block';
    errorBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  console.log("=== HASIL PREDICT ===");
console.log(predictData);

// =====================================================
// HASIL PREDIKSI
// =====================================================

const hasilWrap = document.getElementById('hasil-wrap');
const hasilKabName = document.getElementById('hasil-kab-name');
const hasilError = document.getElementById('hasil-error');

hasilError.style.display = 'none';

// Kabupaten/kota
const regionSelect = document.querySelector('[name="region"]');
const selectedRegion = regionSelect?.selectedOptions[0];

hasilKabName.textContent =
  selectedRegion?.textContent?.trim() || predictData.kode_kab;

// =====================================================
// SINGLE-STAGE
// =====================================================

if (
  predictData.single_stage &&
  !predictData.single_stage.error
) {
  document.getElementById('rp-single').textContent =
    predictData.single_stage.y_pred_formatted ?? '—';
} else {
  document.getElementById('rp-single').textContent = '—';
}

// =====================================================
// TWO-STAGE
// =====================================================

if (
  predictData.two_stage &&
  !predictData.two_stage.error
) {
  document.getElementById('rp-two').textContent =
    predictData.two_stage.y_pred_formatted ?? '—';
} else {
  document.getElementById('rp-two').textContent = '—';
}

// =====================================================
// MODEL FINAL
// =====================================================

if (predictData.final_model === 'two_stage') {
  document.getElementById('badge-final').style.display = 'block';
} else {
  document.getElementById('badge-final').style.display = 'none';
}

// =====================================================
// PROBABILITAS RENTAN
// =====================================================

const pRentanPct =
  predictData.two_stage?.p_rentan_pct ?? null;

document.getElementById('gauge-pct').textContent =
  pRentanPct !== null ? `${pRentanPct}%` : '—';

// Gambar gauge
const gaugeFill = document.getElementById('gauge-fill');

if (pRentanPct !== null) {
  const gaugePath = 'M 20 90 A 70 70 0 1 1 160 90';

  gaugeFill.setAttribute('d', gaugePath);

  // Panjang pendekatan busur semicircle
  const gaugeLength = 220;

  const filledLength =
    Math.max(0, Math.min(100, pRentanPct)) / 100 * gaugeLength;

  gaugeFill.setAttribute(
    'stroke-dasharray',
    `${filledLength} ${gaugeLength}`
  );
} else {
  gaugeFill.setAttribute('d', '');
}

// =====================================================
// MODEL DEBUG
// =====================================================

  const debugModel = {
    final_model: predictData.final_model,
    single_stage: predictData.single_stage?.debug ?? null,
    two_stage: predictData.two_stage?.debug ?? null
  };

  document.getElementById('debug-model-json').textContent =
    JSON.stringify(debugModel, null, 2);

  // =====================================================
  // TAMPILKAN HASIL
  // =====================================================

  hasilWrap.style.display = 'block';

  hasilWrap.scrollIntoView({
    behavior: 'smooth',
    block: 'start'
  });

  console.log("=== HASIL PREDICT ===");
  console.log(predictData);
  } catch (err) {
    errorBox.textContent = 'Tidak bisa terhubung ke server. Coba lagi.';
    errorBox.style.display = 'block';
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Jalankan estimasi';
  }
});
