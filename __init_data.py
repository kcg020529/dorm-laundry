import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from laundry.models import Building, Machine

# 동별 세탁기/건조기 수 정의
buildings = {
    "A동": {"washer": 10, "dryer": 7},
    "B동": {"washer": 9, "dryer": 6},
    "C동": {"washer": 14, "dryer": 8},
    "D동": {"washer": 10, "dryer": 10},
    "E동": {"washer": 10, "dryer": 10},
}

for name, machine_counts in buildings.items():
    building, created = Building.objects.get_or_create(name=name)
    if created:
        print(f"건물 추가됨: {name}")
    else:
        print(f"기존 건물: {name}")

    for machine_type, count in machine_counts.items():
        # 이미 있는 기계 수 확인
        existing = Machine.objects.filter(building=building, machine_type=machine_type).count()
        to_create = count - existing

        for i in range(existing + 1, existing + to_create + 1):
            Machine.objects.create(
                name=f"{name} {machine_type.upper()}{i}",
                building=building,
                machine_type=machine_type
            )
        print(f"  > {machine_type} {to_create}대 추가 완료 (총 {count}대 예상)")