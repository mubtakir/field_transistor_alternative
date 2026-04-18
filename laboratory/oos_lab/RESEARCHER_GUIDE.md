# دليل الباحث الشامل: من التصميم إلى المحاكاة (OOS-Lab v1.1)

مرحباً بك في مختبر **OOS-Lab Professional**. هذا الدليل مصمم ليأخذك خطوة بخطوة من الفكرة الفيزيائية إلى النموذج الصناعي الجاهز للفحص والتشغيل.

---

## المرحلة الأولى: التصميم الفيزيائي (Physical Design)
ابدأ بتحديد أبعاد الجهاز والمواد المستخدمة. يمكنك الاختيار بين التصميم الكلاسيكي أو التصميم الطبيعي الخطّي.

**الخطوات:**
1. حدد سمك العازل (`tox`) والمساحة (`area`).
2. اختر مادة البوابة (مثلاً `buriti` للخطية أو `pani_rgo` للمنطق المكمل).

```python
from oos_lab import UPlateDevice, NaturalFTA

# مثال لتجهيز خلية FTA طبيعية (Natural NDR)
device = NaturalFTA(
    geometry={'tox': 20e-9, 'area': 1e-12},
    material_type='buriti'
)
```

---

## المرحلة الثانية: المحاكاة والتحسين (Unified Simulation)
استخدم الواجهة الموحدة لإجراء كافة أنواع التحاليل دون تعقيد.

**الخطوات:**
1. قم بإجراء مسح الجهد (IV) للتأكد من سلوك النفق.
2. حلل استجابة التردد (AC) لإيجاد عرض النطاق.

```python
import oos_lab

# محاكاة IV بلمسة واحدة
iv_results = oos_lab.simulate(device_type='natural', analysis='iv', V_stop=5.0)

# محاكاة الاستجابة النبضية (Transient)
pulse_data = oos_lab.simulate(device_type='u_plate', analysis='transient', V_step=1.0)
```

---

## المرحلة الثالثة: القياس الافتراضي (Virtual Lab Bench)
قبل الانتقال للتصنيع، استخدم "طاولة المختبر" لقياس الخصائص الكهربائية الدقيقة.

**الخطوات:**
1. استخدم **VirtualMultimeter** لقياس السعة (C) والمقاومة (R).
2. استخدم **Impedance Analyzer** لرسم مخطط بود.

```python
from oos_lab import FTALabBench

bench = FTALabBench()
metrics = bench.multimeter.measure_all(V_test=1.2)
print(f"Capacitance: {metrics['capacitance']*1e15:.2f} fF")
```

---

## المرحلة الرابعة: التكامل الصناعي (Industry Export)
حول نتائجك إلى ملفات يمكن لمهندسي الإلكترونيات استخدامها في برامج مثل Cadence و ADS.

**الخطوات:**
1. صدر موديل **Verilog-A** الموجود في مجلد `models/`.
2. استخرج صافي الدائرة **SPICE (.subckt)**.

```python
bench.export_to_spice("my_fta_model.lib")
bench.export_to_csv("simulation_data.csv", iv_results)
```

---

## المرحلة الخامسة: قائمة فحص الجاهزية (Testing Readiness Checklist)
تأكد من النقاط التالية قبل تشغيل المختبر الفعلي أو إرسال التصميم للتصنيع:

- [ ] **التحقق من العزل:** هل `tox` كافٍ لمنع الانهيار الكهربائي؟
- [ ] **نقطة الخطية:** هل قمت بتشغيل `lab.find_optimal_bias()` لإيجاد جهد العمل المثالي؟
- [ ] **كسب الجهد:** هل الكسب المتوقع في تقرير DMM يتجاوز 10 V/V؟
- [ ] **استجابة التردد:** هل التردد القاطع (Cut-off) مناسب للتطبيق المطلوب؟

---

**ملاحظة:** لمزيد من التفاصيل التقنية، راجع [USER_MANUAL.md](file:///c:/Users/allmy/Desktop/oos/oos_lab/USER_MANUAL.md).

**إعداد: باسل يحيى عبد الله — مارس 2026**
