# Atlas Industries — MFA Setup Guide / دليل إعداد المصادقة الثنائية

**Document ID:** IT-MFA-010
**Owner / الجهة المسؤولة:** IT Security / قسم أمن المعلومات
**Last Updated / آخر تحديث:** 1 May 2025
**Version / الإصدار:** 4.0

---

## EN — Overview

Multi-Factor Authentication (MFA) is **mandatory for all Atlas Industries employees**, contractors, and interns. MFA protects your account even if your password is leaked or guessed.

## AR — نظرة عامة

المصادقة الثنائية (MFA) **إلزامية لجميع موظفي شركة أطلس الصناعية**، المتعاقدين، والمتدربين. توفر المصادقة الثنائية حماية لحسابك حتى في حال تسرب كلمة المرور أو اختراقها.

---

## EN — Supported App

Atlas Industries supports **Microsoft Authenticator** only. Third-party apps (Google Authenticator, Authy) are **not supported** for production accounts due to recovery and policy requirements.

## AR — التطبيق المعتمد

تدعم شركة أطلس الصناعية **تطبيق Microsoft Authenticator فقط**. التطبيقات الأخرى مثل Google Authenticator و Authy **غير مدعومة** لحسابات الإنتاج بسبب متطلبات الاسترداد والسياسة.

---

## EN — Setup Steps

1. Install **Microsoft Authenticator** from the App Store (iOS) or Google Play (Android).
2. On your computer, open `mfa.atlas-industries.com` and sign in with your SSO credentials.
3. Click **Add MFA Method** → **Authenticator App**.
4. Scan the QR code displayed on screen using the Microsoft Authenticator app.
5. Enter the 6-digit code from the app to confirm.
6. Save the **8-digit recovery code** shown after setup — store it in a safe place (not on your laptop).

## AR — خطوات الإعداد

1. قم بتنزيل تطبيق **Microsoft Authenticator** من App Store أو Google Play.
2. من الكمبيوتر، افتح الرابط `mfa.atlas-industries.com` وسجل الدخول ببيانات SSO.
3. انقر على **إضافة طريقة تحقق** → **تطبيق المصادقة**.
4. امسح رمز QR الظاهر على الشاشة باستخدام تطبيق Microsoft Authenticator.
5. أدخل الرمز المكون من 6 أرقام من التطبيق للتأكيد.
6. احفظ **رمز الاسترداد المكون من 8 أرقام** في مكان آمن (ليس على الكمبيوتر).

---

## EN — Lost Device

If you lose your MFA device, contact the IT Service Desk immediately at `support@atlas-industries.com` or by phone. Provide your recovery code or be prepared to verify your identity through your direct manager. Account access is suspended until verification is complete.

## AR — فقدان الجهاز

في حال فقدان جهاز المصادقة، تواصل فوراً مع قسم الدعم على `support@atlas-industries.com` أو عبر الهاتف. قدم رمز الاسترداد أو تحقق من هويتك عبر المدير المباشر. يتم تعليق الحساب إلى أن يتم التحقق.

---

*Related / مستندات ذات صلة: IT-VPN-001, IT-PWD-002, IT-AUP-006*
