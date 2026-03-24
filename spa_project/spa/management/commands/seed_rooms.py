"""Seed rooms data"""
from django.core.management.base import BaseCommand
from spa.models import Room


class Command(BaseCommand):
    help = 'Seed rooms data for spa'

    def handle(self, *args, **options):
        rooms_data = [
            {'code': 'P01', 'name': '1', 'capacity': 3},
            {'code': 'P02', 'name': '2', 'capacity': 2},
            {'code': 'P03', 'name': '3', 'capacity': 4},
            {'code': 'P04', 'name': '4', 'capacity': 2},
            {'code': 'P05', 'name': '5', 'capacity': 3},
        ]

        created_count = 0
        for room_data in rooms_data:
            room, created = Room.objects.get_or_create(
                code=room_data['code'],
                defaults={
                    'name': room_data['name'],
                    'capacity': room_data['capacity'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created room: {room.code} - {room.name}'))
            else:
                self.stdout.write(f'Room already exists: {room.code}')

        self.stdout.write(self.style.SUCCESS(f'Seeded {created_count} new rooms'))