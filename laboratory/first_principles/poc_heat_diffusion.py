import numpy as np
import matplotlib.pyplot as plt
import os
import time
import sys

# إصلاح مشكلة طباعة الحروف العربية في موجه أوامر ويندوز
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# إعداد المتغيرات الأساسية للمكان والزمان
grid_size = 100
steps = 3000
dt = 0.1
dx = 1.0
dy = 1.0

# 1. تعريف مكان المحاكاة والمواد (Spatial and Material Grid)
# سنبدأ بوضع معامل انتشار (توصيلية) منخفض يمثل الفراغ أو العازل
alpha = np.ones((grid_size, grid_size)) * 0.0001 

# 2. نحت "شكل" المادة وتحديد هويتها في الشبكة 
# لنصنع ناقلاً بشكل حرف U مقلوب وسطه ضيق (عنق زجاجة)
alpha[20:80, 20:80] = 0.5 # المربع الكلي للمادة الناقلة

# نفرغ قلب المربع لنصنع شكل حرف U
alpha[40:80, 40:60] = 0.0001 

# نجعل أحد الأذرع أضيق (نغير في الشكل المكاني)
alpha[50:80, 20:30] = 0.0001

# 3. مصفوفة الطاقة/الجهد
U = np.zeros((grid_size, grid_size))

# 4. دالة المحاكاة الموضعية (Local Interactions)
def simulate_step(U, alpha):
    U_new = U.copy()
    # كل خلية تتفاعل مع جيرانها الأربعة فقط لنقل الطاقة بناءً على مادتها (alpha)
    laplacian = (
        U[2:, 1:-1] + U[:-2, 1:-1] + 
        U[1:-1, 2:] + U[1:-1, :-2] - 
        4 * U[1:-1, 1:-1]
    ) / (dx * dy)
    
    # التحديث يعتمد على التوصيلية الموضعية
    U_new[1:-1, 1:-1] = U_new[1:-1, 1:-1] + alpha[1:-1, 1:-1] * dt * laplacian
    
    # مصدر طاقة مستمر (مثبط حراري أو قطب بطارية) في أسفل الذراع الأيمن
    U_new[20:30, 60:80] = 100.0
    return U_new

print("بدء محاكاة المبادئ الأولى (First Principles)...")
start_time = time.time()

# 5. تشغيل الزمن خطوة بخطوة
for step in range(steps):
    U = simulate_step(U, alpha)

end_time = time.time()
print(f"انتهت المحاكاة في {end_time - start_time:.2f} ثانية للـ {steps} خطوة.")

# 6. رسم النتائج لتتأكد بعينيك!
plt.figure(figsize=(14, 6))

plt.subplot(1, 2, 1)
plt.title("توزيع المادة في الفضاء (Identities & Shapes)", fontsize=14)
plt.imshow(alpha, cmap='viridis', origin='lower')
plt.colorbar(label='معامل التوصيلية')

plt.subplot(1, 2, 2)
plt.title(f"انتشار الطاقة بعد {steps} تفاعل موضعي", fontsize=14)
# نستخدم حداً أقصى للألوان لكي تظهر التدرجات بوضوح
plt.imshow(U, cmap='inferno', origin='lower', vmax=100)
plt.colorbar(label='مستوى الطاقة (الجهد / الحرارة)')

plt.tight_layout()
output_path = os.path.join(os.path.dirname(__file__), "simulation_result.png")
plt.savefig(output_path, dpi=150)
print(f"تم حفظ الصورة بنجاح في:\n{output_path}")
