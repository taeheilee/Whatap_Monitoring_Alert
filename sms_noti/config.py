# -*- coding: utf-8 -*-
"""
Whatap 모니터링 알림 시스템 설정 파일
"""

# NCP Cloud Outbound Mailer 설정
NCP_ACCESS_KEY = ""
NCP_SECRET_KEY = ""
NCP_MAIL_API_URL = ""

# WhatAp API 설정
WHATAP_API_URL = ""
WHATAP_TOKEN = ""
WHATAP_PROJECT_CODE = ""

# 메일 설정
SENDER_EMAIL = ""
RECIPIENT_EMAILS = [
    {"address": "test@test.com", "name": "관리자"}
]

# 시간 설정 (분 단위)
CHECK_INTERVAL_MINUTES = 1

