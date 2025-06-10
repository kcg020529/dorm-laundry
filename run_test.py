import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # settings 경로에 맞게 수정
django.setup()


from laundry.models import Machine

for m in Machine.objects.all():
    print(m.name)