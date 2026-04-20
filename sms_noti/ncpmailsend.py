#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NCP Cloud Outbound Mailer 메일 발송 스크립트
Whatap 이벤트 정보를 HTML 형식의 메일로 발송합니다.
"""

import requests
import json
import hmac
import hashlib
import base64
import time
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

    # System Load Average 이벤트 여부 확인
    title = event.get('title', '')
    is_load_average_event = 'System Load Average' in title

    # metricValue 파싱 (System Load Average 이벤트인 경우)
    load_avg_data = {}
    if is_load_average_event:
        metric_value = event.get('message', '')
        # [sum=1.94,count=12,min=0.1,max=0.22,last=0.21] 형식 파싱
        if metric_value:
            import re
            matches = re.findall(r'(\w+)=([\d.]+)', metric_value)
            load_avg_data = {key: float(value) for key, value in matches}

            # PER 계산 (sum/count)*100 - 퍼센테이지로 표시
            if 'sum' in load_avg_data and 'count' in load_avg_data and load_avg_data['count'] > 0:
                load_avg_data['per'] = (load_avg_data['sum'] / load_avg_data['count']) * 100

    # 스냅샷 데이터 파싱 (System Load Average 이벤트가 아닌 경우에만)
    snapshot_str = event.get('snapshot', '{}')
    
    # 스냅샷 데이터 파싱
    snapshot_str = event.get('snapshot', '{}')
    try:
        snapshot = json.loads(snapshot_str)
    except:
        snapshot = {}
    
    # CPU 정보
    cpu_info = snapshot.get('cpu', {})
    cpu_usage = cpu_info.get('cpu', 0)
    cpu_user = cpu_info.get('usr', 0)
    cpu_system = cpu_info.get('sys', 0)
    
    # 메모리 정보
    memory_info = snapshot.get('memory', {})
    memory_used_percent = memory_info.get('pused', 0)
    memory_used_gb = memory_info.get('used', 0) / (1024**3)
    memory_free_gb = memory_info.get('free', 0) / (1024**3)
    memory_cached_gb = memory_info.get('cached', 0) / (1024**3)
    memory_total_gb = memory_info.get('total', 0) / (1024**3)
    memory_pagefaults = memory_info.get('pagefaults', 0)
    
    # Swap 정보
    swap_used_percent = memory_info.get('swappused', 0)
    
    # 디스크 정보
    disk_info = snapshot.get('disk', {})
    
    # 네트워크 정보
    network_info = snapshot.get('network', {})
    
    # 로그 정보 (없을 수 있음)
    log_info = snapshot.get('log', {})
    has_log_info = bool(log_info)
    log_source = log_info.get('source', '')
    log_keyword = log_info.get('keyword', '')
    log_content = log_info.get('content', '')
    
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
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin-bottom: 20px;
            }}
            .metric-card {{
                background-color: #f8f9fa;
                padding: 16px;
                border-radius: 6px;
                text-align: center;
            }}
            .metric-label {{
                font-size: 12px;
                color: #666;
                margin-bottom: 4px;
            }}
            .metric-value {{
                font-size: 20px;
                font-weight: 600;
                color: #333;
            }}
            .metric-unit {{
                font-size: 14px;
                color: #666;
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
                grid-template-columns: repeat(3, 1fr);
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
            .log-content {{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 12px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                color: #495057;
                overflow-x: auto;
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 서버 모니터링 알림</h1>
                <div class="level-badge">{level}</div>
            </div>
            
            <div class="content">
                <div class="info-section">
                    <div class="info-title">📋 이벤트 제목</div>
                    <div class="info-value">{event.get('title', 'N/A')}</div>
                </div>
                
                <div class="info-section">
                    <div class="detail-row">
                        <div class="detail-label">서버명</div>
                        <div class="detail-value">{event.get('oname', 'N/A')}</div>
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
                        <div class="detail-label">프로젝트</div>
                        <div class="detail-value">{event.get('product', 'N/A').upper()}</div>
                    </div>
                </div>
{f'''
                <div class="info-section">
                    <div class="info-title">📊 System Load Average 정보</div>
                    
                    <!-- Load Average 요약 -->
                    <div class="server-stats-group">
                        <div class="stats-header">현재 System Load Average (5m)</div>
                        <div style="text-align: center; padding: 16px; background-color: white; border-radius: 4px; margin-top: 8px;">
                            <div style="font-size: 32px; font-weight: 700; color: {level_color};">
                                {load_avg_data.get('per', 0):.2f}%
                            </div>
                            <div style="font-size: 12px; color: #6c757d; margin-top: 4px;">
                                임계값: {float(event.get('metricThreshold', 0)) * 100:.2f}%
                            </div>
                        </div>
                    </div>
                    
                    <!-- Load Average 상세 정보 -->
                    <div class="server-stats-group">
                        <div class="stats-header">상세 메트릭</div>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-label">Sum</span>
                                <span class="stat-value">{load_avg_data.get('sum', 0):.2f}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Count</span>
                                <span class="stat-value">{load_avg_data.get('count', 0):.0f}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Min</span>
                                <span class="stat-value">{load_avg_data.get('min', 0):.2f}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Max</span>
                                <span class="stat-value">{load_avg_data.get('max', 0):.2f}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Last</span>
                                <span class="stat-value">{load_avg_data.get('last', 0):.2f}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Average</span>
                                <span class="stat-value">{load_avg_data.get('sum', 0) / load_avg_data.get('count', 1) if load_avg_data.get('count', 0) > 0 else 0:.2f}</span>
                            </div>
                        </div>
                    </div>
                </div>
                ''' if is_load_average_event else f'''
                <div class="info-section">
                    <div class="info-title">📊 서버 상태</div>
                    
                    <!-- CPU 정보 -->
                    <div class="server-stats-group">
                        <div class="stats-header">CPU</div>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-label">사용률</span>
                                <span class="stat-value">{cpu_usage:.2f}%</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">User</span>
                                <span class="stat-value">{cpu_user:.2f}%</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">System</span>
                                <span class="stat-value">{cpu_system:.2f}%</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 메모리 정보 -->
                    <div class="server-stats-group">
                        <div class="stats-header">Memory</div>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-label">사용률</span>
                                <span class="stat-value">{memory_used_percent:.2f}%</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Used</span>
                                <span class="stat-value">{memory_used_gb:.2f}GB</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Free</span>
                                <span class="stat-value">{memory_free_gb:.2f}GB</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Cached</span>
                                <span class="stat-value">{memory_cached_gb:.2f}GB</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Pagefaults</span>
                                <span class="stat-value">{memory_pagefaults:.1f}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Swap Used</span>
                                <span class="stat-value">{swap_used_percent:.2f}%</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 디스크 정보 -->
                    {''.join([f'''
                    <div class="server-stats-group">
                        <div class="stats-header">Disk - {mount_point}</div>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-label">사용률</span>
                                <span class="stat-value">{disk_data.get("usedPercent", 0):.2f}%</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Used</span>
                                <span class="stat-value">{disk_data.get("usedSpace", 0) / (1024**3):.2f}GB</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Free</span>
                                <span class="stat-value">{disk_data.get("freeSpace", 0) / (1024**3):.2f}GB</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Total</span>
                                <span class="stat-value">{disk_data.get("totalSpace", 0) / (1024**3):.2f}GB</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">FileSystem</span>
                                <span class="stat-value">{disk_data.get("fileSystem", "N/A")}</span>
                            </div>
                        </div>
                    </div>
                    ''' for mount_point, disk_data in disk_info.items() if disk_data.get("fileSystem", "").lower() != "shm"])}
                    
                    <!-- 네트워크 정보 -->
                    {''.join([f'''
                    <div class="server-stats-group">
                        <div class="stats-header">Network - {net_data.get("desc", "N/A")}</div>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-label">IP</span>
                                <span class="stat-value">{net_data.get("ip", "N/A")}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">MAC Address</span>
                                <span class="stat-value">{hw_addr if hw_addr else "N/A"}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Traffic In</span>
                                <span class="stat-value">{net_data.get("trafficIn", 0) / 1024:.2f}KB/s</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Traffic Out</span>
                                <span class="stat-value">{net_data.get("trafficOut", 0) / 1024:.2f}KB/s</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Packet In</span>
                                <span class="stat-value">{net_data.get("packetIn", 0):.2f}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Packet Out</span>
                                <span class="stat-value">{net_data.get("packetOut", 0):.2f}</span>
                            </div>
                        </div>
                    </div>
                    ''' for hw_addr, net_data in network_info.items()])}
                </div>
                '''}

                {f'''
                <div class="info-section">
                    <div class="info-title">📄 로그 정보</div>
                    <div class="detail-row">
                        <div class="detail-label">파일 경로</div>
                        <div class="detail-value">{log_source}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">키워드</div>
                        <div class="detail-value">{log_keyword}</div>
                    </div>
                    <div style="margin-top: 8px;">
                        <div class="log-content">{log_content}</div>
                    </div>
                </div>
                ''' if has_log_info else ''}
            </div>
            
            <div class="footer">
                <p>이 메일은 Whatap 모니터링 시스템에서 자동으로 발송되었습니다.</p>
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
    
    # 메일 제목 생성
    level = event.get('level', 'Unknown')
    title = f"[{level}] {event.get('oname', 'Unknown Server')} - {event.get('alertType', 'Alert')}"
    
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
        print("사용법: python ncpmailsend.py '<JSON_EVENT>'")

