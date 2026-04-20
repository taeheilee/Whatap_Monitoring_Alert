#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whatap API 이벤트 조회 스크립트
최근 1분간의 이벤트를 조회하여 반환합니다.
"""

import requests
import json
import time
from datetime import datetime
from config import WHATAP_API_URL, WHATAP_TOKEN, WHATAP_PROJECT_CODE


def get_whatap_events():
    """
    Whatap API를 호출하여 최근 1분간의 이벤트를 조회합니다.
    
    Returns:
        list: 이벤트 리스트
    """
    # 현재 시간과 1분 전 시간을 밀리초 단위로 계산
    end_time = int(time.time() * 1000)
    start_time = end_time - (60 * 1000)
    
    # API 엔드포인트 구성
    url = f"{WHATAP_API_URL}?stime={start_time}&etime={end_time}"
    
    # 헤더 설정
    headers = {
        "Content-Type": "application/json",
        "x-whatap-token": WHATAP_TOKEN,
        "x-whatap-pcode": WHATAP_PROJECT_CODE
    }
    
    try:
        # API 호출
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # JSON 파싱
        events = response.json()
        
        # 문자열로 반환된 경우 다시 파싱
        if isinstance(events, str):
            events = json.loads(events)
        
        # 리스트가 아닌 경우 빈 리스트 반환
        if not isinstance(events, list):
            return []
        
        if events:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {len(events)}개의 이벤트를 조회했습니다.")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 조회된 이벤트가 없습니다.")
        
        return events
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Whatap API 호출 중 오류 발생: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 파싱 중 오류 발생: {e}")
        return []


if __name__ == "__main__":
    events = get_whatap_events()
    if events:
        print(json.dumps(events, indent=2, ensure_ascii=False))

