# المملكة المغربية — بوابة ومستودع المساطر الإدارية CPSV-AP 3.2.0
# Kingdom of Morocco — CPSV-AP 3.2.0 Administrative Portal & Semantic Dataset

[![CPSV-AP 3.2.0](https://img.shields.io/badge/CPSV--AP-3.2.0_SEMIC-blue.svg)](https://semiceu.github.io/CPSV-AP/releases/3.2.0/)
[![SHACL Validation](https://img.shields.io/badge/SHACL_Validation-100%25_PASS_(0_Violations)-brightgreen.svg)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)]()
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)]()
[![Version](https://img.shields.io/badge/Version-0.9.0_Production_Ready-orange.svg)]()

---

## 🏛️ نظرة عامة | Overview

المستودع الوطني الرسمي للبيانات المترابطة الخاصة بالمساطر والخدمات العمومية للمملكة المغربية، وفقاً للمعيار الأوروبي الموحد لتوصيف الخدمات العمومية **CPSV-AP 3.2.0** (Core Public Service Vocabulary – Application Profile).

يحتوي المستودع على:
* **102,009 ثلاثية دلالية (Semantic Triples)** في المستودع الوطني الرئيسي خالية تماماً من أي مخالفات لمعيار SHACL (**0 مخالفات بنسبة نجاح 100%**).
* **2,382 مسطرة وخدمة عمومية منقحة** تشمل الإدارات المركزية، الجماعات الترابية، القنصليات بالخارج، وسيناريوهات البطاقة الوطنية وجواز السفر البيومتري وشواهد السكنى.
* **107 مؤسسة وإدارة عمومية مختصة** (Competent Authorities).
* **2,075 مخرج وشهادة إدارية نهائية** (Outputs / Deliverables).
* **7,798 وثيقة ومستند إثبات** (Evidences / Required Documents).
* **2,382 تعريفة وتكلفة رسمية** (Formal Costs / Tariffs).
* **سياسة معرفات مبسطة موحدة (Simplified ID Policy)**: ترقيم تسلسلي قياسي ونظيف (`PS00001`، `CA00001`، `OTPT000001`، `EVD00001`، `COST00001`).
* **مصدر حقيقة معياري غير قابل للتعارض (Canonical Source of Truth)** يضم التسميات الرسمية والأوصاف الإدارية الدقيقة ويدعم المطابقة الضبابية (Fuzzy Matching عبر RapidFuzz).
* **بوابة ويب رسمية** تمكن المستخدمين من البحث والتدقيق الحي، تعديل المساطر، وفحص مطابقة SHACL المباشر عبر المتصفح.

---

## 🏷️ سياسة المعرفات الموحدة والمبسطة | Simplified ID Architecture

لتيسير التعامل البشري والتقني وتفادي المعرفات العشوائية المعقدة (UUIDs و MD5 Slugs)، يعتمد المستودع نسق ترقيم تسلسلي قياسي ونظيف مرتبط بمصدر الحقيقة المعتمد:

| الكيان الإداري | النسق والبادئة | مثال المعرف | المجال الحالي | مسار المعرف الدلالي (URI) |
| :--- | :--- | :--- | :--- | :--- |
| **مسطرة / خدمة عمومية** | `PS` + 5 أرقام | `PS00001` | `PS00001` — `PS02382` | `http://procedures_administratives_cpsv.ma/id/public_service/PS00001` |
| **إدارة / مؤسسة مختصة** | `CA` + 5 أرقام | `CA00001` | `CA00001` — `CA00107` | `http://procedures_administratives_cpsv.ma/id/organisation/CA00001` |
| **مخرج / شهادة مسلمة** | `OTPT` + 6 أرقام | `OTPT000001` | `OTPT000001` — `OTPT002075` | `http://procedures_administratives_cpsv.ma/id/output/OTPT000001` |
| **وثيقة إثبات مطلوبة** | `EVD` + 5 أرقام | `EVD00001` | `EVD00001` — `EVD07798` | `http://procedures_administratives_cpsv.ma/id/evidence/EVD00001` |
| **تكلفة / رسم إداري** | `COST` + 5 أرقام | `COST00001` | `COST00001` — `COST02382` | `http://procedures_administratives_cpsv.ma/id/cost/COST00001` |

> [!NOTE]
> يتم الحفاظ تلقائياً على سجل المعرفات السابقة (`legacy_uuid` و `legacy_slug`) داخل ملف سجل الحقيقة المعتمد [`canonical_ids_registry.json`](file:///home/ysn/Desktop/NYB_28092026/procedures_administratives_maroc_cpsv/src/morocco_cpsv_composer/registry/canonical_ids_registry.json) لضمان التوافقية العكسية 100%.

---

## 📂 بنية المشروع الصالحة للشحن والتسليم | Repository Structure

```text
.
├── docker-compose.yml                       # تشغيل فوري بنقرة واحدة عبر Docker Compose (Port 8085)
├── Dockerfile                               # صورة Docker معزولة ومؤمنة (Python 3.12-slim)
├── .dockerignore                            # تصفية الملفات والمسودات لتقليص حجم الحاوية
├── .gitattributes                           # فرض نهايات أسطر LF لمنع أخطاء Windows CRLF
├── .gitignore                               # استبعاد الملفات المؤقتة وملفات التخزين المؤقت
├── requirements.txt                         # حزم بايثون المعتمدة (rdflib, pyshacl, rapidfuzz)
├── run.sh                                   # سكريبت الإقلاع الموحد (Docker أو بيئة محلية)
├── audit_modifications.log                  # سجل تدقيق وتتبع كافة التعديلات والتحديثات الإدارية
├── README.md                                # الدليل التوثيقي الشامل (هذا الملف)
│
├── output/                                  # البيانات الدلالية الوطنية الرسمية (Master Datasets)
│   ├── procedures_administratives_cpsv.ttl  # المستودع الدلالي الوطني بصيغة Turtle (102,018 Triples)
│   └── procedures_administratives_cpsv.rdf  # المستودع الدلالي الوطني بصيغة RDF/XML (102,018 Triples)
│
└── src/
    ├── procedures_administratives_cpsv.db   # قاعدة البيانات المرجعية التشغيلية (SQLite WAL Mode)
    ├── sync_dataset_distributions.py        # سكريبت المزامنة التلقائية للمستودعات وتوزيعات RDF
    │
    ├── sql/
    │   └── 03_rdf_views.sql                 # استعلامات توليد ثلاثيات RDF لمعيار CPSV-AP
    │
    ├── morocco_cpsv_composer/               # تطبيق الويب ومحرك الواجهات البرمجية وإدارة المعرفات
    │   ├── __init__.py
    │   ├── id_policy.py                     # محرك سياسة المعرفات ومنع التكرار (Fuzzy Deduplication)
    │   ├── audit_logger.py                  # مسجل أحداث التدقيق المباشر لكافة عمليات التعديل والحذف
    │   ├── builder.py                       # محول البيانات إلى ثلاثيات RDF وTurtle
    │   ├── procedure_manager.py             # إدارة واستعلام وتعديل المساطر في قاعدة البيانات
    │   ├── registry.py                      # سجل المؤسسات والمخرجات والوثائق وقوائم المصطلحات
    │   ├── server.py                        # خادم HTTP محلي والواجهات البرمجية REST API (منفذ 8085)
    │   ├── registry/
    │   │   └── canonical_ids_registry.json  # مصدر الحقيقة المعتمد (العناوين، الأوصاف، المعرفات)
    │   │
    │   └── web/                             # واجهة البوابة الإدارية الرسمية
    │       ├── index.html                   # هيكل البوابة باللغة العربية (الاتجاه من اليمين لليسار RTL)
    │       ├── portal.css                   # التنسيق الإداري الرسمي المستوحى من الصفقات العمومية والخزينة
    │       ├── portal.js                    # التفاعل، البحث المباشر، الفحص الآني وتحديث البيانات
    │       ├── coat_of_arms.svg             # الشعار الرسمي للمملكة المغربية
    │       ├── flag_morocco.svg             # العلم المغربي الرسمي (SVG)
    │       └── flag_morocco.png             # العلم المغربي الرسمي (PNG)
    │
    └── morocco_cpsv_validator/              # محرك تدقيق المطابقة الرسمية SEMIC SHACL
        ├── __init__.py
        ├── validator.py                     # محرك تدقيق SHACL عالي الأداء مع التخزين المؤقت
        ├── official_cpsv_ap_3.2.0_shapes.ttl # قواعد وقوالب التدقيق الرسمية للمفوضية الأوروبية
        └── validate_dataset.py              # أداة سطر الأوامر لتدقيق ملفات Turtle وRDF/XML
```

---

## 🚀 دليل التشغيل السريع | Quick Start

### الخيار 1: التشغيل عبر Docker Compose (موصى به للإنتاج والشحن)
يضمن هذا الخيار بيئة معزولة بالكامل دون الحاجة لتثبيت أي متطلبات على النظام المضيف:

```bash
# 1. الانتقال إلى مجلد المشروع
cd procedures_administratives_maroc_cpsv

# 2. تشغيل الحاوية في الخلفية مع إعادة البناء
docker compose up -d --build

# 3. التأكد من حالة الحاوية
docker compose ps
```

افتح المتصفح مباشرة على:
👉 **[http://localhost:8085](http://localhost:8085)**

لإيقاف الحاوية:
```bash
docker compose down
```

---

### الخيار 2: التشغيل المباشر عبر بايثون (Native Python)
يتطلب بايثون 3.10 أو أحدث:

```bash
# 1. تثبيت الحزم المطلوبة
pip install -r requirements.txt

# 2. تشغيل الخادم
python3 src/morocco_cpsv_composer/server.py 8085
```

أو عبر سكريبت الإقلاع الموحد:
```bash
./run.sh
```

---

## 🔄 المزامنة التلقائية وتحديث البيانات | Auto-update & Synchronization

يوفر المشروع سكريبتات مؤتمتة لضمان اتساق ثلاثيات RDF مع قاعدة البيانات ومصدر الحقيقة في أي لحظة:

### 1. مزامنة المستودع الوطني وتوزيعات RDF:
لقراءة قاعدة البيانات وتوليد ملفات `output/procedures_administratives_cpsv.ttl` و `output/procedures_administratives_cpsv.rdf` وسيناريوهات `cnie_passport_cpsv.ttl`:
```bash
docker compose exec morocco-cpsv-portal python3 src/sync_dataset_distributions.py
# أو محلياً:
python3 src/sync_dataset_distributions.py
```

### 2. تحديث وتثبيت مصدر الحقيقة (Source of Truth):
لقراءة أحدث التعديلات على الأوصاف والعناوين من قاعدة البيانات وتحديث [`canonical_ids_registry.json`](file:///home/ysn/Desktop/NYB_28092026/procedures_administratives_maroc_cpsv/src/morocco_cpsv_composer/registry/canonical_ids_registry.json):
```bash
python3 src/update_source_of_truth_and_ids.py
```

---

## 🔍 تدقيق البيانات عبر سطر الأوامر | CLI SHACL Validation

يمكنك التحقق من مطابقة أي ملف للبيانات مقابل قواعد المفوضية الأوروبية SEMIC CPSV-AP 3.2.0 في أي وقت:

```bash
# تدقيق ملف السيناريوهات المنقحة
python3 src/morocco_cpsv_validator/validate_dataset.py src/cnie_passport_cpsv.ttl

# تدقيق المستودع الوطني الكامل
python3 src/morocco_cpsv_validator/validate_dataset.py output/procedures_administratives_cpsv.ttl
```

**النتيجة الرسمية المعتمدة (Validation Output):**
```text
1. Loading data graph: src/cnie_passport_cpsv.ttl (format: turtle)...
   Parsed 1580 triples in 0.22s.
2. Validating against official SHACL shapes: official_cpsv_ap_3.2.0_shapes.ttl...
   Validation finished in 1.37s.

========================================
CONFORMANCE STATUS: PASS (Conforms)
========================================
Total Constraint Violations: 0
```

---

## 🌐 الواجهات البرمجية المتاحة | REST API Endpoints

يقدم الخادم واجهة REST API عالية الأداء لدعم التطبيقات والأنظمة الخارجية:

| المسار (Endpoint) | الطريقة | الوصف |
| :--- | :--- | :--- |
| `GET /api/status` | GET | إحصائيات المستودع وحالة جاهزية محرك SHACL |
| `GET /api/procedures` | GET | البحث الفوري في المساطر مع الترقيم التلقائي (`q`, `limit`, `offset`) |
| `GET /api/procedures/<id>` | GET | تفاصيل مسطرة كاملة بالمعرف المبسط (مثل `PS02382`) مع الوثائق والمخرج النهائي |
| `POST /api/procedures/update` | POST | تعديل وتحديث بيانات المسطرة في قاعدة البيانات وفحص SHACL وتسجيل الحدث |
| `POST /api/procedures/validate-draft` | POST | فحص مطابقة مسودة مسطرة قيد التحرير قبل حفظها |
| `DELETE /api/procedures/<id>` | DELETE | حذف مسطرة مع روابط إثباتاتها وتسجيل عملية الحذف في سجل التدقيق |
| `GET /api/authorities` | GET | قائمة المؤسسات والإدارات العمومية المختصة الـ 107 مع إمكانية البحث |
| `POST /api/authorities` | POST | إضافة مؤسسة أو إدارة عمومية جديدة مع تخصيص معرف `CA{:05d}` |
| `GET /api/outputs` | GET | قائمة المخرجات والشهادات الإدارية الـ 2,075 مع البحث |
| `POST /api/outputs` | POST | إضافة مخرج إداري جديد مع تخصيص معرف `OTPT{:06d}` |
| `GET /api/evidences` | GET | قائمة وثائق ومستندات الإثبات الـ 7,798 مع البحث |
| `GET /api/audit-log` | GET | استرجاع آخر 150 حركة وتعديل إداري مسجل في سجل التدقيق المباشر |
| `GET /api/vocabularies` | GET | المصطلحات المضبوطة (العملات، اللغات، النطاق الجغرافي) |
| `POST /api/validate` | POST | تدقيق نص Turtle مقابل مواصفات SEMIC SHACL المباشرة |

---

## 🛡️ المعاجم والمصطلحات المضبوطة (Controlled Vocabularies)

تعتمد البيانات المصطلحات المرجعية الصادرة عن مكتب المنشورات التابع للاتحاد الأوروبي (EU Publications Office):
* **العملة (Currency)**: `http://publications.europa.eu/resource/authority/currency/MAD` (درهم مغربي).
* **اللغات (Languages)**: 
  * `http://publications.europa.eu/resource/authority/language/ARA` (العربية - `@ar`)
  * `http://publications.europa.eu/resource/authority/language/FRA` (الفرنسية - `@fr`)
  * `http://publications.europa.eu/resource/authority/language/BER` (الأمازيغية - `@zgh`)
* **النطاق المكاني (Spatial)**: `http://publications.europa.eu/resource/authority/country/MAR` (المملكة المغربية).

---

## 📄 الترخيص وحقوق الاستخدام | License
هذا العمل مخصص لأرشفة ومشاركة البيانات الإدارية المفتوحة للمملكة المغربية وفق معايير الويب الدلالي W3C وSEMIC.
