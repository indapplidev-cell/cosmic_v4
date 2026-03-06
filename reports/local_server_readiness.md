# Local Server Readiness Report

Generated at: 2026-03-06 18:06:49 +03:00
Project root: D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4

## Readiness verdict

**Current verdict:** PostgreSQL local URL: OK, DB smoke test: OK, Alembic metadata visibility: OK

## Server module overview

### server/ tree (depth <= 2)
~~~text

FullName                                                                                                              
--------                                                                                                              
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\alembic                                             
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\doc                                                 
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\infra                                               
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models                                              
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\scripts                                             
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\services                                            
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\__pycache__                                         
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\alembic.ini                                         
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\config.py                                           
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\db.py                                               
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\README.md                                           
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\__init__.py                                         
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\alembic\versions                                    
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\alembic\__pycache__                                 
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\alembic\env.py                                      
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\alembic\script.py.mako                              
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\alembic\versions\__pycache__                        
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\alembic\versions\.gitkeep                           
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\alembic\versions\0001_init.py                       
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\alembic\__pycache__\env.cpython-311.pyc             
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\doc\policy_en.md                                    
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\doc\policy_ru.md                                    
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\doc\rule_en.md                                      
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\doc\rule_ru.md                                      
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\infra\docker-compose.yml                            
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models\__pycache__                                  
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models\balance.py                                   
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models\profile_game.py                              
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models\profile_user.py                              
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models\user.py                                      
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models\__init__.py                                  
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models\__pycache__\balance.cpython-311.pyc          
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models\__pycache__\profile_game.cpython-311.pyc     
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models\__pycache__\profile_user.cpython-311.pyc     
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models\__pycache__\user.cpython-311.pyc             
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\models\__pycache__\__init__.cpython-311.pyc         
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\scripts\__pycache__                                 
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\scripts\smoke_auth.py                               
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\scripts\__init__.py                                 
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\scripts\__pycache__\smoke_auth.cpython-311.pyc      
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\scripts\__pycache__\__init__.cpython-311.pyc        
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\services\__pycache__                                
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\services\auth_service.py                            
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\services\profile_service.py                         
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\services\rating_service.py                          
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\services\__init__.py                                
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\services\__pycache__\auth_service.cpython-311.pyc   
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\services\__pycache__\profile_service.cpython-311.pyc
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\services\__pycache__\rating_service.cpython-311.pyc 
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\services\__pycache__\__init__.cpython-311.pyc       
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\__pycache__\config.cpython-311.pyc                  
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\__pycache__\db.cpython-311.pyc                      
D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\server\__pycache__\__init__.cpython-311.pyc                



~~~

### Entrypoints and framework markers
~~~text
Main/app files under server:

FastAPI/Flask markers in server:

~~~

### DB config location (server/config.py)
~~~python
"""EN: Database configuration for the server module.
RU: РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ Р±Р°Р·С‹ РґР°РЅРЅС‹С… РґР»СЏ СЃРµСЂРІРµСЂРЅРѕРіРѕ РјРѕРґСѓР»СЏ.
"""

from __future__ import annotations

import os


DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy"
DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

if not DATABASE_URL.startswith("postgresql"):
    raise RuntimeError(
        "Only PostgreSQL is supported in server/config.py. "
        f"Got DATABASE_URL={DATABASE_URL!r}"
    )


~~~

### Python environment
~~~text
Python 3.11.9

pip 26.0.1 from D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\.venv\Lib\site-packages\pip (python 3.11)


~~~

### Installed packages
~~~text
alembic==1.18.4
asyncgui==0.6.3
asynckivy==0.6.4
certifi==2026.1.4
charset-normalizer==3.4.4
docutils==0.22.4
filetype==1.2.0
greenlet==3.3.2
idna==3.11
kivy_deps.sdl2==0.8.0
Kivy==2.3.1
kivy-deps.angle==0.4.0
kivy-deps.glew==0.3.1
Kivy-Garden==0.1.5
kivymd @ git+https://github.com/kivymd/KivyMD.git@d668d8b2b3d9eb54517892f613ffe34d9914517a
Mako==1.3.10
markdown-it-py==4.0.0
MarkupSafe==3.0.3
materialshapes==0.3
materialyoucolor==3.0.1
mdurl==0.1.2
packaging==26.0
pillow==12.1.0
psycopg==3.3.3
psycopg-binary==3.3.3
pycairo==1.29.0
Pygments==2.19.2
pypiwin32==223
pywin32==311
requests==2.32.5
rich==13.9.4
SQLAlchemy==2.0.48
typing_extensions==4.15.0
tzdata==2025.3
urllib3==2.6.3

~~~

## Host network & OS

### OS
~~~text

OS Name:                   Майкрософт Windows 10 Pro
OS Version:                10.0.19045 N/A Build 19045
System Type:               x64-based PC
BIOS Version:              Dell Inc. A25, 06.03.2018



~~~

### Hostname / DNS
~~~text
Hostname:
Oleg

DNS client settings:

InterfaceAlias               InterfaceIndex AddressFamily ServerAddresses                                       
--------------               -------------- ------------- ---------------                                       
singbox_tun                              20 IPv4          {172.18.0.2}                                          
singbox_tun                              20 IPv6          {}                                                    
Ethernet                                 14 IPv4          {}                                                    
Ethernet                                 14 IPv6          {fec0:0:0:ffff::1, fec0:0:0:ffff::2, fec0:0:0:ffff::3}
vEthernet (Default Switch)               32 IPv4          {}                                                    
vEthernet (Default Switch)               32 IPv6          {fec0:0:0:ffff::1, fec0:0:0:ffff::2, fec0:0:0:ffff::3}
Подключение по локальной...1             16 IPv4          {}                                                    
Подключение по локальной...1             16 IPv6          {fec0:0:0:ffff::1, fec0:0:0:ffff::2, fec0:0:0:ffff::3}
Подключение по локально...10              4 IPv4          {}                                                    
Подключение по локально...10              4 IPv6          {fec0:0:0:ffff::1, fec0:0:0:ffff::2, fec0:0:0:ffff::3}
Беспроводная сеть                        13 IPv4          {192.168.0.1}                                         
Беспроводная сеть                        13 IPv6          {}                                                    
Loopback Pseudo-Interface 1               1 IPv4          {}                                                    
Loopback Pseudo-Interface 1               1 IPv6          {fec0:0:0:ffff::1, fec0:0:0:ffff::2, fec0:0:0:ffff::3}
vEthernet (WSL)                          51 IPv4          {}                                                    
vEthernet (WSL)                          51 IPv6          {fec0:0:0:ffff::1, fec0:0:0:ffff::2, fec0:0:0:ffff::3}



~~~

### IP addresses
~~~text

Windows IP Configuration

   Host Name . . . . . . . . . . . . : Oleg
   Primary Dns Suffix  . . . . . . . : 
   Node Type . . . . . . . . . . . . : Hybrid
   IP Routing Enabled. . . . . . . . : No
   WINS Proxy Enabled. . . . . . . . : No

Unknown adapter singbox_tun:

   Connection-specific DNS Suffix  . : 
   Description . . . . . . . . . . . : sing-tun Tunnel
   Physical Address. . . . . . . . . : 
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes
   Link-local IPv6 Address . . . . . : fe80::a38b:d060:513b:6051%20(Preferred) 
   IPv4 Address. . . . . . . . . . . : 172.18.0.1(Preferred) 
   Subnet Mask . . . . . . . . . . . : 255.255.255.252
   Default Gateway . . . . . . . . . : 172.18.0.2
   DNS Servers . . . . . . . . . . . : 172.18.0.2
   NetBIOS over Tcpip. . . . . . . . : Enabled

Ethernet adapter Ethernet:

   Media State . . . . . . . . . . . : Media disconnected
   Connection-specific DNS Suffix  . : 
   Description . . . . . . . . . . . : Intel(R) 82579LM Gigabit Network Connection
   Physical Address. . . . . . . . . : 5C-26-0A-68-85-A5
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes

Ethernet adapter vEthernet (Default Switch):

   Connection-specific DNS Suffix  . : 
   Description . . . . . . . . . . . : Hyper-V Virtual Ethernet Adapter
   Physical Address. . . . . . . . . : 00-15-5D-B2-8C-BA
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes
   Link-local IPv6 Address . . . . . : fe80::5ec8:1eaf:1095:bff8%32(Preferred) 
   IPv4 Address. . . . . . . . . . . : 172.29.80.1(Preferred) 
   Subnet Mask . . . . . . . . . . . : 255.255.240.0
   Default Gateway . . . . . . . . . : 
   DHCPv6 IAID . . . . . . . . . . . : 536876381
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-2F-B9-3D-62-5C-26-0A-68-85-A5
   DNS Servers . . . . . . . . . . . : fec0:0:0:ffff::1%1
                                       fec0:0:0:ffff::2%1
                                       fec0:0:0:ffff::3%1
   NetBIOS over Tcpip. . . . . . . . : Enabled

Wireless LAN adapter ������祭�� �� �����쭮� ��* 1:

   Media State . . . . . . . . . . . : Media disconnected
   Connection-specific DNS Suffix  . : 
   Description . . . . . . . . . . . : Microsoft Wi-Fi Direct Virtual Adapter
   Physical Address. . . . . . . . . : A0-88-B4-1D-F2-05
   DHCP Enabled. . . . . . . . . . . : Yes
   Autoconfiguration Enabled . . . . : Yes

Wireless LAN adapter ������祭�� �� �����쭮� ��* 10:

   Media State . . . . . . . . . . . : Media disconnected
   Connection-specific DNS Suffix  . : 
   Description . . . . . . . . . . . : Microsoft Wi-Fi Direct Virtual Adapter #2
   Physical Address. . . . . . . . . : A2-88-B4-1D-F2-04
   DHCP Enabled. . . . . . . . . . . : Yes
   Autoconfiguration Enabled . . . . : Yes

Wireless LAN adapter ���஢����� ���:

   Connection-specific DNS Suffix  . : 
   Description . . . . . . . . . . . : Intel(R) Centrino(R) Advanced-N 6205
   Physical Address. . . . . . . . . : A0-88-B4-1D-F2-04
   DHCP Enabled. . . . . . . . . . . : Yes
   Autoconfiguration Enabled . . . . : Yes
   Link-local IPv6 Address . . . . . : fe80::b9a8:470d:3194:3d39%13(Preferred) 
   IPv4 Address. . . . . . . . . . . : 192.168.0.103(Preferred) 
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Lease Obtained. . . . . . . . . . : 4 ���� 2026 �. 14:37:56
   Lease Expires . . . . . . . . . . : 6 ���� 2026 �. 19:37:55
   Default Gateway . . . . . . . . . : 192.168.0.1
   DHCP Server . . . . . . . . . . . : 192.168.0.1
   DHCPv6 IAID . . . . . . . . . . . : 211847348
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-2F-B9-3D-62-5C-26-0A-68-85-A5
   DNS Servers . . . . . . . . . . . : 192.168.0.1
   NetBIOS over Tcpip. . . . . . . . : Enabled

Ethernet adapter vEthernet (WSL):

   Connection-specific DNS Suffix  . : 
   Description . . . . . . . . . . . : Hyper-V Virtual Ethernet Adapter #2
   Physical Address. . . . . . . . . : 00-15-5D-18-08-C0
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes
   Link-local IPv6 Address . . . . . : fe80::9520:9e2:82b9:75aa%51(Preferred) 
   IPv4 Address. . . . . . . . . . . : 172.29.96.1(Preferred) 
   Subnet Mask . . . . . . . . . . . : 255.255.240.0
   Default Gateway . . . . . . . . . : 
   DHCPv6 IAID . . . . . . . . . . . : 855643485
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-2F-B9-3D-62-5C-26-0A-68-85-A5
   DNS Servers . . . . . . . . . . . : fec0:0:0:ffff::1%1
                                       fec0:0:0:ffff::2%1
                                       fec0:0:0:ffff::3%1
   NetBIOS over Tcpip. . . . . . . . : Enabled

~~~

~~~text

ifIndex IPAddress                    PrefixLength PrefixOrigin SuffixOrigin AddressState PolicyStore
------- ---------                    ------------ ------------ ------------ ------------ -----------
51      fe80::9520:9e2:82b9:75aa%51            64 WellKnown    Link         Preferred    ActiveStore
32      fe80::5ec8:1eaf:1095:bff8%32           64 WellKnown    Link         Preferred    ActiveStore
4       fe80::1816:6d2e:7777:8571%4            64 WellKnown    Link         Deprecated   ActiveStore
14      fe80::af10:79ba:c581:b4c7%14           64 WellKnown    Link         Deprecated   ActiveStore
16      fe80::5347:7b25:4619:6806%16           64 WellKnown    Link         Deprecated   ActiveStore
13      fe80::b9a8:470d:3194:3d39%13           64 WellKnown    Link         Preferred    ActiveStore
20      fe80::a38b:d060:513b:6051%20           64 WellKnown    Link         Preferred    ActiveStore
1       ::1                                   128 WellKnown    WellKnown    Preferred    ActiveStore
51      172.29.96.1                            20 Manual       Manual       Preferred    ActiveStore
32      172.29.80.1                            20 Manual       Manual       Preferred    ActiveStore
4       169.254.205.157                        16 WellKnown    Link         Tentative    ActiveStore
14      192.168.1.2                            24 Manual       Manual       Tentative    ActiveStore
14      169.254.33.57                          16 WellKnown    Link         Tentative    ActiveStore
16      169.254.255.25                         16 WellKnown    Link         Tentative    ActiveStore
13      192.168.0.103                          24 Dhcp         Dhcp         Preferred    ActiveStore
20      172.18.0.1                             30 Manual       Manual       Preferred    ActiveStore
1       127.0.0.1                               8 WellKnown    WellKnown    Preferred    ActiveStore



~~~

### Occupied ports (top 200 lines)
~~~text

Active Connections

  Proto  Local Address          Foreign Address        State           PID
  TCP    0.0.0.0:135            0.0.0.0:0              LISTENING       1160
  TCP    0.0.0.0:445            0.0.0.0:0              LISTENING       4
  TCP    0.0.0.0:1947           0.0.0.0:0              LISTENING       5200
  TCP    0.0.0.0:2179           0.0.0.0:0              LISTENING       2660
  TCP    0.0.0.0:3389           0.0.0.0:0              LISTENING       1312
  TCP    0.0.0.0:5040           0.0.0.0:0              LISTENING       7728
  TCP    0.0.0.0:5357           0.0.0.0:0              LISTENING       4
  TCP    0.0.0.0:5432           0.0.0.0:0              LISTENING       18304
  TCP    0.0.0.0:5985           0.0.0.0:0              LISTENING       4
  TCP    0.0.0.0:47001          0.0.0.0:0              LISTENING       4
  TCP    0.0.0.0:49664          0.0.0.0:0              LISTENING       1020
  TCP    0.0.0.0:49665          0.0.0.0:0              LISTENING       888
  TCP    0.0.0.0:49666          0.0.0.0:0              LISTENING       1524
  TCP    0.0.0.0:49667          0.0.0.0:0              LISTENING       2100
  TCP    0.0.0.0:49668          0.0.0.0:0              LISTENING       3044
  TCP    0.0.0.0:49669          0.0.0.0:0              LISTENING       5060
  TCP    0.0.0.0:49670          0.0.0.0:0              LISTENING       968
  TCP    127.0.0.1:8884         0.0.0.0:0              LISTENING       4
  TCP    127.0.0.1:9990         0.0.0.0:0              LISTENING       5420
  TCP    127.0.0.1:10808        0.0.0.0:0              LISTENING       4460
  TCP    127.0.0.1:10808        127.0.0.1:50261        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55173        TIME_WAIT       0
  TCP    127.0.0.1:10808        127.0.0.1:55185        TIME_WAIT       0
  TCP    127.0.0.1:10808        127.0.0.1:55197        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55310        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55358        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55423        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55491        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55548        TIME_WAIT       0
  TCP    127.0.0.1:10808        127.0.0.1:55574        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55588        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55589        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55651        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55654        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55656        TIME_WAIT       0
  TCP    127.0.0.1:10808        127.0.0.1:55657        TIME_WAIT       0
  TCP    127.0.0.1:10808        127.0.0.1:55669        ESTABLISHED     4460
  TCP    127.0.0.1:10808        127.0.0.1:55687        ESTABLISHED     4460
  TCP    127.0.0.1:10814        0.0.0.0:0              LISTENING       6468
  TCP    127.0.0.1:16709        0.0.0.0:0              LISTENING       5688
  TCP    127.0.0.1:50261        127.0.0.1:10808        ESTABLISHED     6668
  TCP    127.0.0.1:50911        0.0.0.0:0              LISTENING       5516
  TCP    127.0.0.1:50912        0.0.0.0:0              LISTENING       5508
  TCP    127.0.0.1:54989        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:54995        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55197        127.0.0.1:10808        ESTABLISHED     3892
  TCP    127.0.0.1:55310        127.0.0.1:10808        ESTABLISHED     6468
  TCP    127.0.0.1:55358        127.0.0.1:10808        ESTABLISHED     3892
  TCP    127.0.0.1:55362        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55423        127.0.0.1:10808        ESTABLISHED     6668
  TCP    127.0.0.1:55491        127.0.0.1:10808        ESTABLISHED     11364
  TCP    127.0.0.1:55497        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55501        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55524        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55574        127.0.0.1:10808        ESTABLISHED     6468
  TCP    127.0.0.1:55588        127.0.0.1:10808        ESTABLISHED     6668
  TCP    127.0.0.1:55589        127.0.0.1:10808        ESTABLISHED     6668
  TCP    127.0.0.1:55616        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55623        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55626        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55629        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55632        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55635        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55647        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55651        127.0.0.1:10808        ESTABLISHED     6468
  TCP    127.0.0.1:55654        127.0.0.1:10808        ESTABLISHED     6668
  TCP    127.0.0.1:55655        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55666        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55669        127.0.0.1:10808        ESTABLISHED     3892
  TCP    127.0.0.1:55672        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55675        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55678        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55681        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55684        127.0.0.1:10808        TIME_WAIT       0
  TCP    127.0.0.1:55687        127.0.0.1:10808        ESTABLISHED     13056
  TCP    127.0.0.1:61934        0.0.0.0:0              LISTENING       13056
  TCP    172.18.0.1:139         0.0.0.0:0              LISTENING       4
  TCP    172.18.0.1:50293       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.18.0.1:55065       185.216.87.26:443      TIME_WAIT       0
  TCP    172.18.0.1:55073       185.216.87.26:443      TIME_WAIT       0
  TCP    172.18.0.1:55181       185.216.87.26:443      TIME_WAIT       0
  TCP    172.18.0.1:55186       185.216.87.26:443      TIME_WAIT       0
  TCP    172.18.0.1:55198       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.18.0.1:55309       172.64.155.209:443     ESTABLISHED     11364
  TCP    172.18.0.1:55311       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.18.0.1:55359       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.18.0.1:55364       185.216.87.26:443      TIME_WAIT       0
  TCP    172.18.0.1:55429       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.18.0.1:55492       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.18.0.1:55575       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.18.0.1:55601       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.18.0.1:55605       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.18.0.1:55650       52.123.240.63:443      ESTABLISHED     5324
  TCP    172.18.0.1:55652       185.216.87.26:443      CLOSE_WAIT      4460
  TCP    172.18.0.1:55662       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.18.0.1:55670       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.18.0.1:55688       185.216.87.26:443      ESTABLISHED     4460
  TCP    172.29.80.1:139        0.0.0.0:0              LISTENING       4
  TCP    172.29.96.1:139        0.0.0.0:0              LISTENING       4
  TCP    192.168.0.103:139      0.0.0.0:0              LISTENING       4
  TCP    192.168.0.103:49675    4.207.247.138:443      ESTABLISHED     5748
  TCP    192.168.0.103:50296    185.216.87.26:443      ESTABLISHED     6468
  TCP    192.168.0.103:54991    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:54997    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55199    185.216.87.26:443      ESTABLISHED     6468
  TCP    192.168.0.103:55312    185.216.87.26:443      ESTABLISHED     6468
  TCP    192.168.0.103:55360    185.216.87.26:443      ESTABLISHED     6468
  TCP    192.168.0.103:55432    185.216.87.26:443      ESTABLISHED     6468
  TCP    192.168.0.103:55493    185.216.87.26:443      ESTABLISHED     6468
  TCP    192.168.0.103:55499    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55505    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55526    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55576    185.216.87.26:443      ESTABLISHED     6468
  TCP    192.168.0.103:55608    185.216.87.26:443      ESTABLISHED     6468
  TCP    192.168.0.103:55609    185.216.87.26:443      ESTABLISHED     6468
  TCP    192.168.0.103:55618    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55625    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55628    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55631    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55634    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55637    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55649    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55653    185.216.87.26:443      LAST_ACK        6468
  TCP    192.168.0.103:55660    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55663    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55664    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55665    185.216.87.26:443      ESTABLISHED     6468
  TCP    192.168.0.103:55668    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55671    185.216.87.26:443      ESTABLISHED     6468
  TCP    192.168.0.103:55674    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55677    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55680    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55683    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55686    185.216.87.26:443      TIME_WAIT       0
  TCP    192.168.0.103:55689    185.216.87.26:443      ESTABLISHED     6468
  TCP    [::]:135               [::]:0                 LISTENING       1160
  TCP    [::]:445               [::]:0                 LISTENING       4
  TCP    [::]:1947              [::]:0                 LISTENING       5200
  TCP    [::]:2179              [::]:0                 LISTENING       2660
  TCP    [::]:3389              [::]:0                 LISTENING       1312
  TCP    [::]:5357              [::]:0                 LISTENING       4
  TCP    [::]:5432              [::]:0                 LISTENING       18304
  TCP    [::]:5985              [::]:0                 LISTENING       4
  TCP    [::]:47001             [::]:0                 LISTENING       4
  TCP    [::]:49664             [::]:0                 LISTENING       1020
  TCP    [::]:49665             [::]:0                 LISTENING       888
  TCP    [::]:49666             [::]:0                 LISTENING       1524
  TCP    [::]:49667             [::]:0                 LISTENING       2100
  TCP    [::]:49668             [::]:0                 LISTENING       3044
  TCP    [::]:49669             [::]:0                 LISTENING       5060
  TCP    [::]:49670             [::]:0                 LISTENING       968
  TCP    [::1]:5432             [::]:0                 LISTENING       12840
  UDP    0.0.0.0:53             *:*                                    3956
  UDP    0.0.0.0:53             *:*                                    3956
  UDP    0.0.0.0:500            *:*                                    5236
  UDP    0.0.0.0:1947           *:*                                    5200
  UDP    0.0.0.0:3389           *:*                                    1312
  UDP    0.0.0.0:3702           *:*                                    3628
  UDP    0.0.0.0:3702           *:*                                    5656
  UDP    0.0.0.0:3702           *:*                                    5656
  UDP    0.0.0.0:3702           *:*                                    3628
  UDP    0.0.0.0:4500           *:*                                    5236
  UDP    0.0.0.0:5050           *:*                                    7728
  UDP    0.0.0.0:5353           *:*                                    11336
  UDP    0.0.0.0:5353           *:*                                    11336
  UDP    0.0.0.0:5353           *:*                                    3544
  UDP    0.0.0.0:5353           *:*                                    3892
  UDP    0.0.0.0:5353           *:*                                    11336
  UDP    0.0.0.0:5353           *:*                                    3892
  UDP    0.0.0.0:5353           *:*                                    3892
  UDP    0.0.0.0:5353           *:*                                    3892
  UDP    0.0.0.0:5353           *:*                                    3892
  UDP    0.0.0.0:5353           *:*                                    3892
  UDP    0.0.0.0:5353           *:*                                    3892
  UDP    0.0.0.0:5353           *:*                                    11336
  UDP    0.0.0.0:5353           *:*                                    11336
  UDP    0.0.0.0:5353           *:*                                    11336
  UDP    0.0.0.0:5353           *:*                                    11336
  UDP    0.0.0.0:5353           *:*                                    3892
  UDP    0.0.0.0:5353           *:*                                    11336
  UDP    0.0.0.0:5355           *:*                                    3544
  UDP    0.0.0.0:49664          *:*                                    3628
  UDP    0.0.0.0:51817          *:*                                    5656
  UDP    0.0.0.0:56972          *:*                                    3956
  UDP    0.0.0.0:62332          *:*                                    3956
  UDP    0.0.0.0:62333          *:*                                    3956
  UDP    127.0.0.1:1900         *:*                                    6532
  UDP    127.0.0.1:10808        *:*                                    4460
  UDP    127.0.0.1:49666        *:*                                    4436
  UDP    127.0.0.1:64171        *:*                                    6532
  UDP    172.18.0.1:137         *:*                                    4
  UDP    172.18.0.1:138         *:*                                    4
  UDP    172.18.0.1:1900        *:*                                    6532
  UDP    172.18.0.1:64168       *:*                                    6532
  UDP    172.29.80.1:67         *:*                                    3956
  UDP    172.29.80.1:68         *:*                                    3956

~~~

### WSL / Linux (if available)
~~~text
    N A M E                             S T A T E                       V E R S I O N 
 
 *   U b u n t u                         R u n n i n g                   2 
 
     d o c k e r - d e s k t o p         R u n n i n g                   2 
 
 

~~~

~~~text
Linux Oleg 6.6.87.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux

~~~

~~~text
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:15:5d:0b:d6:e2 brd ff:ff:ff:ff:ff:ff
    inet 172.29.107.84/20 brd 172.29.111.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::215:5dff:fe0b:d6e2/64 scope link 
       valid_lft forever preferred_lft forever

~~~

~~~text
Netid State  Recv-Q Send-Q Local Address:Port Peer Address:PortProcess
udp   UNCONN 0      0          127.0.0.1:323       0.0.0.0:*          
udp   UNCONN 0      0              [::1]:323          [::]:*          
tcp   LISTEN 0      4096               *:5432            *:*          

~~~

## PostgreSQL readiness

### Docker-based setup
~~~text
Docker version 28.3.2, build 578ccf6

Docker Compose version v2.38.2-desktop.1

~~~

~~~text
NAMES                STATUS       PORTS
cosmic_v4_postgres   Up 4 hours   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp

~~~

~~~text
docker : time="2026-03-06T18:06:42+03:00" level=warning msg="D:\\disk_E\\course_py\\game\\game_galaxy_code_python\\cosm
ic_v4\\server\\infra\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to 
avoid potential confusion"
At D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\reports\collect_local_server_readiness.ps1:83 char:50
+ ... e_config" { docker compose -f server/infra/docker-compose.yml config  ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (time="2026-03-0...tial confusion":String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
name: infra
services:
  postgres:
    container_name: cosmic_v4_postgres
    environment:
      POSTGRES_DB: game_galaxy
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
    image: postgres:16
    networks:
      default: null
    ports:
      - mode: ingress
        target: 5432
        published: "5432"
        protocol: tcp
    restart: unless-stopped
    volumes:
      - type: volume
        source: postgres_data
        target: /var/lib/postgresql/data
        volume: {}
networks:
  default:
    name: infra_default
volumes:
  postgres_data:
    name: infra_postgres_data

~~~

~~~text
The files belonging to this database system will be owned by user "postgres".
This user must also own the server process.

The database cluster will be initialized with locale "en_US.utf8".
The default database encoding has accordingly been set to "UTF8".
The default text search configuration will be set to "english".

Data page checksums are disabled.

fixing permissions on existing directory /var/lib/postgresql/data ... ok
creating subdirectories ... ok
docker : initdb: warning: enabling "trust" authentication for local connections
At D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\reports\collect_local_server_readiness.ps1:88 char:9
+         docker logs $postgresContainer.ToString().Trim() --tail 200
+         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (initdb: warning...cal connections:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
selecting dynamic shared memory implementation ... posix
initdb: hint: You can change this by editing pg_hba.conf or using the option -A, or --auth-local and --auth-host, the n
ext time you run initdb.
selecting default max_connections ... 100
selecting default shared_buffers ... 128MB
selecting default time zone ... Etc/UTC
creating configuration files ... ok
running bootstrap script ... ok
performing post-bootstrap initialization ... ok
syncing data to disk ... ok


Success. You can now start the database server using:

    pg_ctl -D /var/lib/postgresql/data -l logfile start

waiting for server to start....2026-03-06 11:32:33.650 UTC [48] LOG:  starting PostgreSQL 16.10 (Debian 16.10-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
2026-03-06 11:32:33.656 UTC [48] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-06 11:32:33.672 UTC [51] LOG:  database system was shut down at 2026-03-06 11:32:33 UTC
2026-03-06 11:32:33.683 UTC [48] LOG:  database system is ready to accept connections
 done
server started
CREATE DATABASE


/usr/local/bin/docker-entrypoint.sh: ignoring /docker-entrypoint-initdb.d/*

waiting for server to shut down...2026-03-06 11:32:34.064 UTC [48] LOG:  received fast shutdown request
.2026-03-06 11:32:34.074 UTC [48] LOG:  aborting any active transactions
2026-03-06 11:32:34.077 UTC [48] LOG:  background worker "logical replication launcher" (PID 54) exited with exit code 1
2026-03-06 11:32:34.078 UTC [49] LOG:  shutting down
2026-03-06 11:32:34.084 UTC [49] LOG:  checkpoint starting: shutdown immediate
2026-03-06 11:32:34.264 UTC [49] LOG:  checkpoint complete: wrote 926 buffers (5.7%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.050 s, sync=0.116 s, total=0.186 s; sync files=301, longest=0.032 s, average=0.001 s; distance=4273 kB, estimate=4273 kB; lsn=0/191F0E0, redo lsn=0/191F0E0
2026-03-06 11:32:34.276 UTC [48] LOG:  database system is shut down
 done
server stopped

PostgreSQL init process complete; ready for start up.

2026-03-06 11:32:34.411 UTC [1] LOG:  starting PostgreSQL 16.10 (Debian 16.10-1.pgdg13+1) on x86_64-pc-linux-gnu, compi
led by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
2026-03-06 11:32:34.412 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-03-06 11:32:34.412 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-03-06 11:32:34.421 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-06 11:32:34.432 UTC [64] LOG:  database system was shut down at 2026-03-06 11:32:34 UTC
2026-03-06 11:32:34.443 UTC [1] LOG:  database system is ready to accept connections
2026-03-06 11:37:34.502 UTC [62] LOG:  checkpoint starting: time
2026-03-06 11:37:46.440 UTC [62] LOG:  checkpoint complete: wrote 121 buffers (0.7%); 0 WAL file(s) added, 0 removed, 0
 recycled; write=11.880 s, sync=0.027 s, total=11.938 s; sync files=76, longest=0.008 s, average=0.001 s; distance=549 
kB, estimate=549 kB; lsn=0/19A88D0, redo lsn=0/19A8898
2026-03-06 11:57:34.589 UTC [62] LOG:  checkpoint starting: time
2026-03-06 11:57:37.646 UTC [62] LOG:  checkpoint complete: wrote 31 buffers (0.2%); 0 WAL file(s) added, 0 removed, 0 
recycled; write=3.015 s, sync=0.013 s, total=3.057 s; sync files=21, longest=0.006 s, average=0.001 s; distance=4 kB, e
stimate=495 kB; lsn=0/19A99A0, redo lsn=0/19A9968
2026-03-06 12:02:34.726 UTC [62] LOG:  checkpoint starting: time
2026-03-06 12:02:35.176 UTC [62] LOG:  checkpoint complete: wrote 5 buffers (0.0%); 0 WAL file(s) added, 0 removed, 0 r
ecycled; write=0.407 s, sync=0.012 s, total=0.450 s; sync files=5, longest=0.009 s, average=0.003 s; distance=0 kB, est
imate=445 kB; lsn=0/19A9D80, redo lsn=0/19A9D48

~~~

### Service-based setup (psql)
~~~text
ERROR: The term 'psql' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.

~~~

## DB connection test

### DATABASE_URL resolution
~~~text
postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy
Local PostgreSQL URL check: OK

~~~

### Alembic
~~~text
python.exe : INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
At D:\disk_E\course_py\game\game_galaxy_code_python\cosmic_v4\reports\collect_local_server_readiness.ps1:122 char:40
+ ... ic_current" { & $pythonExe -m alembic -c server/alembic.ini current }
+                   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (INFO  [alembic....PostgresqlImpl.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
INFO  [alembic.runtime.migration] Will assume transactional DDL.
0001_init (head)

~~~

~~~text
0001_init (head)

~~~

~~~text
Skipped intentionally to avoid destructive risk on non-empty/non-test DB in readiness scan.

~~~

### SQLAlchemy smoke (eports/tmp_db_smoke.py)
~~~text
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy
SELECT 1 -> 1
Tables:
  - alembic_version
  - users
  - profile_users
  - profile_games
  - balances

~~~

## Security baseline

### Soft secrets scan
~~~text
.\server\config.py:10:DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy"
.\server\README.md:22:set DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy
.\server\README.md:28:$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy"
.\server\README.md:34:postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy

~~~

### Server env markers
~~~text
server\infra\docker-compose.yml:9:      POSTGRES_USER: postgres
server\infra\docker-compose.yml:10:      POSTGRES_PASSWORD: postgres
server\infra\docker-compose.yml:11:      POSTGRES_DB: game_galaxy
server\config.py:10:DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy"
server\config.py:11:DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
server\config.py:13:if not DATABASE_URL.startswith("postgresql"):
server\config.py:16:        f"Got DATABASE_URL={DATABASE_URL!r}"
server\db.py:13:from server.config import DATABASE_URL
server\db.py:17:    DATABASE_URL,
server\alembic\env.py:12:from server.config import DATABASE_URL
server\alembic\env.py:21:config.set_main_option("sqlalchemy.url", DATABASE_URL)
server\README.md:17:## 3) Configure DATABASE_URL
server\README.md:22:set DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy
server\README.md:28:$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/game_galaxy"
server\README.md:31:If `DATABASE_URL` is not set, the server module uses:
server\README.md:52:python -c "from sqlalchemy import create_engine, text; from server.config import DATABASE_URL; e=create_engine(DATABASE_URL); print(e.connect().execute(text('select 1')).scalar())"

~~~

### Notes
- Reverse proxy (nginx) and TLS are not required for local-only tests, but are required before external access.
- Keep DATABASE_URL in environment or secret manager for production-like deployment.

## Expected load & bottlenecks

### Database size / version (if psql available)
~~~text
ERROR: The term 'psql' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.

~~~

~~~text
ERROR: The term 'psql' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.

~~~

~~~text
ERROR: The term 'psql' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.

~~~

### Index and query hints from code
~~~text
server/models\balance.py:27:        index=True,
server/services\auth_service.py:16:def register_user(email: str, psw: str) -> dict:
server/services\auth_service.py:20:    email_value = (email or "").strip()
server/services\auth_service.py:22:    if not email_value or not psw_value:
server/services\auth_service.py:27:            exists = session.scalar(select(User.id).where(User.email == email_value))
server/services\auth_service.py:31:            user = User(email=email_value, psw=psw_value)
server/services\auth_service.py:44:def login_user(email: str, psw: str) -> dict:
server/services\auth_service.py:48:    email_value = (email or "").strip()
server/services\auth_service.py:50:    if not email_value or not psw_value:
server/services\auth_service.py:55:            user = session.scalar(select(User).where(User.email == email_value))
server/services\auth_service.py:65:def get_user_id_by_email(email: str) -> dict:
server/services\auth_service.py:66:    """EN: Resolve user id by email for legacy cache fallback paths.
server/services\auth_service.py:67:    RU: Найти user id по email для fallback-путей со старым кешем.
server/services\auth_service.py:69:    email_value = (email or "").strip()
server/services\auth_service.py:70:    if not email_value:
server/services\auth_service.py:74:            user_id = session.scalar(select(User.id).where(User.email == email_value))
server/services\__init__.py:7:    get_user_id_by_email,
server/services\__init__.py:17:from server.services.rating_service import get_top_ratings
server/services\__init__.py:23:    "get_user_id_by_email",
server/services\__init__.py:28:    "get_top_ratings",
server/services\rating_service.py:15:def get_top_ratings(limit: int = 100) -> list[dict]:
server/services\rating_service.py:16:    """EN: Return top users by rating/record as plain dict list.
server/services\rating_service.py:17:    RU: Вернуть топ пользователей по rating/record в виде списка словарей.
server/services\rating_service.py:30:                    User.email.label("email"),
server/services\rating_service.py:33:                    ProfileGame.rating.label("rating"),
server/services\rating_service.py:39:                    desc(ProfileGame.rating),
server/services\rating_service.py:40:                    desc(ProfileGame.record),
server/services\rating_service.py:50:            email_raw = (row.get("email") or "").strip()
server/services\rating_service.py:51:            user_name = login_raw if login_raw and login_raw != "no data" else email_raw
server/services\rating_service.py:58:                rating_value = int(row.get("rating") or 0)
server/services\rating_service.py:60:                rating_value = 0
server/services\rating_service.py:66:                    "rating": rating_value,
server/services\profile_service.py:12:_PROFILE_GAME_FIELDS = {"record", "rating", "balance"}
server/services\profile_service.py:99:    rating: int | None = None,
server/services\profile_service.py:116:            if rating is not None:
server/services\profile_service.py:117:                obj.rating = int(rating)
server/models\profile_user.py:24:        unique=True,
server/models\profile_user.py:25:        index=True,
server/models\profile_game.py:14:    """EN: Stores record/rating/balance summary for exactly one user.
server/models\profile_game.py:15:    RU: Хранит сводные record/rating/balance ровно для одного пользователя.
server/models\profile_game.py:24:        unique=True,
server/models\profile_game.py:25:        index=True,
server/models\profile_game.py:29:    rating: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default=text("0"))
server/models\user.py:21:    """EN: Primary user table with unique email and password string field.
server/models\user.py:22:    RU: Основная таблица пользователей с уникальным email и строковым полем пароля.
server/models\user.py:28:    email: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)

~~~

### Bottleneck notes
- Current server module is DB/service layer only; no HTTP API entrypoint yet (FastAPI/Flask marker check above).
- On-prem deployment needs API process manager + reverse proxy before multi-client usage.
- SQLAlchemy pool is enabled in server/db.py; tune PostgreSQL max_connections when real concurrency appears.

## Readiness checklist

| Item | Status | Comment |
|---|---|---|
| PostgreSQL reachable locally | OK | Based on DATABASE_URL locality check |
| DATABASE_URL valid for PostgreSQL | OK | Must start with postgresql |
| Alembic sees migrations | OK | current/heads outputs captured |
| App DB connectivity (SELECT 1) | OK | Smoke output in section above |
| Ports available for future API server | RISK | Check host_netstat_200 |
| Secrets not hardcoded | RISK | Soft grep only; manual review still needed |
| Docker/Compose available (if used) | OK | Docker command outputs captured |

