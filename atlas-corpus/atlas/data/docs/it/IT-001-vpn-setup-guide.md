# Atlas Industries — VPN Setup & Connection Guide

**Document ID:** IT-VPN-001
**Owner:** IT Infrastructure
**Last Updated:** 12 April 2025
**Audience:** All employees with remote-access needs

---

## Overview

Atlas Industries uses **Cisco AnyConnect Secure Mobility Client** to provide encrypted access to internal systems for employees working remotely or traveling. This guide covers first-time setup, daily use, and common troubleshooting.

## 1. Prerequisites

Before you begin, make sure you have:
- A company-issued laptop with up-to-date OS (Windows 10/11 or macOS 12+)
- Your Atlas SSO username and password
- A registered MFA device (see IT-MFA-010 if not yet registered)
- An active internet connection

## 2. Installation

### Windows
1. Open the Software Center from the Start menu.
2. Search for `Cisco AnyConnect` and click Install.
3. Reboot when prompted.

### macOS
1. Open Self Service (in your Applications folder).
2. Search `AnyConnect` and click Install.
3. When prompted, allow the system extension in System Settings → Privacy & Security.

> If neither tool is available on your device, submit a software request via ServiceDesk (see IT-SW-004).

## 3. Connection Settings

| Field | Value |
|---|---|
| Server | `vpn.atlas-industries.com` |
| Port | **443** (TCP) |
| Protocol | SSL |
| Auth | SSO + MFA |

## 4. Connecting

1. Launch Cisco AnyConnect.
2. In the connection field, enter `vpn.atlas-industries.com` and click Connect.
3. Enter your Atlas SSO username and password.
4. Approve the push notification on your MFA device (Microsoft Authenticator).
5. The status indicator turns green when the tunnel is up.

Sessions automatically disconnect after **8 hours of idle activity** and require re-authentication.

## 5. Common Issues

### "Login failed"
- Verify your password is current. Passwords expire every 90 days — see IT-PWD-002 to reset.
- Make sure your account is not locked. Five failed attempts triggers a 30-minute lockout.

### "Unable to establish a secure connection"
- Check that port 443 is not blocked on the network you're using (hotel/airport Wi-Fi sometimes blocks it).
- Try switching to a mobile hotspot to isolate the issue.

### MFA push doesn't arrive
- Open the Microsoft Authenticator app manually and check for a pending request.
- If your phone is offline, choose "Use a different verification method" and select the OTP option.

## 6. When to Open a Ticket

Open a ticket with IT Support at `support@atlas-industries.com` if:
- You see repeated "Connection terminated" errors after a successful login.
- VPN connects but internal sites (e.g. `intranet.atlas-industries.com`) do not load.
- Your laptop does not have Cisco AnyConnect available in Software Center.

Standard SLA for VPN tickets is **4 business hours**.

---

*Related: IT-MFA-010 (MFA Setup), IT-PWD-002 (Password Reset), IT-AUP-006 (Acceptable Use Policy).*
