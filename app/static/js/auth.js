// app/static/js/auth.js

const API_BASE = '/api';  // works when frontend served from same domain as Flask

// ────────────────────────────────────────────────
// Helper functions
// ────────────────────────────────────────────────

function showError(elementId, message) {
    const errorEl = document.getElementById(elementId);
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }
}

function clearError(elementId) {
    const errorEl = document.getElementById(elementId);
    if (errorEl) {
        errorEl.textContent = '';
        errorEl.classList.add('hidden');
    }
}

function setLoading(buttonId, isLoading, lang = 'ar') {
    const btn = document.getElementById(buttonId);
    if (!btn) return;

    btn.disabled = isLoading;
    const textSpan = btn.querySelector('span:last-child') || btn;

    if (isLoading) {
        btn.classList.add('opacity-75', 'cursor-wait');
        textSpan.innerHTML = lang === 'ar' ? 'جاري المعالجة...' : 'Processing...';
    } else {
        btn.classList.remove('opacity-75', 'cursor-wait');
        textSpan.innerHTML = lang === 'ar'
            ? (buttonId === 'submitBtn' ? 'إنشاء الحساب' : 'تسجيل الدخول')
            : (buttonId === 'submitBtn' ? 'Create Account' : 'Sign In');
    }
}

// ────────────────────────────────────────────────
// Register form
// ────────────────────────────────────────────────

const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearError('errorMessage');

        const lang = document.documentElement.getAttribute('data-lang') || 'ar';
        setLoading('submitBtn', true, lang);

        const formData = new FormData(registerForm);
        const data = {
            name: formData.get('name')?.trim(),
            email: formData.get('email')?.trim().toLowerCase(),
            password: formData.get('password'),
            phone_number: formData.get('phone')?.trim() || undefined,
        };

        // Basic client validation
        if (!data.name || data.name.length < 2) {
            showError('errorMessage', lang === 'ar' ? 'الاسم قصير جداً' : 'Name is too short');
            setLoading('submitBtn', false, lang);
            return;
        }
        if (!data.email || !data.email.includes('@')) {
            showError('errorMessage', lang === 'ar' ? 'بريد إلكتروني غير صالح' : 'Invalid email');
            setLoading('submitBtn', false, lang);
            return;
        }
        if (!data.password || data.password.length < 6) {
            showError('errorMessage', lang === 'ar' ? 'كلمة المرور قصيرة' : 'Password too short');
            setLoading('submitBtn', false, lang);
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            const result = await res.json();

            if (result.success) {
                localStorage.setItem('token', result.token);
                localStorage.setItem('user_name', result.user_name);
                localStorage.setItem('user_id', result.user_id);

                window.location.href = '/login';  // redirect to chat
            } else {
                showError('errorMessage', result.message || (lang === 'ar' ? 'خطأ في التسجيل' : 'Registration error'));
            }
        } catch (err) {
            console.error(err);
            showError('errorMessage', lang === 'ar' ? 'فشل الاتصال بالخادم' : 'Failed to connect');
        } finally {
            setLoading('submitBtn', false, lang);
        }
    });
}

// ────────────────────────────────────────────────
// Login form
// ────────────────────────────────────────────────

const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearError('errorMessage');

        const lang = document.documentElement.getAttribute('data-lang') || 'ar';
        setLoading('submitBtn', true, lang);

        const formData = new FormData(loginForm);
        const data = {
            email: formData.get('email')?.trim().toLowerCase(),
            password: formData.get('password'),
        };

        if (!data.email || !data.password) {
            showError('errorMessage', lang === 'ar' ? 'جميع الحقول مطلوبة' : 'All fields required');
            setLoading('submitBtn', false, lang);
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            const result = await res.json();

            if (result.success) {
                localStorage.setItem('token', result.token);
                localStorage.setItem('user_name', result.user_name);
                localStorage.setItem('user_id', result.user_id);

                window.location.href = '/chat';  // redirect to chat
            } else {
                showError('errorMessage', result.message || (lang === 'ar' ? 'بيانات خاطئة' : 'Invalid credentials'));
            }
        } catch (err) {
            console.error(err);
            showError('errorMessage', lang === 'ar' ? 'فشل الاتصال' : 'Connection failed');
        } finally {
            setLoading('submitBtn', false, lang);
        }
    });
}

// ────────────────────────────────────────────────
// Forgot Password form
// ────────────────────────────────────────────────

const forgotPasswordForm = document.getElementById('forgotPasswordForm');
if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearError('errorMessage');

        const lang = document.documentElement.getAttribute('data-lang') || 'ar';
        const email = document.getElementById('email').value.trim().toLowerCase();

        if (!email || !email.includes('@')) {
            showError('errorMessage', lang === 'ar' ? 'بريد إلكتروني غير صالح' : 'Invalid email');
            return;
        }

        const btn = document.getElementById('submitBtn');
        btn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/auth/forgot-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });

            const result = await res.json();

            if (result.success) {
                // Store email in sessionStorage and redirect
                sessionStorage.setItem('reset_email', result.email);
                window.location.href = '/reset-password';
            } else {
                showError('errorMessage', result.message || (lang === 'ar' ? 'البريد الإلكتروني غير موجود' : 'Email not found'));
            }
        } catch (err) {
            showError('errorMessage', lang === 'ar' ? 'فشل الاتصال' : 'Connection failed');
        } finally {
            btn.disabled = false;
        }
    });
}

// ────────────────────────────────────────────────
// Reset Password form
// ────────────────────────────────────────────────

const resetPasswordForm = document.getElementById('resetPasswordForm');
if (resetPasswordForm) {
    const lang = document.documentElement.getAttribute('data-lang') || 'ar';

    // Get email from sessionStorage
    const resetEmail = sessionStorage.getItem('reset_email');
    if (!resetEmail) {
        window.location.href = '/forgot-password';
    } else {
        document.getElementById('resetEmail').value = resetEmail;
    }

    resetPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearError('errorMessage');

        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (!newPassword || newPassword.length < 6) {
            showError('errorMessage', lang === 'ar' ? 'كلمة المرور قصيرة جداً (6 أحرف على الأقل)' : 'Password too short (min 6 characters)');
            return;
        }

        if (newPassword !== confirmPassword) {
            showError('errorMessage', lang === 'ar' ? 'كلمتا المرور غير متطابقتين' : 'Passwords do not match');
            return;
        }

        const btn = document.getElementById('submitBtn');
        btn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/auth/reset-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: resetEmail, new_password: newPassword })
            });

            const result = await res.json();

            if (result.success) {
                sessionStorage.removeItem('reset_email');
                const successEl = document.getElementById('successMessage');
                successEl.textContent = lang === 'ar' ? 'تم تغيير كلمة المرور بنجاح، جاري التحويل...' : 'Password reset successfully, redirecting...';
                successEl.classList.remove('hidden');
                setTimeout(() => window.location.href = '/login', 2000);
            } else {
                showError('errorMessage', result.message || (lang === 'ar' ? 'حدث خطأ' : 'An error occurred'));
            }
        } catch (err) {
            showError('errorMessage', lang === 'ar' ? 'فشل الاتصال' : 'Connection failed');
        } finally {
            btn.disabled = false;
        }
    });
}