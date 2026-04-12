# DEBUG LOGIN STAFF

## Problem:
Login bằng tab [Nhân viên] nhưng không vào được /manage/appointments/

## Checklist:

### 1. USER INFO ✅
- Username: `letan01`
- is_staff: True ✅
- is_active: True ✅

### 2. TEMPLATE ✅
- Staff form exists: ✅
- Hidden input `role="staff"`: ✅
- Input `name="username"`: ✅
- Input `name="password"`: ✅

### 3. VIEW (appointments/views.py:229-235) ✅
```python
@login_required(login_url='accounts:login')
def admin_appointments(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('pages:home')
    return render(request, 'manage/pages/admin_appointments.html')
```

### 4. URL (appointments/urls.py:29) ✅
```python
path('manage/appointments/', views.admin_appointments, name='admin_appointments'),
```

## Test Steps:

1. **Chạy server:**
   ```bash
   python manage.py runserver
   ```

2. **Mở browser:**
   ```
   http://localhost:8000/login/
   ```

3. **Test login:**
   - Click tab: [Nhân viên]
   - Username: `letan01`
   - Password: `letan123`
   - Click [Đăng nhập]

4. **Expected result:**
   - Redirect về: `http://localhost:8000/manage/appointments/`
   - Show page: Quản lý lịch hẹn

5. **If NOT working:**
   - Check browser console (F12) for JavaScript errors
   - Check Django console for error messages
   - Check if `remember_me` checkbox causing issues

## Possible Issues:

### Issue 1: JavaScript not switching forms
**Symptom:** Staff form not showing when clicking [Nhân viên]
**Fix:** Check if `switchRole()` function exists

### Issue 2: Form submitting wrong data
**Symptom:** Role parameter not sent
**Fix:** Check hidden input value

### Issue 3: Redirect loop
**Symptom:** Keep redirecting back to login
**Fix:** Check session expiry

### Issue 4: Permission denied
**Symptom:** "Bạn không có quyền truy cập"
**Fix:** Verify is_staff=True

## Debug Commands:

```bash
# Check user in Django shell
python manage.py shell
>>> from django.contrib.auth.models import User
>>> u = User.objects.get(username='letan01')
>>> u.is_staff
True  # Should be True
>>> u.is_active
True  # Should be True
```

## Next Steps:

1. Test with browser DevTools (Network tab) to see form data
2. Add print() statements in login_view to debug
3. Check Django logs for errors
