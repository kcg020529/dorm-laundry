from django.core.management.base import BaseCommand
from DL.laundry.models import Building, WashingMachine

class Command(BaseCommand):
    help = '건물 및 세탁기 초기 데이터 삽입'

    def handle(self, *args, **kwargs):
        buildings = ['A', 'B', 'C', 'D', 'E']
        for b in buildings:
            building, _ = Building.objects.get_or_create(name=b)
            for i in range(1, 4):  # 각 동마다 3대씩
                WashingMachine.objects.get_or_create(
                    building=building,
                    name=f'{b}{i}'
                )
        self.stdout.write(self.style.SUCCESS('초기 데이터 삽입 완료'))