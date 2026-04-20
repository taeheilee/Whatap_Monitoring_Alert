#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NCP Cloud Outbound Mailer 메일 발송 스크립트 (URL 모니터링 전용)
Whatap URL 체크 이벤트 정보를 HTML 형식의 메일로 발송합니다.
"""

import requests
import json
import hmac
import hashlib
import base64
import time
import re
from datetime import datetime
from config import (
    NCP_ACCESS_KEY, NCP_SECRET_KEY, NCP_MAIL_API_URL,
    SENDER_EMAIL, RECIPIENT_EMAILS
)

def create_signature(timestamp, method, url_path):
    """
    NCP API 인증 서명을 생성합니다.
    
    Args:
        timestamp (str): 타임스탬프
        method (str): HTTP 메서드
        url_path (str): API URL 경로
    
    Returns:
        str: Base64 인코딩된 서명
    """
    message = f"{method} {url_path}\n{timestamp}\n{NCP_ACCESS_KEY}"
    message_bytes = message.encode('utf-8')
    secret_bytes = NCP_SECRET_KEY.encode('utf-8')
    
    signature = hmac.new(secret_bytes, message_bytes, hashlib.sha256).digest()
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    return signature_b64

def format_event_time(timestamp_ms):
    """
    밀리초 타임스탬프를 읽기 쉬운 형식으로 변환합니다.
    
    Args:
        timestamp_ms (int): 밀리초 단위 타임스탬프
    
    Returns:
        str: 포맷된 시간 문자열
    """
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def get_level_color(level):
    """
    이벤트 레벨에 따른 색상을 반환합니다.
    
    Args:
        level (str): 이벤트 레벨
    
    Returns:
        str: 색상 코드
    """
    colors = {
        "Critical": "#dc3545",
        "Warning": "#ffc107",
        "Info": "#17a2b8"
    }
    return colors.get(level, "#6c757d")


def extract_url_from_message(message):
    """
    메시지에서 URL을 추출합니다.
    
    Args:
        message (str): 이벤트 메시지
    
    Returns:
        str: 추출된 URL 또는 'N/A'
    """
    # (https://...) 형식에서 URL 추출
    match = re.search(r'\((https?://[^\)]+)\)', message)
    if match:
        return match.group(1)
    return 'N/A'


def create_html_body(event):
    """
    이벤트 정보를 HTML 형식으로 변환합니다.
    
    Args:
        event (dict): 이벤트 정보
    
    Returns:
        str: HTML 형식의 메일 본문
    """
    level = event.get('level', 'Unknown')
    level_color = get_level_color(level)
    event_time = format_event_time(event.get('eventTime', 0))
    
    # 메시지 및 URL 정보
    message = event.get('message', 'N/A')
    url = extract_url_from_message(message)
    
    # 메트릭 정보
    metric_name = event.get('metricName', '')
    metric_value = event.get('metricValue', '0')
    metric_threshold = event.get('metricThreshold', '0')
    
    # 상태 코드 또는 경과 시간에 따른 표시
    is_status_code = metric_name == 'status'
    is_elapsed = metric_name == 'elapsed'
    
    # 숫자에서 쉼표 제거 후 float 변환
    try:
        metric_value_num = float(metric_value.replace(',', ''))
        metric_threshold_num = float(metric_threshold.replace(',', ''))
    except:
        metric_value_num = 0
        metric_threshold_num = 0
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background-color: {level_color};
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .level-badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                background-color: rgba(255,255,255,0.3);
                font-size: 14px;
                margin-top: 8px;
            }}
            .content {{
                padding: 24px;
            }}
            .info-section {{
                margin-bottom: 20px;
            }}
            .info-title {{
                font-size: 14px;
                color: #666;
                margin-bottom: 8px;
                font-weight: 600;
            }}
            .info-value {{
                font-size: 16px;
                color: #333;
                background-color: #f8f9fa;
                padding: 12px;
                border-radius: 4px;
                border-left: 3px solid {level_color};
                word-wrap: break-word;
            }}
            .server-stats-group {{
                background-color: #f8f9fa;
                border-radius: 6px;
                padding: 12px;
                margin-bottom: 10px;
            }}
            .stats-header {{
                font-size: 13px;
                font-weight: 600;
                color: #495057;
                margin-bottom: 8px;
                padding-bottom: 6px;
                border-bottom: 2px solid {level_color};
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
            }}
            .stat-item {{
                display: flex;
                flex-direction: column;
                padding: 6px;
                background-color: white;
                border-radius: 4px;
            }}
            .stat-label {{
                font-size: 10px;
                color: #6c757d;
                margin-bottom: 2px;
            }}
            .stat-value {{
                font-size: 12px;
                font-weight: 600;
                color: #333;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 16px 24px;
                border-top: 1px solid #dee2e6;
                font-size: 12px;
                color: #6c757d;
                text-align: center;
            }}
            .detail-row {{
                display: flex;
                padding: 8px 0;
                border-bottom: 1px solid #f0f0f0;
            }}
            .detail-label {{
                width: 120px;
                font-weight: 600;
                color: #495057;
                font-size: 14px;
            }}
            .detail-value {{
                flex: 1;
                color: #6c757d;
                font-size: 14px;
            }}
            .url-link {{
                color: #007bff;
                text-decoration: none;
                word-break: break-all;
            }}
            .url-link:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 URL 모니터링 알림</h1>
                <div class="level-badge">{level}</div>
            </div>
            
            <div class="content">
                <div class="info-section">
                    <div class="info-title">📋 이벤트 제목</div>
                    <div class="info-value">{event.get('title', 'N/A')}</div>
                </div>
                
                <div class="info-section">
                    <div class="detail-row">
                        <div class="detail-label">URL</div>
                        <div class="detail-value">
                            <a href="{url}" class="url-link" target="_blank">{url}</a>
                        </div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">발생 시간</div>
                        <div class="detail-value">{event_time}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">알림 타입</div>
                        <div class="detail-value">{event.get('alertType', 'N/A')}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">카테고리</div>
                        <div class="detail-value">{event.get('category', 'N/A')}</div>
                    </div>
                </div>
                
                <div class="info-section">
                    <div class="info-title">📊 URL 모니터링 정보</div>
                    
                    <!-- 알림 메시지 -->
                    <div class="server-stats-group">
                        <div class="stats-header">알림 내용</div>
                        <div style="padding: 12px; background-color: white; border-radius: 4px; margin-top: 8px;">
                            <div style="font-size: 14px; color: #333; line-height: 1.6;">
                                {message}
                            </div>
                        </div>
                    </div>
                    
                    <!-- 메트릭 상세 정보 -->
                    <div class="server-stats-group">
                        <div class="stats-header">상세 메트릭</div>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-label">{'상태 코드' if is_status_code else '응답 시간 (ms)' if is_elapsed else '현재 값'}</span>
                                <span class="stat-value" style="font-size: 18px; color: {level_color};">
                                    {metric_value_num:,.0f}{'ms' if is_elapsed else ''}
                                </span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">{'정상 코드' if is_status_code else '임계값 (ms)' if is_elapsed else '기준값'}</span>
                                <span class="stat-value" style="font-size: 18px;">
                                    {metric_threshold_num:,.0f}{'ms' if is_elapsed else ''}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>이 메일은 Whatap URL 모니터링 시스템에서 자동으로 발송되었습니다.</p>
                <p>발송 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def send_mail(event):
    """
    NCP Cloud Outbound Mailer를 통해 메일을 발송합니다.
    
    Args:
        event (dict): Whatap 이벤트 정보
    
    Returns:
        bool: 발송 성공 여부
    """
    # 타임스탬프 생성
    timestamp = str(int(time.time() * 1000))
    
    # URL 경로 추출
    url_path = "/api/v1/mails"
    
    # 서명 생성
    signature = create_signature(timestamp, "POST", url_path)
    
    # 헤더 설정
    headers = {
        "Content-Type": "application/json",
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": NCP_ACCESS_KEY,
        "x-ncp-apigw-signature-v2": signature
    }
    
    # 메시지에서 URL 추출
    message = event.get('message', '')
    url = extract_url_from_message(message)
    
    # 메일 제목 생성
    level = event.get('level', 'Unknown')
    title = f"[{level}] URL 모니터링 - {event.get('title', 'Alert')} ({url})"
    
    # HTML 본문 생성
    html_body = create_html_body(event)
    
    # 수신자 목록 구성
    recipients = [
        {
            "address": recipient["address"],
            "name": recipient["name"],
            "type": "R"
        }
        for recipient in RECIPIENT_EMAILS
    ]
    
    # 요청 데이터 구성
    data = {
        "senderAddress": SENDER_EMAIL,
        "title": title,
        "body": html_body,
        "recipients": recipients,
        "individual": True,
        "advertising": False
    }
    
    try:
        # API 호출
        response = requests.post(
            NCP_MAIL_API_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 메일 발송 성공: {title}")
        print(f"  - Request ID: {result.get('requestId', 'N/A')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 메일 발송 중 오류 발생: {e}")
        if hasattr(e.response, 'text'):
            print(f"  - 응답 내용: {e.response.text}")
        return False
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류 발생: {e}")
        return False


if __name__ == "__main__":
    # 테스트용 샘플 이벤트
    import sys
    
    if len(sys.argv) > 1:
        # 커맨드 라인에서 JSON 이벤트를 받은 경우
        try:
            event = json.loads(sys.argv[1])
            send_mail(event)
        except json.JSONDecodeError:
            print("[ERROR] 잘못된 JSON 형식입니다.")
    else:
        print("사용법: python ncpmailsend_url.py '<JSON_EVENT>'")

