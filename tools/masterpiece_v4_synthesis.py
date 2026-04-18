import os
import re

def synthesize_v4():
    print("Starting FTA Masterpiece V4.0 Synthesis...")
    
    path_foundations = r'c:\Users\allmy\Desktop\aaa\field_transistor_alternative\FTA_Book_Draft_AR.md'
    path_v3_masterpiece = r'c:\Users\allmy\Desktop\aaa\field_transistor_alternative\FTA_Book_Draft_AR_V3_1_Masterpiece.md'
    path_output = r'c:\Users\allmy\Desktop\aaa\field_transistor_alternative\FTA_Book_Draft_AR_V4_0_Masterpiece.md'
    
    # 1. Load Sources
    with open(path_foundations, 'r', encoding='utf-8-sig') as f:
        foundations_content = f.read()
    
    with open(path_v3_masterpiece, 'r', encoding='utf-8-sig') as f:
        v3_lines = f.readlines()
        
    # 2. Extract Parts from V3 Masterpiece
    # Header (Title, TOC, Intro until Chapter 1)
    header = "".join(v3_lines[:358])
    header = header.replace("V3.1 Masterpiece", "V4.0 Masterpiece Supreme")
    header = header.replace("النسخة النهائية الكاملة", "النسخة السيادية الشاملة")
    
    # Technical Phases (Ch 7 to start of Ch 18)
    technical_phases = "".join(v3_lines[746:2890]) # Line 747 is index 746
    
    # Final Chapters (Ch 19 onwards)
    final_chapters = "".join(v3_lines[2945:]) # Line 2946 is index 2945
    
    # 3. Prepare Chapter 18 (QMV)
    chapter_18 = """
## <a name="ch18"></a>الفصل الثامن عشر: صمام التوجيه الكمي المغناطيسي (Quantum Magnetic Valve - QMV)

### 18.1 الهندسة العميقة وكسر الحواجز التقليدية (Phase 8 Breakthrough)
في هذا الفصل، ننتقل من التحكم الكهربائي الصرف إلى التحكم الهندسي بالحث المغناطيسي. صمام التوجيه الكمي (QMV) يمثل الذروة التقنية لمشروع FTA في إصداره الرابع (V4.0)، حيث ندمج لوحة الحث (U-Plate) المنطقية مع بنية الفجوات النانوية المزدوجة لتحقيق استجابة فائقة السرعة.

### 18.2 آلية إخماد لورنتز (Lorentz Quenching Mechanism)
تعتمد التقنية على تسليط تيار تعديل (Modulation Current) عبر اللوحة العلوية، مما يولد مجالاً مغناطيسياً عمودياً على مسار الإلكترونات النفقية. 
- **التأثير:** عند تفعيل المجال، تنحرف الإلكترونات عن مسارها المباشر بفعل قوة لورنتز، مما يزيد من طول المسار الفعلي خلف الحاجز ويقلل احتمالية النفق بشكل دراماتيكي.
- **النتائج:** تم التحقق عبر المحاكاة (`sim_phase8_magnetic_valve.py`) من أن تياراً قدره 10mA في لوحة الحث يكفي لخفض التيار الناتج بنسبة تفوق 14 ضعفاً، مما يوفر "هامش إغلاق" (Off-State) لم يكن ممكناً في الإصدارات السابقة.

![هندسة صمام التوجيه الكمي](../assets/images1/fta_asset_131.png)
*الشكل 18.1: المخطط الهندسي لصمام QMV ووضع لوحة الحث U-Plate فوق الفجوة النانوية.*

### 18.3 التميز الحراري: الموليبدينوم مقابل النحاس
تم اختيار الموليبدينوم (Mo) كركيزة أساسية بدلاً من النحاس (Cu) لضمان الاستقرار الحراري في ظروف التشغيل القاسية. معامل التمدد الحراري المنخفض للموليبدينوم ($4.8 \\times 10^{-6} K^{-1}$) يضمن بقاء الفجوات النانوية (2nm) مستقرة هندسياً تحت إجهاد تيارات التعديل العالية.

### 18.4 منحنى الإخماد والتحكم الخطي
تُظهر نتائج المحاكاة علاقة خطية هامة بين تيار الحث وكسب التيار النازل، مما يحول الـ FTA من مجرد "مفتاح" إلى "صمام" تحكم دقيق (Valve) يضاهي الصمامات المفرغة القديمة ولكن بأحجام نانوية وكفاءة كمومية.

![منحنى الإخماد المغناطيسي](../assets/images1/fta_qmv_quench_curve.png)
*الشكل 18.2: استجابة التيار الناتج لتيار التعديل في لوحة الحث، موضحاً منطقة القطع (Quenching Region).*

---
"""

    # 4. Assemble the Masterpiece
    # We strip the title and redundant header from Foundations content if needed
    # (Foundations_content usually starts with # FTA Foundations)
    
    full_manuscript = []
    full_manuscript.append(header)
    full_manuscript.append("\n# الجزء الأول: الأسس السيادية (Foundations)\n")
    full_manuscript.append(foundations_content)
    full_manuscript.append("\n# الجزء الثاني: الأطوار التقنية المتقدمة (Technical Phases)\n")
    full_manuscript.append(technical_phases)
    full_manuscript.append(chapter_18)
    full_manuscript.append("\n# الجزء الثالث: الصناعة والنهائية (DIY & Finality)\n")
    full_manuscript.append(final_chapters)
    
    content = "\n".join(full_manuscript)
    
    # 5. Fix Image Paths (Ensure absolute paths in the final draft if required, or keep relative)
    # The user wanted portability, we'll ensure they point to assets/
    content = content.replace("../assets/", "assets/") 
    
    # 6. Save File
    with open(path_output, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Success! V4.0 Masterpiece generated at: {path_output}")

if __name__ == "__main__":
    synthesize_v4()
