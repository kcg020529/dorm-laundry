# laundry/task.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Reservation, Machine, WaitList, PushSubscription
from django.conf import settings
import json
from pywebpush import webpush, WebPushException
'''
@shared_task
def start_reservation_task(reservation_id):
    """
    예약 시작 시각에 호출되어 기기 사용 상태를 True로 전환합니다.
    """
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        machine = reservation.machine
        machine.is_in_use = True
        machine.save()
    except Reservation.DoesNotExist:
        pass

@shared_task
def end_reservation_task(reservation_id):
    """
    예약 종료 시각에 호출되어 예약 삭제, 기기 사용 상태 False, 대기열 승격을 처리합니다.
    """
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        machine = reservation.machine
        reservation.delete()
        machine.is_in_use = False
        machine.save()
    except Reservation.DoesNotExist:
        return

    # 대기열에서 다음 사용자 자동 승격
    next_wait = WaitList.objects.filter(machine=machine).order_by('created_at').first()
    if next_wait:
        start = timezone.now()
        end = start + timedelta(hours=1)
        new_res = Reservation.objects.create(
            user=next_wait.user,
            machine=machine,
            start_time=start,
            end_time=end
        )
        next_wait.delete()
        # 기기 상태 토글 스케줄
        start_reservation_task.apply_async(args=[new_res.id], eta=start)
        end_reservation_task.apply_async(args=[new_res.id], eta=end)
        # 푸시 알림 스케줄
        for label, offset in [('10분 전', timedelta(minutes=10)), ('시작 시각', timedelta())]:
            eta = start - offset
            if timezone.is_naive(eta):
                eta = timezone.make_aware(eta, timezone.get_current_timezone())
            send_reservation_reminder.apply_async(args=[new_res.id, label], eta=eta)

@shared_task
def send_reservation_reminder(reservation_id, label):
    """
    reservation_id에 해당하는 예약 정보를 조회하여
    label(예: '10분 전', '시작 시각') 웹푸시 알림을 전송합니다.
    """
    try:
        res = Reservation.objects.select_related('user', 'machine').get(id=reservation_id)
    except Reservation.DoesNotExist:
        return

    subs = PushSubscription.objects.filter(user=res.user)
    if not subs.exists():
        return

    payload = {
        "title": "예약 알림",
        "body": f"{res.machine.building}동 {res.machine.name} {label}",
        "url": settings.SITE_URL + "/laundry/"
    }

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh_key, "auth": sub.auth_key}
                },
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_CLAIMS_SUB}
            )
        except WebPushException:
            sub.delete()
            continue
'''