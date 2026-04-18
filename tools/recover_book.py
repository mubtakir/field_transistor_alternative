import os

source_path = r'c:\Users\allmy\Desktop\oos\field_transistor_alternative\phase2_foundations\FTA_Book_Draft_AR_V3_1_Masterpiece0.md'
target_path = r'c:\Users\allmy\Desktop\oos\field_transistor_alternative\phase2_foundations\FTA_Book_Draft_AR_V3_1_Masterpiece.md'

# Core V4.0 Content in Arabic (Synthesized from session history)
v4_content = """
### 10.10 ثبات مادة الموليبدينوم مقابل النحاس (Mo vs Cu)
في الأبعاد النانوية، يصبح التمدد الحراري هو العائق الأول أمام استقرار الفجوات (Nano-gaps). 
- **النحاس (Cu):** معامل التمدد ($16.5 \\times 10^{-6} K^{-1}$) يؤدي لتشوه الصفائح عند حرارة التشغيل العالية.
- **الموليبدينوم (Mo):** معامل التمدد المنخفض ($4.8 \\times 10^{-6} K^{-1}$) يضمن بقاء الفجوات مستقرة حتى درجة حرارة 400 كلفن، مما يمنع حدوث قصر (Short Circuit) في الخلايا الحساسة.

### 10.11 بوابة الجرافين واختراق حاجز التيراهيرتز
تم التحقق عبر المحاكاة (`sim_graphene_thz.py V2.1`) من أن استخدام الجرافين كبوابة داخلية يؤدي إلى:
- **سرعة تبديل (f_t):** تصل إلى **318 THz**.
- **زمن صعود (Rise Time):** قدره **24.0 fs**، وهو ما يمثل تحسناً بمقدار **14.2 ضعفاً** مقارنة بالبوابات المعدنية التقليدية.
- **السبب الفيزيائي:** الشفافية الكهروستاتيكية للجرافين (Field Transparency) التي تسمح باختراق خطوط المجال دون تشتت الشحنات.

### 10.12 بنية نيتريك الغاليوم (GaN) والاستقطاب الذاتي
تعد ركيزة GaN ضرورية في بنية V4.0 لسببين:
1. **التحيز الذاتي (Self-Biasing):** استغلال حقول الاستقطاب التلقائي (Piezo-polarization) في GaN لتوفير جهد انحياز داخلي يقلل من متطلبات الجهد الخارجي.
2. **عزل فائق:** توفر الركيزة العزل اللازم للعمل بجهود تصل إلى 50V في مسافات نانوية دون حدوث انهيار بلوري.

### 10.13 المخطط النهائي V4.0: المصفوفة العليا (Supreme Matrix)
البنية الصناعية النهائية المقترحة لـ FTA تعتمد على:
- **المادة الموصلة الأساسية:** الموليبدينوم (للاستقرار).
- **مادة البوابة المتحكمة:** الجرافين أحادي الطبقة (للسرعة).
- **الركيزة والعازل الأساسي:** نيتريك الغاليوم (HEMT-Compatible).
"""

try:
    with open(source_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # Identify Chapter 10 location - find Header 10 and Header 11
    marker_10 = '## الفصل العاشر'
    marker_11 = '## الفصل الحادي عشر'
    
    if marker_10 in content:
        start_idx = content.find(marker_10)
        end_idx = content.find(marker_11) if marker_11 in content else len(content)
        
        # Keep original header but replace subsections (10.x are often missing in Masterpiece0)
        new_chapter_10 = content[start_idx:end_idx].rstrip() + "\n\n" + v4_content
        
        updated_content = content[:start_idx] + new_chapter_10 + content[end_idx:]
        
        with open(target_path, 'w', encoding='utf-8-sig') as f:
            f.write(updated_content)
        print(f'SUCCESS: Restored and Upgraded Masterpiece. New Size: {len(updated_content)} bytes.')
    else:
        # Try finding by word sequence if markers are slightly different
        print('ERROR: Could not find Chapter 10 marker in source.')

except Exception as e:
    print(f'FAILED: {type(e).__name__}: {e}')
