from django.core.management.base import BaseCommand
from laundry.models import Building, Machine

class Command(BaseCommand):
    help = "Seed initial buildings and machines"

    seed_config = {
        'A': {'washers': 3, 'dryers': 2},
        'B': {'washers': 4, 'dryers': 3},
        'C': {'washers': 2, 'dryers': 1},
        'D': {'washers': 5, 'dryers': 4},
        'E': {'washers': 3, 'dryers': 3},
    }

    def handle(self, *args, **options):
        for name, counts in self.seed_config.items():
            bldg, _ = Building.objects.get_or_create(name=name)
            for i in range(1, counts['washers'] + 1):
                Machine.objects.create(building=bldg, name=f"W{i}", machine_type='washer')
            for i in range(1, counts['dryers'] + 1):
                Machine.objects.create(building=bldg, name=f"D{i}", machine_type='dryer')
        self.stdout.write(self.style.SUCCESS("Seeding completed."))