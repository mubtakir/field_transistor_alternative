import taichi as ti
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import time

# إصلاح ترميز طباعة الحروف العربية في موجه الأوامر
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# مساعدة Taichi في اختيار أفضل معالج رسومي متاح
ti.init(arch=ti.gpu)

# 1. إعداد دقة الفضاء (Grid Resolution)
n = 200  # شبكة 200x200 يعني 40000 خلية!

# 2. الهياكل البيانية لمتغيرات الفيزياء (Fields)
V = ti.field(dtype=ti.f32, shape=(n, n))
V_new = ti.field(dtype=ti.f32, shape=(n, n))

T = ti.field(dtype=ti.f32, shape=(n, n))
T_new = ti.field(dtype=ti.f32, shape=(n, n))

# هويات المادة (خصائصها)
sigma = ti.field(dtype=ti.f32, shape=(n, n))  # Electrical Conductivity
alpha = ti.field(dtype=ti.f32, shape=(n, n))  # Thermal Diffusivity

@ti.kernel
def init_materials_and_fields():
    """نحت الشكل ثلاثي الأقطاب والأذرع (مشابه لفكرة مسار اختناق)"""
    for i, j in sigma:
        # فراغ أو عازل (توصيلية شبه معدومة)
        sigma[i, j] = 1e-4
        alpha[i, j] = 1e-4

        # رسم جسد المادة الرئيسة بشكل يشبه الحرف U
        if 40 <= i < 160 and 40 <= j < 160:
            sigma[i, j] = 1.0
            alpha[i, j] = 1.0
        
        # تفريغ قلب الحرف 
        if 80 <= i < 160 and 80 <= j < 120:
            sigma[i, j] = 1e-4
            alpha[i, j] = 1e-4
            
        # اختناق (عنق الزجاجة) في الذراع الأيسر لكي نرى تكدس الطاقة الحرارية!
        if 100 <= i < 160 and 40 <= j < 60:
            sigma[i, j] = 1e-4
            alpha[i, j] = 1e-4

        # إعداد المجالات 
        V[i, j] = 0.0
        # درجة حرارة الغرفة (20 درجة)
        T[i, j] = 20.0  

@ti.kernel
def solve_voltage():
    """بناء المجال الكهربائي بناءً على الأقطاب واستمرارية الناقل (Jacobi Iteration)"""
    # Taichi ينفذ هذا في كل من الـ 40 ألف خلية على التوازي!
    for i, j in ti.ndrange((1, n-1), (1, n-1)):
        # المتوسط החسابي لتوصيلية كل واجهة مشتركة بين خليتين (Harmonic mean is better but arithmetic is simple)
        s_right = 0.5 * (sigma[i, j] + sigma[i+1, j])
        s_left  = 0.5 * (sigma[i, j] + sigma[i-1, j])
        s_up    = 0.5 * (sigma[i, j] + sigma[i, j+1])
        s_down  = 0.5 * (sigma[i, j] + sigma[i, j-1])
        
        sum_s = s_right + s_left + s_up + s_down
        
        # موازنة الجهد الكهربائي حسب جودة النواقل المجاورة
        V_new[i, j] = (s_right*V[i+1, j] + s_left*V[i-1, j] + s_up*V[i, j+1] + s_down*V[i, j-1]) / sum_s
        
        # تحديد الأقطاب الكهربائية الثابتة
        # Ground (0V) عند أسفل الذراع الأيسر
        if i < 50 and j >= 40 and j < 80:
            V_new[i, j] = 0.0
            
        # VCC (100V) عند أسفل الذراع الأيمن
        if i < 50 and j >= 120 and j < 160:
            V_new[i, j] = 100.0

    # تحديث مصفوفة الجهد المعتمدة
    for i, j in ti.ndrange((1, n-1), (1, n-1)):
        V[i, j] = V_new[i, j]

@ti.kernel
def update_thermal(dt: ti.f32):
    """حساب الحرارة المتبددة (Joule Heating) وانتشارها"""
    for i, j in ti.ndrange((1, n-1), (1, n-1)):
        # 1. حساب التسخين بواسطة جول: Q = sigma * |Grad(V)|^2
        dv_dx = (V[i+1, j] - V[i-1, j]) * 0.5
        dv_dy = (V[i, j+1] - V[i, j-1]) * 0.5
        
        # طاقة مصطنعة لغرض توضيح الرؤية (مكبّر للرؤية)
        Q = sigma[i, j] * (dv_dx**2 + dv_dy**2) * 20.0  
        
        # 2. حساب انتشار الحرارة من الخلايا الساخنة للأبرد
        a_right = 0.5 * (alpha[i, j] + alpha[i+1, j])
        a_left  = 0.5 * (alpha[i, j] + alpha[i-1, j])
        a_up    = 0.5 * (alpha[i, j] + alpha[i, j+1])
        a_down  = 0.5 * (alpha[i, j] + alpha[i, j-1])
        
        laplace_T = (a_right*(T[i+1, j]-T[i, j]) - a_left*(T[i, j]-T[i-1, j]) + 
                     a_up*(T[i, j+1]-T[i, j]) - a_down*(T[i, j]-T[i-1, j]))
                     
        # 3. تحديث الدرجة الحالية للحرارة
        T_new[i, j] = T[i, j] + dt * laplace_T + dt * Q
        
        # تثبيت حرارة الأقطاب كأنها موصولة بمبردات خارجية
        if i < 50 and ((j >= 40 and j < 80) or (j >= 120 and j < 160)):
            T_new[i, j] = 20.0

    # اعتماد التحديث الحراري
    for i, j in ti.ndrange((1, n-1), (1, n-1)):
        T[i, j] = T_new[i, j]

def main():
    print("> تهيئة الفضاء الفيزيائي المادي...")
    init_materials_and_fields()
    
    # 1. حساب توافق المجال الكهربائي 
    # (سرعة الضوء تجعل الكهرباء تستقر قبل أن تتغير الحرارة بشكل ملحوظ)
    print("> يتم الآن حل المجال الكهربائي في الفضاء (معادلة بواسون)...")
    t0 = time.time()
    for _ in range(8000): # تكرارات الموازنة للجهد
        solve_voltage()
    print(f"تم بناء المجال الكهربائي واستقراره في {time.time()-t0:.2f} ثانية!")
    
    # 2. تطوير الزمن لانتشار الحرارة المتولدة عن المقاومة المكانية
    print("> بدأ التأثير الكهرومغناطيسي بتوليد حرارة جول عبر المكان...")
    t1 = time.time()
    steps = 4000
    for step in range(steps):
        update_thermal(0.01)
    print(f"تم إغلاق دورة الزمن الحرارية في {time.time()-t1:.2f} ثانية!")
            
    # استخراج البيانات من كارت الشاشة وعرضها
    V_np = V.to_numpy().T
    T_np = T.to_numpy().T
    sigma_np = sigma.to_numpy().T
    
    plt.figure(figsize=(15, 6))
    
    plt.subplot(1, 3, 1)
    plt.title("المصفوفة الهندسية المادية (Conductivity)", fontsize=13)
    plt.imshow(sigma_np, origin='lower', cmap='viridis')
    plt.colorbar(label='توصيلية المادة')

    plt.subplot(1, 3, 2)
    plt.title("توزع الجهد الكهربائي المستقر (V)", fontsize=13)
    plt.imshow(V_np, origin='lower', cmap='plasma')
    plt.colorbar(label='الجهد والتيار')

    plt.subplot(1, 3, 3)
    plt.title("تولد وتكدس الحرارة (Joule Heating hotspot)", fontsize=13)
    plt.imshow(T_np, origin='lower', cmap='inferno')
    plt.colorbar(label='درجة الحرارة (C)')

    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), "electro_thermal_result.png")
    plt.savefig(output_path, dpi=150)
    print(f"\n[نجاح] تم حفظ نتائج المحاكاة المتطورة في المسار:\n{output_path}")

if __name__ == "__main__":
    main()
