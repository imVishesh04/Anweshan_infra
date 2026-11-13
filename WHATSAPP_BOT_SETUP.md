# WhatsApp Bot — Setup (simple steps)

Bot kya karega:
1. Customer kuch bhi bheje → 3–4 line greeting + bhasha: **1. English 2. हिंदी 3. ଓଡ଼ିଆ**
2. Phir sawaal (button / list tap karo ya number type karo):
   - Kaam kya hai (Full home / Kitchen & wardrobe / Shop-office / Furniture repair / Kuch aur)
   - Size (1/2/3 BHK, villa, shop) → Area/city → Nayi ya purani jagah → Budget → Kab shuru → Photos → Visit ka time
   - Furniture / Kuch aur: details → area → photos → visit
3. End mein summary + "team call karegi"
4. Enquiry **Admin → Enquiries** mein aa jaati hai (green **WhatsApp** tag) + **Telegram alert**
5. Customer ki photos aur baad ke messages bhi **Telegram** pe aa jaate hain

**Website se aaya customer:** Services card, Gallery design ya Furniture tool ka WhatsApp button dabane pe message ke end mein ek code jaata hai (jaise `Ref: AI-KITCHEN`). Bot us code se kaam pehchaan leta hai aur **"Aapko kis kaam mein madad chahiye?" skip** kar deta hai. Seedha greeting → bhasha → baaki sawaal.
Direct "Hi" likhne wale (ya website ka general "Chat on WhatsApp" button) se kaam ka sawaal poocha jaata hai.

Customer kabhi bhi **MENU** likhe → shuru se.

---

## Step 0 — Number decide karo

- **Naya SIM lo** (sabse aasaan). Is number pe WhatsApp app install **mat** karna.
  Bot isi number pe chalega. Aapka purana number (86584 29239) WhatsApp Business app pe waise hi chalta rahega.
- Agar naye SIM pe pehle se WhatsApp hai → app mein *Settings → Account → Delete account* karo, tabhi API pe judega.

## Step 1 — Meta app banao (15 min)

1. **business.facebook.com** → "ANWESHAN Infra" business portfolio banao (agar nahi hai).
2. **developers.facebook.com** → *My Apps → Create app* → use case **"Connect with customers through WhatsApp"** → business portfolio select karo → Create.
3. App mein **WhatsApp → API Setup** → *Add phone number* → naya SIM number, display name **ANWESHAN Infra**, category *Home improvement* → OTP se verify.
4. Wahin **Phone number ID** copy karo. 📋 (ye `WA_PHONE_NUMBER_ID` hai)
5. **WhatsApp Manager → Payment settings** → card add karo. (1,000 service messages/month free, uske baad ~₹0.115 + GST per message)

## Step 2 — 3 secret cheezein copy karo

| Kya | Kahan milega | Railway variable |
|---|---|---|
| App secret | App → *App settings → Basic* → App secret → Show | `WA_APP_SECRET` |
| Permanent token | business.facebook.com → *Settings → Users → System users* → Add (Admin) → *Assign assets*: apna app + WhatsApp account (full control) → *Generate token* → expiry **Never** → tick `whatsapp_business_messaging` + `whatsapp_business_management` | `WA_ACCESS_TOKEN` |
| Verify token | Khud banao, koi bhi lamba text, jaise `anweshan-bot-7Kq92xLm4Pz` | `WA_VERIFY_TOKEN` |

⚠️ Ye values kisi ko mat bhejna, screenshot mein bhi nahi.

## Step 3 — Code push + Railway variables

1. Zip ki files apne project mein same jagah paste karo (replace) → VS Code se commit + push.
2. Railway → backend service → **Variables** → ye add karo:
   ```
   WA_VERIFY_TOKEN=<step 2 wala>
   WA_APP_SECRET=<step 2 wala>
   WA_ACCESS_TOKEN=<step 2 wala>
   WA_PHONE_NUMBER_ID=<step 1 wala>
   WA_OWNER_CONTACT=+91 86584 29239
   ```
3. Deploy hone do (green ✅).

## Step 4 — Webhook jodo

1. Meta app → **WhatsApp → Configuration → Webhook → Edit**
   - Callback URL: `https://anweshaninfra-production.up.railway.app/api/whatsapp/webhook`
   - Verify token: wahi `WA_VERIFY_TOKEN`
   - **Verify and save** dabao
2. Neeche **Webhook fields → messages → Subscribe** ✅
3. App ko **Live** karo: *App settings → Basic* → Privacy Policy URL: `https://anweshaninfra.in/privacy.html` → Save → upar **Publish / Live** toggle.
   (Live nahi kiya toh asli customers ke messages bot tak nahi aayenge.)

## Step 5 — Test

1. Apne personal phone se naye bot number pe "hi" bhejo → greeting + 3 language buttons aane chahiye.
2. Pura flow complete karo → Admin → Enquiries mein green **WhatsApp** tag wali enquiry + Telegram alert.
3. Sab theek → Admin → **Settings → WhatsApp number** mein naya bot number daal do. Ab website ka WhatsApp button seedha bot pe jayega. (Call button purane number pe hi rahega.)

---

## Kuch nahi aa raha? (jaldi check)

| Problem | Kya check karo |
|---|---|
| "Verify and save" fail | Railway deploy green hai? `WA_VERIFY_TOKEN` exact same hai? Four `WA_` variables set hain? |
| "hi" bhejne pe reply nahi | App **Live** hai? *messages* field subscribed hai? Railway logs mein `WhatsApp send failed` dikh raha? |
| `Meta error code 190` log | Token galat/expire → naya System User token banao |
| `Meta error code 131030` | App abhi test mode mein hai / number allowed list mein nahi |
| Photos Telegram pe nahi | Telegram variables set hain? (Photo 5 MB se badi ho toh skip hoti hai) |

## Note
- Hindi aur Odia lines ek baar kisi native se padhwa lena; badalni ho toh `backend/app/whatsapp/texts.py` mein text change karo.
- Bot sirf customer ke message ka jawab deta hai — khud se kisi ko message nahi bhejta.
