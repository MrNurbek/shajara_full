from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path.cwd()
BACKUP_SUFFIX = ".bak_tree_upgrade"


def read(path: str) -> str:
    file_path = ROOT / path
    if not file_path.exists():
        raise FileNotFoundError(f"Topilmadi: {path}. Skriptni loyiha root papkasida ishga tushiring.")
    return file_path.read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    file_path = ROOT / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.exists():
        backup = file_path.with_name(file_path.name + BACKUP_SUFFIX)
        if not backup.exists():
            shutil.copy2(file_path, backup)
    file_path.write_text(content, encoding="utf-8", newline="\n")
    print(f"OK: {path}")


def replace_once(content: str, old: str, new: str, label: str) -> str:
    if old not in content:
        if new in content:
            return content
        raise RuntimeError(f"Marker topilmadi: {label}")
    return content.replace(old, new, 1)


def replace_between(content: str, pattern: str, new: str, label: str) -> str:
    updated, count = re.subn(pattern, new, content, count=1, flags=re.S)
    if count == 0:
        if new.strip() in content:
            return content
        raise RuntimeError(f"Blok topilmadi: {label}")
    return updated


def patch_tree_builder() -> None:
    path = "genealogy/services/tree_builder.py"
    content = read(path)

    if "from datetime import date" not in content:
        content = replace_once(
            content,
            "from __future__ import annotations\n\n",
            "from __future__ import annotations\n\nfrom datetime import date\n",
            "datetime import",
        )

    sort_func = '''\n\ndef child_sort_key(person: Person) -> tuple[bool, date, str, str, str, str]:\n    """Farzandlarni yosh tartibida saralaydi: 1-farzand eng katta bo‘ladi.\n\n    Tug‘ilgan sanasi yo‘q farzandlar ism-familiyasi bo‘yicha oxirroqqa qo‘yiladi.\n    Bu tartib SQLite/PostgreSQL dagi NULL saralash farqiga bog‘lanib qolmaydi.\n    """\n    birth_date = person.birth_date or date.max\n    return (\n        person.birth_date is None,\n        birth_date,\n        person.last_name.lower(),\n        person.first_name.lower(),\n        person.middle_name.lower(),\n        str(person.id),\n    )\n'''
    if "def child_sort_key(" not in content:
        content = replace_once(
            content,
            "\n\ndef children_of_marriage(marriage: Marriage) -> list[Person]:",
            sort_func + "\ndef children_of_marriage(marriage: Marriage) -> list[Person]:",
            "child_sort_key insert",
        )

    new_children_marriage = '''def children_of_marriage(marriage: Marriage) -> list[Person]:\n    children = [\n        link.child\n        for link in marriage.child_links.select_related("child").all()\n    ]\n    return sorted(children, key=child_sort_key)\n\n\n'''
    content = replace_between(
        content,
        r"def children_of_marriage\(marriage: Marriage\) -> list\[Person\]:\n.*?\n\ndef children_of_single_parent",
        new_children_marriage + "def children_of_single_parent",
        "children_of_marriage",
    )

    new_children_single = '''def children_of_single_parent(parent: Person) -> list[Person]:\n    children = [\n        link.child\n        for link in parent.single_child_links.select_related("child").all()\n    ]\n    return sorted(children, key=child_sort_key)\n\n\n'''
    content = replace_between(
        content,
        r"def children_of_single_parent\(parent: Person\) -> list\[Person\]:\n.*?\n\ndef order_partners",
        new_children_single + "def order_partners",
        "children_of_single_parent",
    )

    old_single_loop = '''    for child in children_of_single_parent(person):\n        node["children"].append(\n            build_from_person(\n                child,\n                seen_marriages=seen_marriages,\n                person_path=next_path,\n                max_depth=max_depth - 1,\n            )\n        )\n'''
    new_single_loop = '''    for birth_order, child in enumerate(children_of_single_parent(person), start=1):\n        child_node = build_from_person(\n            child,\n            seen_marriages=seen_marriages,\n            person_path=next_path,\n            max_depth=max_depth - 1,\n        )\n        child_node["birth_order"] = birth_order\n        node["children"].append(child_node)\n'''
    content = replace_once(content, old_single_loop, new_single_loop, "single parent children loop")

    old_marriage_loop = '''    for child in children_of_marriage(marriage):\n        node["children"].append(\n            build_from_person(\n                child,\n                seen_marriages=seen_marriages,\n                person_path=next_path,\n                max_depth=max_depth - 1,\n            )\n        )\n'''
    new_marriage_loop = '''    for birth_order, child in enumerate(children_of_marriage(marriage), start=1):\n        child_node = build_from_person(\n            child,\n            seen_marriages=seen_marriages,\n            person_path=next_path,\n            max_depth=max_depth - 1,\n        )\n        child_node["birth_order"] = birth_order\n        node["children"].append(child_node)\n'''
    content = replace_once(content, old_marriage_loop, new_marriage_loop, "marriage children loop")

    write(path, content)


def patch_tree_template() -> None:
    path = "templates/genealogy/tree.html"
    content = read(path)
    link = "  <link rel=\"stylesheet\" href=\"{% static 'genealogy/css/tree-map-upgrades.css' %}?v=20260615\">\n"
    if "tree-map-upgrades.css" not in content:
        content = replace_once(
            content,
            "  <link rel=\"stylesheet\" href=\"{% static 'genealogy/css/tree-modern.css' %}\">\n",
            "  <link rel=\"stylesheet\" href=\"{% static 'genealogy/css/tree-modern.css' %}\">\n" + link,
            "tree upgrade css link",
        )
    write(path, content)


def patch_recursive_template() -> None:
    path = "templates/genealogy/partials/tree_recursive.html"
    content = read(path)

    if "spouse-card partner-{{ forloop.counter }}" not in content:
        content = content.replace(
            '      <button class="person {% if p.gender == \'M\' %}male{% elif p.gender == \'F\' %}female{% else %}unknown{% endif %}{% if p.is_deceased %} deceased{% endif %}"',
            '      <button class="person spouse-card partner-{{ forloop.counter }} {% if p.gender == \'M\' %}male{% elif p.gender == \'F\' %}female{% else %}unknown{% endif %}{% if p.is_deceased %} deceased{% endif %}"',
            1,
        )

    badge = '''        {% if node.birth_order %}\n          <span class="child-order" aria-label="{{ node.birth_order }}-farzand" title="{{ node.birth_order }}-farzand">{{ node.birth_order }}</span>\n        {% endif %}\n'''
    if "class=\"child-order\"" not in content:
        single_pos = content.find('{% elif node.type == "single" %}')
        if single_pos == -1:
            raise RuntimeError("single node template topilmadi")
        marker = '        <span class="avatar-mini" aria-hidden="true">{{ p.name|first }}</span>\n'
        insert_pos = content.find(marker, single_pos)
        if insert_pos == -1:
            raise RuntimeError("single avatar marker topilmadi")
        insert_pos += len(marker)
        content = content[:insert_pos] + badge + content[insert_pos:]

    write(path, content)


def patch_tree_js() -> None:
    path = "static/genealogy/js/tree.js"
    content = read(path)

    content = content.replace("  const minScale = 0.25;\n  const maxScale = 3;", "  const minScale = 0.06;\n  const maxScale = 3.5;")

    old_fit = '''  function fitToView(){\n    const tree = inner.querySelector(".tree"); if(!tree) return;\n    const oldTransform = inner.style.transform;\n    inner.style.transform = "translate(0px, 0px) scale(1)";\n    const natural = tree.getBoundingClientRect();\n    inner.style.transform = oldTransform;\n    const pad = outer.clientWidth < 600 ? 24 : 70;\n    const sx = (outer.clientWidth - pad) / Math.max(1, natural.width);\n    const sy = (outer.clientHeight - pad) / Math.max(1, natural.height);\n    scale = clamp(Math.min(sx, sy), minScale, maxScale);\n    tx = (outer.clientWidth - natural.width * scale) / 2;\n    ty = (outer.clientHeight - natural.height * scale) / 2;\n    applyTransform();\n  }\n'''
    new_fit = '''  function fitToView(){\n    const tree = inner.querySelector(".tree"); if(!tree) return;\n    const oldTransform = inner.style.transform;\n    inner.style.transform = "translate(0px, 0px) scale(1)";\n    const naturalRect = tree.getBoundingClientRect();\n    const naturalWidth = Math.max(tree.scrollWidth, tree.offsetWidth, naturalRect.width, 1);\n    const naturalHeight = Math.max(tree.scrollHeight, tree.offsetHeight, naturalRect.height, 1);\n    inner.style.transform = oldTransform;\n    const pad = outer.clientWidth < 600 ? 20 : 82;\n    const viewportWidth = Math.max(1, outer.clientWidth - pad);\n    const viewportHeight = Math.max(1, outer.clientHeight - pad);\n    const sx = viewportWidth / naturalWidth;\n    const sy = viewportHeight / naturalHeight;\n    scale = clamp(Math.min(sx, sy), minScale, maxScale);\n    tx = (outer.clientWidth - naturalWidth * scale) / 2;\n    ty = Math.max(18, (outer.clientHeight - naturalHeight * scale) / 2);\n    applyTransform();\n  }\n'''
    content = replace_once(content, old_fit, new_fit, "fitToView")

    old_pan = '''      const canPan = event.pointerType === "touch" || event.pointerType === "pen" || spaceHeld || event.button === 1 || event.button === 2;\n      if(canPan){ panStart = {clientX:event.clientX, clientY:event.clientY, tx, ty}; setGrabbing(true); event.preventDefault(); }\n'''
    new_pan = '''      const interactive = event.target.closest(".person, button, input, a, select, textarea, [data-person]");\n      const blankLeftDrag = event.pointerType === "mouse" && event.button === 0 && !interactive;\n      const canPan = event.pointerType === "touch" || event.pointerType === "pen" || blankLeftDrag || spaceHeld || event.button === 1 || event.button === 2;\n      if(canPan){ panStart = {clientX:event.clientX, clientY:event.clientY, tx, ty}; setGrabbing(true); event.preventDefault(); }\n'''
    content = replace_once(content, old_pan, new_pan, "pan logic")

    write(path, content)


def write_upgrade_css() -> None:
    css = r''':root{
  --tree-node-width:154px;
  --tree-node-gap:14px;
  --tree-branch-1:#2f6b4f;
  --tree-branch-2:#c89b3c;
  --tree-branch-3:#5b6ee1;
  --tree-branch-4:#c05a8a;
  --spouse-soft:#fff1f2;
  --spouse-strong:#e11d48;
}

/* Katta shajara xaritasida float asosidagi chiziqlar siljib ketmasligi uchun
   daraxt qatlamini flex sxemaga o‘tkazamiz. HTML rekursiyasi o‘zgarmaydi. */
.tree{
  min-width:max(920px, max-content);
  padding:64px 72px 88px;
  white-space:nowrap;
}

.tree ul{
  position:relative;
  display:flex;
  justify-content:center;
  align-items:flex-start;
  gap:0;
  width:max-content;
  min-width:100%;
  margin:0 auto;
  padding:38px 0 0;
}

.tree > ul{
  padding-top:0;
}

.tree li{
  --branch-color:var(--line-strong);
  position:relative;
  float:none;
  display:flex;
  flex:0 0 auto;
  flex-direction:column;
  align-items:center;
  min-width:calc(var(--tree-node-width) + var(--tree-node-gap) * 2);
  list-style:none;
  text-align:center;
  padding:38px var(--tree-node-gap) 0;
}

.tree li::before,
.tree li::after{
  content:"";
  position:absolute;
  top:0;
  width:50%;
  height:38px;
  border-top:2px solid var(--branch-color);
  opacity:.86;
}

.tree li::before{
  right:50%;
}

.tree li::after{
  right:auto;
  left:50%;
  border-left:2px solid var(--branch-color);
}

.tree li:first-child::before,
.tree li:last-child::after{
  border:0;
}

.tree li:last-child::before{
  border-right:2px solid var(--branch-color);
  border-radius:0 14px 0 0;
}

.tree li:first-child::after{
  border-radius:14px 0 0 0;
}

.tree li:only-child{
  padding-top:0;
}

.tree li:only-child::before,
.tree li:only-child::after,
.tree > ul::before{
  display:none;
}

.tree ul ul::before,
.tree li > ul::before{
  content:"";
  position:absolute;
  top:0;
  left:50%;
  width:0;
  height:38px;
  border-left:2px solid var(--branch-color);
  opacity:.9;
}

.tree > ul > li{--branch-color:var(--tree-branch-1)}
.tree > ul > li > ul > li{--branch-color:var(--tree-branch-2)}
.tree > ul > li > ul > li > ul > li{--branch-color:var(--tree-branch-3)}
.tree > ul > li > ul > li > ul > li > ul > li{--branch-color:var(--tree-branch-4)}
.tree > ul > li > ul > li > ul > li > ul > li > ul > li{--branch-color:var(--tree-branch-1)}

.tree li:nth-child(4n+1){--branch-color:var(--tree-branch-1)}
.tree li:nth-child(4n+2){--branch-color:var(--tree-branch-2)}
.tree li:nth-child(4n+3){--branch-color:var(--tree-branch-3)}
.tree li:nth-child(4n+4){--branch-color:var(--tree-branch-4)}

.union{
  isolation:isolate;
  border-color:rgba(47,107,79,.16);
  background:linear-gradient(180deg,rgba(255,255,255,.92),rgba(255,253,247,.86));
}

.union::before{
  width:34px;
  height:3px;
  border-radius:999px;
  background:linear-gradient(90deg,var(--tree-branch-1),var(--gold));
}

.union:not(.single)::after{
  content:"Nikoh";
  position:absolute;
  left:50%;
  bottom:-11px;
  transform:translateX(-50%);
  z-index:2;
  padding:2px 8px;
  border:1px solid rgba(200,155,60,.34);
  border-radius:999px;
  background:#fffaf0;
  color:#8a641b;
  font-size:10px;
  font-weight:850;
  letter-spacing:.03em;
}

.person{
  min-width:var(--tree-node-width);
  transition:transform .16s ease, box-shadow .16s ease, border-color .16s ease;
}

.person:hover,
.person:focus-visible{
  transform:translateY(-2px);
}

.union:not(.single) .person.partner-2,
.union:not(.single) .person.female{
  border-color:rgba(225,29,72,.32);
  background:linear-gradient(180deg,#fff,var(--spouse-soft));
  box-shadow:0 8px 18px rgba(225,29,72,.08);
}

.union:not(.single) .person.partner-2::after,
.union:not(.single) .person.female::after{
  content:"Turmush o‘rtoq";
  position:absolute;
  top:-9px;
  right:10px;
  padding:2px 7px;
  border-radius:999px;
  background:var(--spouse-strong);
  color:#fff;
  font-size:9px;
  font-weight:850;
  line-height:1.35;
  box-shadow:0 5px 12px rgba(225,29,72,.22);
}

.child-order{
  position:absolute;
  top:-10px;
  left:-10px;
  z-index:3;
  display:grid;
  place-items:center;
  width:28px;
  height:28px;
  border:2px solid #fff;
  border-radius:50%;
  background:linear-gradient(135deg,var(--primary),var(--primary-dark));
  color:#fff;
  font-size:12px;
  font-weight:900;
  box-shadow:0 8px 18px rgba(47,107,79,.22);
}

.pz-outer{
  background:
    linear-gradient(90deg,rgba(47,107,79,.07) 1px,transparent 1px) 0 0/56px 56px,
    linear-gradient(0deg,rgba(47,107,79,.07) 1px,transparent 1px) 0 0/56px 56px,
    radial-gradient(circle at 1px 1px,rgba(200,155,60,.20) 1.1px,transparent 0) 0 0/28px 28px,
    linear-gradient(180deg,#fffdf8,#f4efe4);
}

@media (max-width:640px){
  :root{--tree-node-width:118px;--tree-node-gap:8px}
  .tree{padding:38px 30px 66px;min-width:max(760px, max-content)}
  .tree ul{padding-top:30px}
  .tree li{padding-top:30px}
  .tree li::before,.tree li::after,.tree ul ul::before,.tree li > ul::before{height:30px}
  .child-order{width:24px;height:24px;font-size:11px;top:-8px;left:-8px}
  .union:not(.single)::after{display:none}
  .union:not(.single) .person.partner-2::after,
  .union:not(.single) .person.female::after{display:none}
}
'''
    write("static/genealogy/css/tree-map-upgrades.css", css)


def main() -> None:
    patch_tree_builder()
    patch_tree_template()
    patch_recursive_template()
    patch_tree_js()
    write_upgrade_css()
    print("\nTayyor. Endi: python manage.py check")
    print("Agar serverda ishlatsa: python manage.py collectstatic --noinput")


if __name__ == "__main__":
    main()
