// Dark mode toggle script
const toggleSwitch = document.getElementById('theme-toggle');

// Check for saved user preference, if any
if (localStorage.getItem('dark-mode') === 'enabled') {
    document.body.classList.add('dark-mode');
    toggleSwitch.checked = true;
}

// Toggle dark mode on button click
toggleSwitch.addEventListener('change', function() {
    if (this.checked) {
        document.body.classList.add('dark-mode');
        localStorage.setItem('dark-mode', 'enabled');
    } else {
        document.body.classList.remove('dark-mode');
        localStorage.setItem('dark-mode', 'disabled');
    }
});

// Function to confirm deletion
function confirmDelete(event) {
    // Prevent the form from being submitted immediately
    event.preventDefault();

    // Show confirmation dialog
    const confirmed = confirm("Are you sure you want to delete this subject?");

    // If the user confirms, submit the form
    if (confirmed) {
        event.target.closest('form').submit();
    }
}

// Global function to open edit modal (used by onclick attribute)
function openEditModal(paperId, paperName, paperDescription, paperLink) {
    const modal = document.getElementById('editPaperModal');
    if (!modal) return;
    
    document.getElementById('modal-paper-id').value = paperId;
    document.getElementById('modal-name').value = paperName;
    document.getElementById('modal-description').value = paperDescription;
    document.getElementById('modal-current-file').textContent = paperLink;
    modal.style.display = "block";
}

// Add event listeners once the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add delete functionality to delete buttons
    document.querySelectorAll('.btn-delete-subject').forEach(button => {
        button.addEventListener('click', confirmDelete);
    });

    // Get modal elements
    const addSubjectModal = document.getElementById("addSubjectModal");
    const closeAddSubjectModal = document.getElementById("closeAddSubjectModal");
    const editSubjectModal = document.getElementById("editSubjectModal");
    const closeEditSubjectModal = document.getElementById("closeEditSubjectModal");

    // Add Subject Modal functionality
    const addSubjectBtn = document.getElementById('addSubjectBtn');

    // Open Add Subject Modal
    if (addSubjectBtn) {
        addSubjectBtn.onclick = function() {
            addSubjectModal.style.display = 'block';
        };
    }

    // Close the Add Subject Modal
    if (closeAddSubjectModal) {
        closeAddSubjectModal.onclick = function() {
            addSubjectModal.style.display = 'none';
        };
    }

    // Edit Subject Modal functionality
    const editButtons = document.querySelectorAll(".btn-edit-subject");

    // Add event listeners to all edit buttons
    editButtons.forEach(button => {
        button.addEventListener("click", function() {
            // Retrieve subject data from the button's attributes
            const subjectId = this.getAttribute("data-id");
            const subjectName = this.getAttribute("data-name");
            const subjectDescription = this.getAttribute("data-description");

            // Populate the modal fields with the subject's data
            const editSubjectModal = document.getElementById(`editSubjectModal${subjectId}`);
            const editSubjectName = document.getElementById(`editSubjectName${subjectId}`);
            const editSubjectDescription = document.getElementById(`editSubjectDescription${subjectId}`);

            editSubjectName.value = subjectName;
            editSubjectDescription.value = subjectDescription;

            // Display the modal
            if (editSubjectModal) {
                editSubjectModal.style.display = "block";
            }
        });
    });

    // Close the Edit Subject modal when the close button is clicked
    const closeButtons = document.querySelectorAll(".close");
    closeButtons.forEach(closeButton => {
        closeButton.addEventListener("click", function() {
            const modalId = this.getAttribute("id").replace("close", "editSubjectModal");
            const modal = document.getElementById(modalId);
            
            if (modal) {
                modal.style.display = "none";
            }
        });
    });


    // Paper Modal Elements
    const addPaperModal = document.getElementById("addPaperModal");
    const addPaperBtn = document.getElementById("addPaperBtn");
    const closeAddPaperModal = document.getElementById("closeAddPaperModal");
    const editPaperModal = document.getElementById('editPaperModal');
    const closeEditPaperModal = document.getElementById('closeEditPaperModal');

    // Add Paper Modal functionality
    if (addPaperBtn) {
        addPaperBtn.onclick = function() {
            addPaperModal.style.display = "block";
        }
    }

    if (closeAddPaperModal) {
        closeAddPaperModal.onclick = function() {
            addPaperModal.style.display = "none";
        }
    }

    // Edit Paper Modal functionality
    if (closeEditPaperModal) {
        closeEditPaperModal.onclick = function() {
            editPaperModal.style.display = "none";
        }
    }

    // Handle edit paper form submission
    const editPaperForm = document.getElementById('editPaperForm');
    if (editPaperForm) {
        editPaperForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submitted');
            
            const formData = new FormData(this);
            const paperId = document.getElementById('modal-paper-id').value;
            console.log('Paper ID:', paperId);
            
            // Log form data
            for (let pair of formData.entries()) {
                console.log(pair[0] + ': ' + pair[1]);
            }
            
            // Make the POST request to update the paper
            fetch(`/edit_paper/${paperId}`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                console.log('Response status:', response.status);
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Server returned non-JSON response');
                }
                return response.json().then(data => {
                    if (!response.ok) {
                        throw new Error(data.message || 'Server error');
                    }
                    return data;
                });
            })
            .then(data => {
                console.log('Success:', data);
                if (data.success) {
                    // Update the paper content in the DOM
                    const paperId = document.getElementById('modal-paper-id').value;
                    const paperName = document.getElementById('modal-name').value;
                    const paperDescription = document.getElementById('modal-description').value;
                    const currentFile = document.getElementById('modal-current-file').textContent;
                    
                    // Find and update the paper card using the edit button
                    const editButton = document.querySelector(`.btn-edit-paper[onclick*="${paperId}"]`);
                    if (editButton) {
                        const paperCard = editButton.closest('.catalogue-item');
                        const nameElement = paperCard.querySelector('.content h3');
                        const descriptionElement = paperCard.querySelector('.content p');
                        const fileElement = paperCard.querySelector('.content a'); // Assuming it's a link with class "content"

                        // Update the paper name and description
                        if (nameElement) nameElement.textContent = data.paper_name;
                        if (descriptionElement) descriptionElement.textContent = data.paper_description;
                        
                        // Update the file link if the file has changed
                        if (fileElement && data.paper_link) {
                            fileElement.textContent = `Download ${data.paper_link}`;
                            fileElement.setAttribute('href', `/static/papers/${data.paper_link}`);
                        }
                        
                        // Update the edit button's onclick attribute
                        editButton.setAttribute('onclick', 
                            `openEditModal('${data.paper_id}', '${data.paper_name}', '${data.paper_description}', '${data.paper_link}')`
                        );
                    }
                    
                    // Close the modal
                    const editPaperModal = document.getElementById('editPaperModal');
                    if (editPaperModal) {
                        editPaperModal.style.display = 'none';
                    }
                } else {
                    alert(data.message || 'Error updating paper');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error updating paper: ' + error.message);
            });
        });
    }


    // Add delete functionality to paper buttons
    document.querySelectorAll('.btn-delete-paper').forEach(button => {
        button.addEventListener('click', confirmDelete);
    });

    // Close modals when clicking outside
    window.onclick = function(event) {
        if (event.target === addSubjectModal) {
            addSubjectModal.style.display = 'none';
        }
        if (event.target === editSubjectModal) {
            editSubjectModal.style.display = 'none';
        }
        if (event.target === addPaperModal) {
            addPaperModal.style.display = 'none';
        }
        if (event.target === editPaperModal) {
            editPaperModal.style.display = 'none';
        }
    }
});

// Add Paper Note Modal Elements
const addPaperNoteModal = document.getElementById("addPaperNoteModal");
const closeAddPaperNoteModal = document.getElementById("closeAddPaperNoteModal");

// Function to open Add Paper Note modal
function openAddPaperNoteModal(paperId) {
    const modal = document.getElementById('addPaperNoteModal');
    if (!modal) return;

    // Set the paper ID for the note
    document.querySelector('input[name="paper_id"]').value = paperId;

    // Open the modal
    modal.style.display = "block";
}

// Event listener for closing Add Paper Note modal
if (closeAddPaperNoteModal) {
    closeAddPaperNoteModal.onclick = function() {
        addPaperNoteModal.style.display = "none";
    };
}

// Close modals when clicking outside (for specific modals)
window.addEventListener('click', function(event) {
    if (event.target === addPaperNoteModal) {
        addPaperNoteModal.style.display = 'none';
    }
});
