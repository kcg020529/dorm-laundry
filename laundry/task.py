from celery import shared_task
from django.core.mail import send_mail
from .models import Reservation

@shared_task
def send_reservation_reminder.apply_async(
    args=[reservation.id],
    eta=reservation.start_time - timedelta(minutes=10)
)
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        user = reservation.user
        # 가정: 이메일은 학번+@school.edu 같은 구조
        email = f"{user.student_id}@school.edu"

        send_mail(
            subject='[세탁기 예약 알림]',
            message=f"{reservation.start_time.strftime('%H:%M')}에 예약하신 세탁기 이용 시간이 10분 남았습니다.",
            from_email='your_email@gmail.com',
            recipient_list=[email]
        )
        return f"알림 전송 완료: {email}"
    except Exception as e:
        return str(e)
