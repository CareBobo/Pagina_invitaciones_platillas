import re

file_path = r"c:\Users\USER\Desktop\TODOS LOS PROYECTOS\Invitacion 1 boda\templates\invitacion_libro.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern for right and left rings
pattern = r"<!-- Espiral \((?:Derecha|Izquierda)\) -->\s*<div[^>]*url\(['\"]/static/assets/anillos\.png['\"]\)[^>]*>\s*</div>"
new_content, count = re.subn(pattern, "", content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Removed {count} occurrences.")
