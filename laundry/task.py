from celery import shared_task
from .models import Reservation, PushSubscription, Machine, WaitList
from django.conf import settings
from pywebpush import webpush, WebPushException
from django.utils import timezone
from datetime import timedelta
import json

@shared_task
def start_reservation_task(reservation_id):
    """
    예약 시작 시각에 호출되어 기기 사용 상태를 True로 전환합니다.
    """
    reservation = Reservation.objects.get(id=reservation_id)
    machine = reservation.machine
    machine.is_in_use = True
    machine.save()

@shared_task
def end_reservation_task(reservation_id):
    """
    예약 종료 시각에 호출되어 예약 삭제, 기기 사용 상태 False, 대기열 승격을 처리합니다.
    """
    reservation = Reservation.objects.get(id=reservation_id)
    machine = reservation.machine
    reservation.delete()
    machine.is_in_use = False
    machine.save()

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
def send_reservation_reminder(reservation_id, when):
    try:
        reservation = Reservation.objects.get(id=reservation_id)

        # 메시지 분기
        if when == '10분 전':
            body = f"{reservation.start_time.strftime('%H:%M')}에 예약하신 세탁기 이용 시간이 10분 남았습니다."
        else:
            body = "지금 예약하신 세탁기를 이용할 시간입니다."

        payload = {
            "title": "[세탁기 예약 알림]",
            "body": body,
            "url": "/mypage/reservations/"
        }

        subs = PushSubscription.objects.filter(user=reservation.user)
        if not subs.exists():
            return "구독 정보 없음, 푸시 스킵"

        vapid_kwargs = {
            "vapid_private_key": settings.WEBPUSH_SETTINGS["VAPID_PRIVATE_KEY"],
            "vapid_claims": settings.WEBPUSH_SETTINGS["VAPID_CLAIMS"],
        }
        for sub in subs:
            try:
                webpush(
                    subscription_info=sub.subscription_info,
                    data=json.dumps(payload),
                    **vapid_kwargs
                )
            except WebPushException:
                sub.delete()

        return "푸시 알림 전송 완료"

    except Reservation.DoesNotExist:
        return "해당 예약이 없습니다."
    except Exception as e:
        return str(e)