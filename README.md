# Whatap_Monitoring_Alert

설명: Whatap API를 통해 이벤트 기록 수집 후 NCP 아웃바운드 메일러를 통해 메일 발송 

필요 모듈: python rquests 

1. config.py 수정 [accesskey, secrtekey, 발송 이메일, 수신이메일 등]
  - 발송 이메일 spf 레코드 등록 필요

3. crontab 수정 
* * * * * python3 /root/sms_noti/main.py >> /root/sms_noti/logs/send_mail_$(date +\%Y\%m\%d).log 2>&1
  - 1분 마다 python 실행, 실행 출력 결과 로그 저장

0 0 * * * find /root/sms_noti/logs/ -type f -mtime +15 -exec rm {} \;
  - 15일 이상 된 로그파일은 삭제

20260620 발송 가능한 모니터링 항목
sms_noti - CPU, Memory, inode, disk, process, port, reboot, network i/o, disk i/o, system load average
url_noti - url 상태코드이상, 접속 지연 
