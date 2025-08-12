// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded, initializing form...');
    
    // Wait for AJAX content to load
    setTimeout(function() {
        initializeLeaveForm();
        setupLeaveForm();
    }, 500);
});

// Function to setup leave form
function setupLeaveForm() {
    console.log('Setting up leave form...');
    
    // Set default dates
    const today = new Date().toISOString().split('T')[0];
    const startDateInput = document.getElementById('start_date') || document.getElementById('startDate');
    const endDateInput = document.getElementById('end_date') || document.getElementById('endDate');
    
    if (startDateInput) {
        startDateInput.value = today;
        startDateInput.addEventListener('change', calculateDays);
        console.log('Start date input found and configured');
    } else {
        console.log('Start date input not found');
    }
    
    if (endDateInput) {
        endDateInput.value = today;
        endDateInput.addEventListener('change', calculateDays);
        console.log('End date input found and configured');
    } else {
        console.log('End date input not found');
    }
    
    // Add event listener for leave type
    const leaveTypeSelect = document.getElementById('leave_type') || document.getElementById('leaveType');
    if (leaveTypeSelect) {
        leaveTypeSelect.addEventListener('change', toggleMedicalCertificate);
        console.log('Leave type select found and configured');
        
        // Check URL parameters for pre-filled data
        const urlParams = new URLSearchParams(window.location.search);
        const leaveTypeFromUrl = urlParams.get('leave_type');
        if (leaveTypeFromUrl) {
            console.log('Setting leave type from URL:', leaveTypeFromUrl);
            leaveTypeSelect.value = leaveTypeFromUrl;
            toggleMedicalCertificate();
        }
    } else {
        console.log('Leave type select not found');
    }
    
    // Load leave history
    loadLeaveHistory();
}

// Function to toggle medical certificate section
function toggleMedicalCertificate() {
    console.log('Toggle medical certificate called');
    const leaveType = document.getElementById('leave_type') || document.getElementById('leaveType');
    const medicalSection = document.getElementById('medical_certificate_section');
    
    if (!leaveType || !medicalSection) {
        console.log('Required elements not found');
        return;
    }
    
    console.log('Leave type selected:', leaveType.value);
    
    if (leaveType.value === 'ลาป่วย') {
        console.log('Showing medical certificate section');
        medicalSection.style.display = 'block';
    } else {
        console.log('Hiding medical certificate section');
        medicalSection.style.display = 'none';
        const medicalCertInput = document.getElementById('medical_certificate');
        if (medicalCertInput) medicalCertInput.value = '';
    }
}

// Calculate days between start and end date
function calculateDays() {
    const startDateInput = document.getElementById('start_date') || document.getElementById('startDate');
    const endDateInput = document.getElementById('end_date') || document.getElementById('endDate');
    const startDate = new Date(startDateInput.value);
    const endDate = new Date(endDateInput.value);
    const daysInput = document.getElementById('days_requested') || document.getElementById('daysRequested');
    
    if (startDate && endDate && endDate >= startDate && daysInput) {
        const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
        daysInput.value = days;
    }
}

// Handle form submission
function initializeLeaveForm() {
    const form = document.getElementById('leaveRequestForm');
    if (!form) {
        console.log('Leave request form not found, waiting for page load...');
        return;
    }
    
    console.log('Leave request form found, adding event listener');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Form submitted');
        
        // Get form data
        const formData = new FormData();
        formData.append('leave_type', document.getElementById('leave_type').value);
        formData.append('start_date', document.getElementById('start_date').value);
        formData.append('end_date', document.getElementById('end_date').value);
        formData.append('days_requested', document.getElementById('days_requested').value);
        formData.append('reason', document.getElementById('reason').value);
        
        // Handle file upload
        const medicalCertificateInput = document.getElementById('medical_certificate');
        if (medicalCertificateInput && medicalCertificateInput.files.length > 0) {
            console.log('Adding medical certificate file');
            formData.append('medical_certificate', medicalCertificateInput.files[0]);
        }
        
        console.log('Sending request to /api/leave/request');
        
        // Send request
        fetch('/api/leave/request', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('Response received:', response);
            return response.json();
        })
        .then(data => {
            console.log('Data received:', data);
            if (data.success) {
                alert('ส่งคำขอการลาสำเร็จ');
                // Reset form
                form.reset();
                // Reset dates
                const today = new Date().toISOString().split('T')[0];
                const startDateInput = document.getElementById('start_date');
                const endDateInput = document.getElementById('end_date');
                if (startDateInput) startDateInput.value = today;
                if (endDateInput) endDateInput.value = today;
                // Hide medical certificate section
                const medicalSection = document.getElementById('medical_certificate_section');
                if (medicalSection) medicalSection.style.display = 'none';
                // Reload history
                loadLeaveHistory();
            } else {
                alert('เกิดข้อผิดพลาด: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('เกิดข้อผิดพลาดในการส่งคำขอ');
        });
    });
}

// Load leave history
function loadLeaveHistory() {
    console.log('Loading leave history...');
    fetch('/api/leave/my-requests')
    .then(response => response.json())
    .then(data => {
        console.log('Leave history data:', data);
        const tbody = document.getElementById('leaveHistory') || document.getElementById('leave-history-tbody');
        if (!tbody) {
            console.log('Leave history tbody not found');
            return;
        }
        
        if (data.leaves && data.leaves.length > 0) {
            tbody.innerHTML = data.leaves.map(leave => `
                <tr>
                    <td>
                        <span class="badge ${getLeaveTypeBadge(leave.leave_type)}">${leave.leave_type}</span>
                    </td>
                    <td>${leave.start_date}</td>
                    <td>${leave.end_date}</td>
                    <td>${leave.days_requested} วัน</td>
                    <td>${leave.reason}</td>
                    <td>
                        <span class="badge ${getStatusBadge(leave.status)}">${getStatusText(leave.status)}</span>
                    </td>
                    <td>${leave.approved_by || '-'}</td>
                    <td>
                        ${leave.leave_type === 'ลาป่วย' && leave.medical_certificate_path ? 
                            `<button class="btn btn-sm btn-info" onclick="downloadCertificate(${leave.id})" title="ดาวน์โหลดใบรับรองแพทย์">
                                <i class="fas fa-download"></i>
                            </button>` : 
                            '<span class="text-muted">-</span>'
                        }
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        ยังไม่มีประวัติการลา
                    </td>
                </tr>
            `;
        }
    })
    .catch(error => {
        console.error('Error loading leave history:', error);
    });
}

// Helper functions
function getLeaveTypeBadge(type) {
    switch(type) {
        case 'ลาป่วย': return 'bg-danger';
        case 'ลาพักร้อน': return 'bg-primary';
        case 'ลากิจ': return 'bg-warning';
        default: return 'bg-secondary';
    }
}

function getStatusBadge(status) {
    switch(status) {
        case 'pending': return 'bg-warning';
        case 'approved': return 'bg-success';
        case 'rejected': return 'bg-danger';
        default: return 'bg-secondary';
    }
}

function getStatusText(status) {
    switch(status) {
        case 'pending': return 'รออนุมัติ';
        case 'approved': return 'อนุมัติแล้ว';
        case 'rejected': return 'ปฏิเสธ';
        default: return status;
    }
}

function downloadCertificate(leaveId) {
    window.location.href = `/api/leave/download-certificate/${leaveId}`;
}

// Also initialize when content is loaded via AJAX
if (typeof window !== 'undefined') {
    // Listen for custom event when content is loaded
    window.addEventListener('contentLoaded', function() {
        setTimeout(function() {
            initializeLeaveForm();
            setupLeaveForm();
        }, 100);
    });
    
    // Also try to initialize periodically
    setInterval(function() {
        const form = document.getElementById('leaveRequestForm');
        if (form && !form.hasAttribute('data-initialized')) {
            console.log('Form found, initializing...');
            form.setAttribute('data-initialized', 'true');
            initializeLeaveForm();
            setupLeaveForm();
        }
    }, 1000);
} 