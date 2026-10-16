# Campus Hostel LAN – Detailed Network Design

## 1. Physical Topology

### Devices

| Device | Model | Role |
|--------|-------|------|
| HLN-Router | Cisco 2911 | WAN gateway, inter-VLAN routing, NAT, ACL |
| HLN-Core-SW | Cisco 3650 L3 | VLAN aggregation, trunk hub, STP root |
| HLN-Admin-SW | Cisco 2960 | Admin + Warden block access switch |
| HLN-HostelA-SW | Cisco 2960 | Hostel Block A student access switch |
| HLN-HostelB-SW | Cisco 2960 | Hostel Block B student access switch |
| HLN-Server-SW | Cisco 2960 | Server room access switch |
| DHCP+DNS Server | Cisco Server | DHCP pools + DNS name resolution |
| Web Server | Cisco Server | Flask hostel management app |
| DB Server | Cisco Server | SQLite/MySQL database |
| AP-A-F1/F2 | Wi-Fi AP | Student VLAN wireless, Block A |
| AP-B-F1/F2 | Wi-Fi AP | Student VLAN wireless, Block B |
| AP-Guest-A/B | Wi-Fi AP | Guest VLAN wireless |

---

## 2. IP Addressing Scheme

### VLAN Subnets

```
VLAN 10 – Administration : 192.168.10.0/24
  Gateway    : 192.168.10.1  (Router sub-interface Gi0/1.10)
  Static range: .1 – .20
  DHCP range : .21 – .254
  Core-SW SVI: 192.168.10.254
  Admin-SW SVI: 192.168.10.253

VLAN 20 – Students : 192.168.20.0/24
  Gateway    : 192.168.20.1  (Router sub-interface Gi0/1.20)
  Static range: .1 – .10
  DHCP range : .11 – .254
  HostelA-SW SVI: 192.168.20.252
  HostelB-SW SVI: 192.168.20.253

VLAN 30 – Wardens : 192.168.30.0/24
  Gateway    : 192.168.30.1  (Router sub-interface Gi0/1.30)
  Static range: .1 – .10
  DHCP range : .11 – .254

VLAN 40 – Common/Lab : 192.168.40.0/24
  Gateway    : 192.168.40.1  (Router sub-interface Gi0/1.40)
  Static range: .1 – .10
  DHCP range : .11 – .254

VLAN 50 – Guest : 192.168.50.0/24
  Gateway    : 192.168.50.1  (Router sub-interface Gi0/1.50)
  DNS Server : 8.8.8.8 (Google DNS – no internal access)
  Static range: .1 – .10
  DHCP range : .11 – .254

VLAN 100 – Servers : 192.168.100.0/24
  Gateway    : 192.168.100.1  (Router sub-interface Gi0/1.100)
  Static IPs ONLY:
    .2  = DHCP + DNS Server
    .3  = Web / App Server (hostel.local)
    .4  = Database Server
    .254 = Server-SW management SVI

WAN Interface (Gi0/0):
  Router WAN IP : 203.0.113.1/30
  ISP Gateway   : 203.0.113.2
```

---

## 3. VLAN Trunk Architecture

```
HLN-Router Gi0/1 ──(trunk: all VLANs)──> HLN-Core-SW Gi0/1
HLN-Core-SW Gi0/2 ──(trunk: 10,30,100)──> HLN-Admin-SW Gi0/1
HLN-Core-SW Gi0/3 ──(trunk: 20,40,50)──> HLN-HostelA-SW Gi0/1
HLN-Core-SW Gi0/4 ──(trunk: 20,40,50)──> HLN-HostelB-SW Gi0/1
HLN-Core-SW Gi0/5 ──(trunk: 100,10)──> HLN-Server-SW Gi0/1
```

Native VLAN on all trunks: 999 (untagged/unused)

---

## 4. Routing Configuration

### Method: Router-on-a-Stick (IEEE 802.1Q)

The router uses sub-interfaces on `GigabitEthernet0/1` to route between VLANs:

```
interface GigabitEthernet0/1.10  → VLAN 10 gateway 192.168.10.1
interface GigabitEthernet0/1.20  → VLAN 20 gateway 192.168.20.1
interface GigabitEthernet0/1.30  → VLAN 30 gateway 192.168.30.1
interface GigabitEthernet0/1.40  → VLAN 40 gateway 192.168.40.1
interface GigabitEthernet0/1.50  → VLAN 50 gateway 192.168.50.1
interface GigabitEthernet0/1.100 → VLAN 100 gateway 192.168.100.1
```

Default route: `ip route 0.0.0.0 0.0.0.0 203.0.113.2`

---

## 5. DHCP Design

DHCP relay (`ip helper-address`) forwards broadcast DHCP requests from all VLANs to the centralized DHCP server at `192.168.100.2`.

| Pool | Scope | Lease | Notes |
|------|-------|-------|-------|
| VLAN10_ADMIN | 192.168.10.21-254 | 1 day | Admin workstations |
| VLAN20_STUDENTS | 192.168.20.11-254 | 8 hours | High churn; short lease |
| VLAN30_WARDENS | 192.168.30.11-254 | 1 day | Warden devices |
| VLAN40_COMMON | 192.168.40.11-254 | 4 hours | Lab/common devices |
| VLAN50_GUEST | 192.168.50.11-254 | 2 hours | Very short; guest devices |
| VLAN100_SERVERS | Static only | N/A | No DHCP pool |

---

## 6. DNS Design

DNS Server: `192.168.100.2`
Domain: `hostel.local`

Key records:
- `hostel.local` → `192.168.100.3` (Web Server)
- `www.hostel.local` → `192.168.100.3`
- `dns.hostel.local` → `192.168.100.2`
- `db.hostel.local` → `192.168.100.4`

Guest VLAN receives `8.8.8.8` as DNS → cannot resolve internal names.

---

## 7. NAT/PAT

```
ip nat inside source list NAT_ACL interface GigabitEthernet0/0 overload
```

All internal VLANs (10,20,30,40,50,100) are translated to the router's WAN IP (`203.0.113.1`) for Internet access.

---

## 8. Security Features

### VLAN Isolation
- Traffic between VLANs must pass through the router
- ACLs applied on each sub-interface control inter-VLAN communication

### Access Control Lists
See `configs/acl_rules.txt` for full ACL configuration.

Summary:
- Students cannot reach Admin or Warden VLANs
- Guest devices cannot reach any internal VLAN
- All ACL denies are logged for monitoring

### Port Security
Applied on Admin and Server switch ports:
- Maximum 1 MAC address per port
- Sticky MAC learning
- Violation: restrict (admin) or shutdown (server)

### SSH Management
All switches and router configured for SSHv2 only.
Default VTY transport: `transport input ssh`
RSA 2048-bit keys.

---

## 9. Wireless Design

| SSID | VLAN | Location | Security |
|------|------|----------|---------|
| hostel-student-A | 20 | Block A, Floors 1-2 | WPA2 |
| hostel-student-B | 20 | Block B, Floors 1-2 | WPA2 |
| hostel-guest | 50 | Common areas | Open/Captive portal |
| hostel-admin | 10 | Admin office | WPA2-Enterprise |
| hostel-warden | 30 | Warden rooms | WPA2 |

---

## 10. Spanning Tree

- Mode: Rapid-PVST (one instance per VLAN)
- STP Root: HLN-Core-SW (priority 4096 for all VLANs)
- PortFast enabled on all access ports to speed up device convergence

---

## 11. Network Connectivity Test Plan

| Test | Source | Destination | Expected |
|------|--------|-------------|---------|
| DHCP | Student PC | DHCP Server | Gets 192.168.20.x |
| DNS | Student PC | hostel.local | Resolves 192.168.100.3 |
| HTTP | Student browser | hostel.local | Hostel portal loads |
| Ping | Student | Web Server | ✅ Success |
| Ping | Student | Admin PC | ❌ Blocked by ACL |
| Ping | Student | Warden PC | ❌ Blocked by ACL |
| Ping | Guest | Any internal | ❌ Blocked by ACL |
| Ping | Admin | Any device | ✅ Full access |
| SSH | Admin PC | Core Switch | ✅ Management access |
| Internet | Any VLAN | 8.8.8.8 | ✅ NAT success |
