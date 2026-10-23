# WESTVISION ARTS — Toleo lililoboreshwa

Toleo la Flask + Socket.IO + SQLite lenye muonekano wa kisasa, group chat, matangazo, usajili wa akaunti, emoji picker, media uploads, na sehemu ya faragha ya Owner.

## Vilivyoboreshwa
- Muonekano wa rangi za navy, purple na gold; chat imepanuliwa na ujumbe una bubble za kisasa.
- Emoji picker kwenye group chat.
- Usajili wa mara ya kwanza kwa email + code ya mwaliko; kila akaunti hupata jina/namba ya kipekee `WESTVISION ARTS #0001`, `#0002`, n.k.
- Email ikishasajiliwa haiwezi kusajiliwa tena; mwanachama hutumia Ingia mara zinazofuata.
- Password huhifadhiwa kama hash, si maandishi ya kawaida.
- Ujumbe, matangazo na private chat huhifadhiwa kwenye SQLite ya seva.
- Owner inbox hufunguliwa baada ya code ya Owner kuthibitishwa.
- Video fupi zina ukaguzi wa muda wa upande wa kivinjari (sekunde 8); ukihost app hadharani, ongeza ukaguzi wa server-side kwa ffprobe/ffmpeg.
- PWA manifest/service worker kwa usaidizi wa kusakinisha kwenye vifaa vinavyoiunga mkono.

## Kuingia / kujisajili
- Kuingia kwa haraka: jina `tanganyika`, PIN `11223344` (inaweza kubadilishwa kwa `WV_QUICK_LOGIN_NAME` na `WV_QUICK_LOGIN_PIN`).
1. Akaunti za kawaida zinaweza kutumia **Jisajili mara ya kwanza**.
2. Weka email yako, code ya kujiunga `tanganyika`, na password yako mwenyewe yenye angalau herufi/namba 8.
3. App itakupa jina la mwanachama lenye namba moja kwa moja.
4. Baadaye tumia email na password kwenye **Ingia**.
5. Owner anaingia kama mwanachama kisha kwenye Chat ya Owner anatumia code `MOUD1234`.

> Code za msingi ni za demo tu. Kabla ya deployment, badilisha `WV_JOIN_CODE`, `WV_OWNER_PASSWORD`, na `WV_SECRET` kuwa siri ndefu na za kipekee kupitia environment variables. Usitumie code hizi za demo kwenye tovuti ya umma.

## Kuendesha kwenye kompyuta ya maendeleo
Unahitaji Python 3.10+ na intaneti mara ya kwanza kusakinisha maktaba.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Kisha fungua `http://127.0.0.1:5000`.

## Kuitumia kwenye Android, iPhone na kompyuta bila Python
App hii ya backend haiwezi kufanya mazungumzo ya watumiaji tofauti kwa kufungua HTML pekee; lazima seva iendeshwe kwenye hosting. Ili kila mtu aitumie bila kusakinisha Python, deploy seva hii kwenye huduma ya hosting inayotumia Python, weka HTTPS, na tumia domain ya app. Baada ya hapo, Android/desktop zinaweza kutumia Install App; iPhone inaweza kutumia Share → Add to Home Screen kupitia Safari.

## Usalama na mipaka
- Hili bado ni toleo la msingi linalohitaji security review kabla ya matumizi ya umma: weka HTTPS, siri za environment zenye nguvu, rate limiting, backup za database, server-side video duration validation, ukaguzi wa upload, na monitoring.
- `MOUD1234` ni code ya demo; ibadilishe kabla ya deployment.
- Kumbuka data iko kwenye database ya seva; ikihamishwa au kufutwa, ujumbe unaweza kuathirika.

## Marekebisho ya tatizo la ujumbe kutoonekana
Toleo hili lina HTTP/API fallback kwa kutuma ujumbe, matangazo na ujumbe wa faragha. Kwa hiyo, hata Socket.IO CDN ikishindwa kupakia kwenye intaneti fulani, ujumbe bado unaweza kuhifadhiwa na kuonekana kupitia refresh ya kiotomatiki (polling). Hili limeongezwa kwa sababu baadhi ya mitandao huzuia CDN ya Socket.IO.

**Muhimu:** Kutuma ujumbe kwa vifaa vingine kunafanya kazi tu pale app inapowekwa kwenye seva moja ya mtandaoni na watumiaji wote wanafungua URL hiyo hiyo. `127.0.0.1` ni kompyuta yako pekee; si link ya kuwatumia wanakikundi.
