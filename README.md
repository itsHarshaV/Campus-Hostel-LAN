# Campus Hostel LAN

> **Computer Networks PBL** – Design and Implementation of a Secure Campus Hostel Network with a full-stack Hostel Management Web Application.

---

## Project Overview

This project models a **real-world college hostel network** using **Cisco Packet Tracer**, demonstrating key Computer Networking concepts:

| Concept | Implementation |
|---|---|
| LAN / WLAN | Wired student rooms + wireless access points |
| VLANs | 6 VLANs across admin, students, wardens, common, guest, servers |
| IP Addressing | Classful subnetting per VLAN (`192.168.x.0/24`) |
| DHCP | Centralized pools with per-VLAN lease times |
| DNS | Internal resolution for `hostel.local` |
| Routing | Router-on-a-stick (802.1Q sub-interfaces) |
| NAT/PAT | Shared Internet via router WAN interface |
| ACLs | Per-VLAN access restriction policies |
| TCP/IP | All application traffic over TCP/IP |
| Client-Server | Flask web app serving all hostel modules |
| Network Security | VLAN isolation + ACL enforcement + port security |

---

## Network Architecture

```
              INTERNET (203.0.113.0/30)
                        |
              ┌─────────────────┐
              │   HLN-Router    │  Cisco 2911
              │  (2911 Router)  │  NAT · ACLs · DHCP Relay
              └────────┬────────┘
                  802.1Q Trunk
              ┌────────▼────────┐
              │  HLN-Core-SW    │  Cisco 3650 L3
              │  (Core Switch)  │  VLANs · STP Root
              └──┬────┬────┬───┘
          ┌──────┘    │    └──────┐
   ┌──────▼──┐  ┌─────▼───┐  ┌───▼──────┐  ┌───────────┐
   │Admin-SW │  │HostelA  │  │HostelB   │  │ Server-SW │
   │VLAN 10  │  │VLAN 20  │  │VLAN 20   │  │ VLAN 100  │
   │VLAN 30  │  │VLAN 40  │  │VLAN 40   │  │           │
   └────┬────┘  │VLAN 50  │  │VLAN 50   │  └─────┬─────┘
        │       └────┬────┘  └────┬─────┘        │
   Admin PCs    Student Rooms  Student Rooms  DHCP·DNS·Web
   Wardens      Wi-Fi APs      Wi-Fi APs      DB Server
```

---

## VLAN Plan

| VLAN | Name | Subnet | Gateway | DHCP Lease |
|------|------|--------|---------|------------|
| 10 | Administration | 192.168.10.0/24 | 192.168.10.1 | 1 Day |
| 20 | Students | 192.168.20.0/24 | 192.168.20.1 | 8 Hours |
| 30 | Wardens | 192.168.30.0/24 | 192.168.30.1 | 1 Day |
| 40 | Common/Lab | 192.168.40.0/24 | 192.168.40.1 | 4 Hours |
| 50 | Guest | 192.168.50.0/24 | 192.168.50.1 | 2 Hours |
| 100 | Servers | 192.168.100.0/24 | 192.168.100.1 | Static |

---

## Server IPs

| IP | Role |
|----|------|
| 192.168.100.2 | DHCP + DNS Server |
| 192.168.100.3 | Web / Application Server (`hostel.local`) |
| 192.168.100.4 | Database Server (SQLite/MySQL) |

---

## ACL Security Policy

| VLAN | Can Access | Blocked From |
|------|-----------|--------------|
| Admin (10) | Everything | — |
| Students (20) | Web Server, DNS, Internet | Admin, Warden VLANs |
| Wardens (30) | Servers, Students, Internet | Admin VLAN |
| Common/Lab (40) | Web Server, DNS, Internet | Admin, Warden VLANs |
| Guest (50) | Internet ONLY | ALL internal VLANs |
| Servers (100) | (no inbound ACL) | — |

---

## Web Application

A full-stack Hostel Management System built with **Python Flask + SQLite**.

### Modules

| Module | Features |
|--------|---------|
| **Student** | Dashboard · Room details · Notices · Complaints · Mess Menu |
| **Warden** | Dashboard · View students · Manage complaints · Post notices · Room overview |
| **Admin** | Manage students · Manage rooms · Manage wardens · Network info · ACL overview |
| **Network Dashboard** | Live device status · Topology view · VLAN chips · Device table |

### Default Credentials

| Role | Username | Password |
|------|---------|----------|
| Admin | `admin` | `admin123` |
| Warden | `warden_a` | `warden123` |
| Student | `stu001` | `student123` |

---

## Running the Web App

### Prerequisites

```bash
pip install flask
```

### Start

```bash
cd webapp
python app.py
```

Opens at: **http://localhost:5000**  
On LAN: **http://hostel.local:5000** (with DNS configured)

---

## Configuration Files

| File | Device | Purpose |
|------|--------|---------|
| `configs/router.txt` | HLN-Router (2911) | Sub-interfaces, NAT, ACLs, SSH |
| `configs/core_switch.txt` | HLN-Core-SW (3650) | VLANs, trunk links, STP root |
| `configs/admin_switch.txt` | HLN-Admin-SW (2960) | VLAN 10/30 access ports, port security |
| `configs/hostel_a_switch.txt` | HLN-HostelA-SW (2960) | VLAN 20/40/50 student + Wi-Fi + guest |
| `configs/hostel_b_switch.txt` | HLN-HostelB-SW (2960) | Same as A, Block B |
| `configs/server_switch.txt` | HLN-Server-SW (2960) | VLAN 100, strict port security |
| `configs/dhcp_pools.txt` | Router / DHCP Server | All 6 VLAN DHCP pools |
| `configs/dns_records.txt` | DNS Server | A records, PTR, CNAMEs |
| `configs/acl_rules.txt` | Router | Full ACL logic reference |

---

## Network Demonstration Flow

1. Student connects to `hostel-student-A` Wi-Fi on Block A
2. Device receives IP `192.168.20.x` via DHCP (8h lease)
3. DNS resolves `hostel.local` → `192.168.100.3`
4. Request travels: Student → HostelA-SW → Core-SW → Router → Server-SW → Web Server
5. ACL on `Gi0/1.20` permits HTTP to `192.168.100.3:80`
6. Flask app serves the hostel portal
7. SQLite database returns student data
8. Response returned to student browser
9. Student tries `ping 192.168.10.x` → **ACL blocks** (logged)
10. Ping tests: student → server ✅ · student → admin ❌

---

## Technologies

- **Network**: Cisco Packet Tracer · Cisco 2911 Router · Cisco 3650 L3 Switch · Cisco 2960 Switches · Wi-Fi APs
- **Web**: Python 3 · Flask · SQLite · HTML5 · CSS3 (Glassmorphism) · JavaScript

---

## Project Structure

```
campus-hostel-lan/
├── configs/                    # Cisco IOS configuration files
│   ├── router.txt
│   ├── core_switch.txt
│   ├── admin_switch.txt
│   ├── hostel_a_switch.txt
│   ├── hostel_b_switch.txt
│   ├── server_switch.txt
│   ├── dhcp_pools.txt
│   ├── dns_records.txt
│   └── acl_rules.txt
├── docs/
│   └── NETWORK_DESIGN.md
├── webapp/
│   ├── app.py                  # Flask application
│   ├── schema.sql              # DB schema + seed data
│   ├── requirements.txt
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── templates/
│       ├── base.html
│       ├── login.html
│       ├── network_dashboard.html
│       ├── student/
│       ├── warden/
│       └── admin/
└── README.md
```
