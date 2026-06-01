// app/static/js/appointment.js

/**
 * Initialize appointment booking from property page
 * Call this when user clicks "Book Appointment" button
 */
function initializeAppointmentBooking(propertyId, agentId) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        alert('Please login first');
        window.location.href = '/login';
        return;
    }

    // Navigate to appointment booking page
    window.location.href = `/appointment/book?id=${propertyId}&agent_id=${agentId}`;
}

/**
 * Go to appointments list
 */
function goToAppointments() {
    window.location.href = '/appointments';
}

/**
 * Go to appointment detail
 */
function viewAppointment(appointmentId) {
    window.location.href = `/appointment/${appointmentId}`;
}