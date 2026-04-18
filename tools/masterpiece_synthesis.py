import os
import re

# Paths
source_md = r'c:\Users\allmy\Desktop\oos\field_transistor_alternative\phase2_foundations\FTA_Book_Draft_AR_V3_1_Masterpiece0.md'
source_html = r'c:\Users\allmy\Desktop\oos\field_transistor_alternative\phase2_foundations\FTA_Book_Draft_AR_V3_1_Masterpiece.html'
target_path = r'c:\Users\allmy\Desktop\oos\field_transistor_alternative\phase2_foundations\FTA_Book_Draft_AR_V3_1_Masterpiece.md'

# V4.0 Content in Arabic
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

def synthesize():
    try:
        # 1. Read MD Foundation (Ch 1-18)
        with open(source_md, 'r', encoding='utf-8-sig') as f:
            md_lines = f.readlines()
        
        # Merge V4.0 into Chapter 10
        # Line 1173 (Index 1172) is Header 10, Line 1439 (Index 1438) is Header 11
        md_lines.insert(1438, v4_content + "\n\n")
        
        # 2. Extract Ch 19 from HTML
        with open(source_html, 'r', encoding='utf-8-sig') as f:
            html_content = f.read()
        
        # Search for Arabic Chapter 19 phrase
        ch19_phrase = 'الفصل التاسع عشر'
        start_idx = html_content.find(ch19_phrase)
        if start_idx != -1:
            # Backtrack to find the start of the header tag <h2 or similar
            header_start = html_content.rfind('<h', 0, start_idx)
            next_header = re.search(r'<h[1-6]', html_content[start_idx:])
            if next_header:
                end_idx = start_idx + next_header.start()
            else:
                end_idx = len(html_content)
            
            ch19_html = html_content[header_start:end_idx]
            # Convert HTML to basic MD
            ch19_md = ch19_html.replace('</h2>', '\n\n').replace('</h1>', '\n\n').replace('</h3>', '\n\n')
            ch19_md = re.sub(r'<h[1-6][^>]*>', '## ', ch19_md)
            ch19_md = re.sub(r'<p[^>]*>', '\n', ch19_md).replace('</p>', '\n')
            ch19_md = re.sub(r'<br[^>]*>', '\n', ch19_md)
            ch19_md = re.sub(r'<[^>]+>', '', ch19_md)
            ch19_md = re.sub(r'\n{3,}', '\n\n', ch19_md).strip()
            
            md_lines.append("\n\n" + ch19_md + "\n")
            print("INFO: Chapter 19 extracted and appended.")
        else:
            print("WARNING: Chapter 19 NOT found in HTML. Check encoding/tags.")

        # 3. Final Write
        with open(target_path, 'w', encoding='utf-8-sig') as f:
            f.writelines(md_lines)
            
        final_size = os.path.getsize(target_path)
        print(f"SUCCESS: Synthesized Masterpiece V4.0. Final Size: {final_size} bytes.")

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    synthesize()
