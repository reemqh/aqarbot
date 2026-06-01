// app/static/js/property.js

// Get property ID from URL
const propertyId = new URLSearchParams(window.location.search).get('id');

if (!propertyId) {
    document.body.innerHTML = '<div class="p-8 text-center text-red-500">Property ID not found</div>';
} else {
    loadProperty();
}

async function loadProperty() {
    const token = localStorage.getItem('token');

    if (!token) {
        window.location.href = '/login';
        return;
    }

    try {
        // Fetch property data from API
        const res = await fetch(`/api/property/${propertyId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) {
            if (res.status === 404) {
                document.body.innerHTML = '<div class="p-8 text-center text-red-500">' +
                    (lang === 'ar' ? 'العقار غير موجود' : 'Property not found') + '</div>';
            } else {
                document.body.innerHTML = '<div class="p-8 text-center text-red-500">' +
                    (lang === 'ar' ? 'خطأ في تحميل العقار' : 'Error loading property') + '</div>';
            }
            return;
        }

        const data = await res.json();
        const property = data.property;
        const agent = data.agent;

        if (!property) {
            document.body.innerHTML = '<div class="p-8 text-center text-red-500">' +
                (lang === 'ar' ? 'لا توجد بيانات' : 'No property data') + '</div>';
            return;
        }

        // Display property details
        displayProperty(property, agent);

    } catch (err) {
        console.error('Error loading property:', err);
        document.body.innerHTML = '<div class="p-8 text-center text-red-500">' +
            (lang === 'ar' ? 'فشل التحميل' : 'Failed to load property') + '</div>';
    }
}

function displayProperty(property, agent) {
    // Parse amenities
    let amenitiesList = [];
    if (typeof property.amenities === 'string') {
        amenitiesList = property.amenities.split(',').map(a => a.trim());
    } else if (Array.isArray(property.amenities)) {
        amenitiesList = property.amenities;
    }

    // Update image
    const imageContainer = document.getElementById('propertyImage');
    if (property.image_url) {
        imageContainer.innerHTML = `<img src="${property.image_url}" alt="${property.title}" class="max-w-full max-h-full object-contain">`;
    } else {
        imageContainer.innerHTML = `
            <div class="w-full max-h-64 bg-gray-200 flex items-center justify-center text-gray-500">
                ${lang === 'ar' ? 'لا توجد صورة' : 'No image available'}
            </div>
        `;
    }

    // Update title and price
    document.getElementById('propertyTitle').textContent = property.title;
    document.getElementById('propertyPrice').textContent = property.price?.toLocaleString() + ' ر.س';

    // Update quick info
    document.getElementById('propertyLocation').textContent = property.location;
    document.getElementById('propertyType').textContent = property.property_type;
    document.getElementById('propertyBeds').textContent = property.num_bedrooms;
    document.getElementById('propertyArea').textContent = property.area_sqft?.toLocaleString();

    // Update description
    document.getElementById('propertyDescription').textContent = property.description || (lang === 'ar' ? 'لا يوجد وصف' : 'No description available');

    // Update amenities
    const amenitiesContainer = document.getElementById('propertyAmenities');
    if (amenitiesList.length > 0) {
        amenitiesContainer.innerHTML = amenitiesList.map(a => `
            <span class="bg-aqar-mint text-aqar-dark px-3 py-1 rounded-full text-sm">
                ${a}
            </span>
        `).join('');
    } else {
        amenitiesContainer.innerHTML = `<span class="text-gray-500">${lang === 'ar' ? 'لا توجد مرافق' : 'No amenities listed'}</span>`;
    }

    // Load agent info
    if (agent) {
        displayAgent(agent);
    } else {
        document.getElementById('agentSection').style.display = 'none';
    }

    // ✅ Store property and agent data globally for appointment booking
    // This allows bookAppointment() function to access dynamic property/agent data
    window.currentPropertyData = {
        propertyId: property.id,
        agentId: agent?.id,
        propertyTitle: property.title,
        agentName: agent?.name
    };

    console.log('Property data stored for booking:', window.currentPropertyData);
}

function displayAgent(agent) {
    if (!agent) {
        document.getElementById('agentSection').style.display = 'none';
        return;
    }

    document.getElementById('agentName').textContent = agent.name || '-';
    document.getElementById('agencyName').textContent = agent.agency_name || '-';

    // ✅ FIX: Check if element exists before setting properties
    const agentSpecElement = document.getElementById('agentSpec');
    if (agentSpecElement && agentSpecElement.querySelector('span')) {
        agentSpecElement.querySelector('span').textContent = agent.specializations || '-';
    }

    const agentRatingElement = document.getElementById('agentRating');
    if (agentRatingElement && agentRatingElement.querySelector('span')) {
        agentRatingElement.querySelector('span').textContent = agent.rating || '0';
    }

    // ✅ FIX: Check if element exists before setting href
    const phoneLink = document.getElementById('agentPhone');
    if (phoneLink) {
        phoneLink.href = `tel:${agent.phone_number}`;
    }

    document.getElementById('agentPhoneDisplay').textContent = agent.phone_number || '-';

    // ✅ FIX: Check if element exists before setting href
    const emailLink = document.getElementById('agentEmail');
    if (emailLink) {
        emailLink.href = `mailto:${agent.email}`;
        emailLink.textContent = agent.email || '-';
    }
}

/**
 * ✅ NEW: Dynamic appointment booking function
 * Gets propertyId and agentId from window.currentPropertyData
 * (which is set in displayProperty function)
 * No parameters needed - data is loaded from the page
 */
function bookAppointment() {
    const token = localStorage.getItem('token');

    // Check if user is logged in
    if (!token) {
        alert(lang === 'ar' ? 'الرجاء تسجيل الدخول أولاً' : 'Please login first');
        window.location.href = '/login';
        return;
    }

    // Get data from global property object (set in displayProperty)
    const data = window.currentPropertyData;

    if (!data || !data.propertyId || !data.agentId) {
        console.error('Property data not available:', data);
        alert(lang === 'ar' ? 'خطأ في تحميل البيانات' : 'Error loading property data');
        return;
    }

    console.log('Booking appointment for property:', data);

    // ✅ Store property data in localStorage before navigating
    localStorage.setItem('currentProperty', JSON.stringify({
        propertyId: data.propertyId,
        agentId: data.agentId,
        propertyTitle: data.propertyTitle,
        agentName: data.agentName
    }));

    console.log('Property data stored in localStorage:', data);

    // Navigate to appointment booking page with dynamic IDs
    window.location.href = `/appointment/book?id=${data.propertyId}&agent_id=${data.agentId}`;

}