document.addEventListener('DOMContentLoaded', () => {
    initModals();
    initClickableRows();
    initDeleteConfirmations();
    initDependentTestValues();
    initDependentMedicalOrganization();
    initReferenceSelector();
});

function initModals() {
    document.querySelectorAll('[data-open-modal]').forEach((button) => {
        button.addEventListener('click', () => {
            const modalId = button.getAttribute('data-open-modal');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('is-open');
                modal.setAttribute('aria-hidden', 'false');
            }
        });
    });

    document.querySelectorAll('[data-close-modal]').forEach((element) => {
        element.addEventListener('click', () => closeModal(element.closest('.modal')));
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal.is-open').forEach(closeModal);
        }
    });
}

function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
}

function initClickableRows() {
    document.querySelectorAll('tr[data-href]').forEach((row) => {
        row.addEventListener('click', () => {
            window.location.href = row.getAttribute('data-href');
        });
    });
}

function initDeleteConfirmations() {
    document.querySelectorAll('.js-confirm').forEach((form) => {
        form.addEventListener('submit', (event) => {
            const message = form.getAttribute('data-confirm') || 'Подтвердить действие?';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
}

function initDependentTestValues() {
    const testCodeSelect = document.getElementById('testCodeSelect');
    const testResultSelect = document.getElementById('testResultSelect');

    if (!testCodeSelect || !testResultSelect) return;

    testCodeSelect.addEventListener('change', async () => {
        const testCodeId = testCodeSelect.value;
        await loadTestValues(testCodeId, '');
    });
}

async function loadTestValues(testCodeId, selectedValue) {
    const testCodeSelect = document.getElementById('testCodeSelect');
    const testResultSelect = document.getElementById('testResultSelect');

    if (!testCodeSelect || !testResultSelect) return;

    testResultSelect.innerHTML = '<option value="">Не выбрано</option>';

    if (!testCodeId) return;

    const urlTemplate = testCodeSelect.getAttribute('data-values-url-template');
    const url = urlTemplate.replace('/0', `/${testCodeId}`);

    try {
        const response = await fetch(url, {headers: {'Accept': 'application/json'}});
        if (!response.ok) return;

        const values = await response.json();
        values.forEach((item) => {
            const option = document.createElement('option');
            option.value = item.VALUE_ID;
            option.textContent = item.TEST_VALUE;
            if (String(item.VALUE_ID) === String(selectedValue)) {
                option.selected = true;
            }
            testResultSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Не удалось загрузить результаты исследования', error);
    }
}



function initDependentMedicalOrganization() {
    const muSelect = document.getElementById('muSelect');
    const officeField = document.getElementById('muOfficeField');
    const officeSelect = document.getElementById('muOfficeSelect');

    if (!muSelect || !officeField || !officeSelect) return;

    const kkptdId = muSelect.getAttribute('data-kkptd-id') || '13812';
    const selectedOfficeId = officeSelect.getAttribute('data-selected-value') || '';

    const updateOfficeBlock = async (preserveSelected = false) => {
        const selectedMuId = muSelect.value;
        const needOffice = String(selectedMuId) === String(kkptdId);

        officeField.classList.toggle('is-hidden', !needOffice);
        officeSelect.required = needOffice;

        if (!needOffice) {
            officeSelect.value = '';
            return;
        }

        await loadMuOffices(selectedMuId, preserveSelected ? selectedOfficeId : '');
    };

    muSelect.addEventListener('change', async () => {
        await updateOfficeBlock(false);
    });

    updateOfficeBlock(true);
}

async function loadMuOffices(muId, selectedValue) {
    const muSelect = document.getElementById('muSelect');
    const officeSelect = document.getElementById('muOfficeSelect');

    if (!muSelect || !officeSelect) return;

    officeSelect.innerHTML = '<option value="">Выберите подразделение</option>';
    if (!muId) return;

    const urlTemplate = muSelect.getAttribute('data-offices-url-template');
    const url = urlTemplate.replace('/0', `/${muId}`);

    try {
        const response = await fetch(url, {headers: {'Accept': 'application/json'}});
        if (!response.ok) return;

        const offices = await response.json();
        offices.forEach((item) => {
            const option = document.createElement('option');
            option.value = item.IDMU;
            option.textContent = item.SH_LNAME || item.MU || item.MUFL || `Подразделение ${item.IDMU}`;
            if (String(item.IDMU) === String(selectedValue)) {
                option.selected = true;
            }
            officeSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Не удалось загрузить подразделения учреждения', error);
    }
}

function initReferenceSelector() {
    const select = document.getElementById('referenceTableSelect');
    if (!select) return;

    select.addEventListener('change', () => {
        const baseUrl = select.getAttribute('data-url');
        const tableKey = select.value;
        window.location.href = `${baseUrl}?table=${encodeURIComponent(tableKey)}`;
    });
}
