// Dark mode toggle script
const toggleSwitch = document.getElementById('theme-toggle');

// Apply saved dark mode preference
if (localStorage.getItem('dark-mode') === 'enabled') {
    document.body.classList.add('dark-mode');
    toggleSwitch.checked = true;
}

toggleSwitch.addEventListener('change', function () {
    if (this.checked) {
        document.body.classList.add('dark-mode');
        localStorage.setItem('dark-mode', 'enabled');
    } else {
        document.body.classList.remove('dark-mode');
        localStorage.setItem('dark-mode', 'disabled');
    }
});

// Confirm deletion
function confirmDelete(event) {
    event.preventDefault();
    const confirmed = confirm("Are you sure you want to delete this subject?");
    if (confirmed) {
        event.target.closest('form').submit();
    }
}

// Global paper edit modal opener
function openEditModal(paperId, paperName, paperDescription, paperLink) {
    const modal = document.getElementById('editPaperModal');
    if (!modal) return;

    document.getElementById('modal-paper-id').value = paperId;
    document.getElementById('modal-name').value = paperName;
    document.getElementById('modal-description').value = paperDescription;
    document.getElementById('modal-current-file').textContent = paperLink;
    modal.style.display = "block";
}

document.addEventListener('DOMContentLoaded', () => {
    // Delete subject buttons
    document.querySelectorAll('.btn-delete-subject').forEach(button => {
        button.addEventListener('click', confirmDelete);
    });

    // Add Subject modal
    const addSubjectModal = document.getElementById("addSubjectModal");
    const closeAddSubjectModal = document.getElementById("closeAddSubjectModal");
    const addSubjectBtn = document.getElementById('addSubjectBtn');
    if (addSubjectBtn) {
        addSubjectBtn.onclick = () => addSubjectModal.style.display = 'block';
    }
    if (closeAddSubjectModal) {
        closeAddSubjectModal.onclick = () => addSubjectModal.style.display = 'none';
    }

    // Edit Subject modal(s)
    const editButtons = document.querySelectorAll(".btn-edit-subject");
    editButtons.forEach(button => {
        button.addEventListener("click", () => {
            const subjectId = button.getAttribute("data-id");
            const name = button.getAttribute("data-name");
            const description = button.getAttribute("data-description");

            const modal = document.getElementById(`editSubjectModal${subjectId}`);
            const nameInput = document.getElementById(`editSubjectName${subjectId}`);
            const descInput = document.getElementById(`editSubjectDescription${subjectId}`);

            nameInput.value = name;
            descInput.value = description;
            if (modal) modal.style.display = "block";
        });
    });

    document.querySelectorAll(".close").forEach(closeBtn => {
        closeBtn.addEventListener("click", function () {
            const modalId = this.getAttribute("id").replace("close", "editSubjectModal");
            const modal = document.getElementById(modalId);
            if (modal) modal.style.display = "none";
        });
    });

    // Add/Edit Paper modals
    const addPaperModal = document.getElementById("addPaperModal");
    const addPaperBtn = document.getElementById("addPaperBtn");
    const closeAddPaperModal = document.getElementById("closeAddPaperModal");

    const editPaperModal = document.getElementById("editPaperModal");
    const closeEditPaperModal = document.getElementById("closeEditPaperModal");

    if (addPaperBtn) {
        addPaperBtn.onclick = () => addPaperModal.style.display = "block";
    }
    if (closeAddPaperModal) {
        closeAddPaperModal.onclick = () => addPaperModal.style.display = "none";
    }
    if (closeEditPaperModal) {
        closeEditPaperModal.onclick = () => editPaperModal.style.display = "none";
    }

    // Edit paper form submission
    const editPaperForm = document.getElementById('editPaperForm');
    if (editPaperForm) {
        editPaperForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const formData = new FormData(this);
            const paperId = document.getElementById('modal-paper-id').value;

            fetch(`/edit_paper/${paperId}`, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => {
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Non-JSON response from server');
                }
                return response.json().then(data => {
                    if (!response.ok) throw new Error(data.message || 'Server error');
                    return data;
                });
            })
            .then(data => {
                if (data.success) {
                    const paperCard = document.querySelector(`.btn-edit-paper[onclick*="${paperId}"]`)?.closest('.catalogue-item');
                    if (paperCard) {
                        paperCard.querySelector('.content h3').textContent = data.paper_name;
                        paperCard.querySelector('.content p').textContent = data.paper_description;
                        const link = paperCard.querySelector('.content a');
                        if (link && data.paper_link) {
                            link.textContent = `Download ${data.paper_link}`;
                            link.href = `/static/papers/${data.paper_link}`;
                        }
                    }

                    const editBtn = document.querySelector(`.btn-edit-paper[onclick*="${paperId}"]`);
                    if (editBtn) {
                        editBtn.setAttribute('onclick', 
                            `openEditModal('${data.paper_id}', '${data.paper_name}', '${data.paper_description}', '${data.paper_link}')`
                        );
                    }

                    editPaperModal.style.display = "none";
                } else {
                    alert(data.message || 'Error updating paper');
                }
            })
            .catch(err => {
                alert('Error: ' + err.message);
                console.error(err);
            });
        });
    }

    // Delete paper buttons
    document.querySelectorAll('.btn-delete-paper').forEach(button => {
        button.addEventListener('click', confirmDelete);
    });

    // Paper Note Modal
    const addPaperNoteModal = document.getElementById("addPaperNoteModal");
    const closeAddPaperNoteModal = document.getElementById("closeAddPaperNoteModal");

    if (closeAddPaperNoteModal) {
        closeAddPaperNoteModal.onclick = () => {
            addPaperNoteModal.style.display = "none";
        };
    }

    // Global modal close on outside click
    window.addEventListener('click', function (event) {
        [
            addSubjectModal,
            editSubjectModal,
            addPaperModal,
            editPaperModal,
            addPaperNoteModal
        ].forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
});

// Open Add Paper Note Modal
function openAddPaperNoteModal(paperId) {
    const modal = document.getElementById('addPaperNoteModal');
    if (!modal) return;

    document.querySelector('input[name="paper_id"]').value = paperId;
    modal.style.display = "block";
}
