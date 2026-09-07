import os,shutil

ROOT = r"D:\alcoder\moslem tools\moslemTools"

deleted = 0

for root, dirs, files in os.walk(ROOT, topdown=True):
    for dirname in dirs[:]:
        if dirname == "__pycache__":
            path = os.path.join(root, dirname)

            try:
                shutil.rmtree(path)
                deleted += 1
                print(f"تم حذف: {path}")
            except Exception as e:
                print(f"فشل حذف: {path}\nالسبب: {e}")

print("\n" + "=" * 50)
print(f"تم حذف {deleted} مجلد __pycache__.")
input("اضغط Enter للخروج...")