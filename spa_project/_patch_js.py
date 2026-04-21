content = open('static/js/admin-appointments.js', 'r', encoding='utf-8').read()

start_marker = '// ===== CREATE MODE — GUEST CARDS ====='
end_marker = 'async function openEditModal(id){'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

print(f'start={start_idx}, end={end_idx}')
print('OLD length:', end_idx - start_idx)
print('FIRST 80:', repr(content[start_idx:start_idx+80]))
print('LAST 80:', repr(content[end_idx-80:end_idx]))
