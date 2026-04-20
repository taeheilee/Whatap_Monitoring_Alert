#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whatap 모니터링 알림 시스템 메인 스크립트
1분마다 실행되어 이벤트를 확인하고 메일을 발송합니다.
"""

import sys
from datetime import datetime
from getwhatapevent import get_whatap_events
from ncpmailsend import send_mail


def main():
    """
    메인 실행 함수
    """
    print(f"\n{'='*60}")
    print(f"Whatap 모니터링 알림 시스템 실행")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 1. Whatap API에서 이벤트 조회
    events = get_whatap_events()
    
    if not events:
        print("발송할 이벤트가 없습니다.\n")
        return 0
    
    # 2. 각 이벤트에 대해 메일 발송
    success_count = 0
    fail_count = 0
    
    for i, event in enumerate(events, 1):
        print(f"\n[{i}/{len(events)}] 이벤트 처리 중...")
        print(f"  - 서버: {event.get('oname', 'N/A')}")
        print(f"  - 레벨: {event.get('level', 'N/A')}")
        print(f"  - 제목: {event.get('title', 'N/A')}")
        
        if send_mail(event):
            success_count += 1
        else:
            fail_count += 1
    
    # 3. 결과 출력
    print(f"\n{'='*60}")
    print(f"처리 완료")
    print(f"  - 총 이벤트: {len(events)}개")
    print(f"  - 발송 성공: {success_count}개")
    print(f"  - 발송 실패: {fail_count}개")
    print(f"{'='*60}\n")
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

