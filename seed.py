"""
Run once to create demo data:  python seed.py
Creates admin user, a normal user, and sample resources.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ssd_booking.settings')
django.setup()

from accounts.models import User
from bookings.models import Resource

def run():
    # Admin user
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@securebook.local',
            password='Admin@1234!',
            first_name='System',
            last_name='Administrator',
        )
        admin.role = User.ROLE_ADMIN
        admin.department = 'IT Department'
        admin.save()
        print('Created admin  | username: admin  | password: Admin@1234!')
    else:
        print('Admin already exists - skipped.')

    # Normal user
    if not User.objects.filter(username='alice').exists():
        user = User.objects.create_user(
            username='alice',
            email='alice@securebook.local',
            password='Alice@1234!',
            first_name='Alice',
            last_name='Smith',
        )
        user.role = User.ROLE_USER
        user.department = 'Engineering'
        user.save()
        print('Created user   | username: alice   | password: Alice@1234!')
    else:
        print('User alice already exists - skipped.')

    # Sample resources
    admin_user = User.objects.filter(username='admin').first()
    resources = [
        {'name': 'Board Room A', 'resource_type': 'room', 'location': 'Level 3', 'capacity': 12},
        {'name': 'Conference Room B', 'resource_type': 'room', 'location': 'Level 2', 'capacity': 8},
        {'name': 'Computer Lab 1', 'resource_type': 'lab', 'location': 'Level 1', 'capacity': 30},
        {'name': 'Training Hall', 'resource_type': 'hall', 'location': 'Ground Floor', 'capacity': 100},
        {'name': 'Projector Unit', 'resource_type': 'equipment', 'location': 'Store Room', 'capacity': 1},
    ]
    for r in resources:
        if not Resource.objects.filter(name=r['name']).exists():
            Resource.objects.create(created_by=admin_user, **r)
            print(f'Created resource: {r["name"]}')

    print('\nDone. Run:  python manage.py runserver')

if __name__ == '__main__':
    run()
