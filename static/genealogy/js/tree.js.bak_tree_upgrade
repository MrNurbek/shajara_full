(function(){
  "use strict";

  const outer = document.getElementById("pz-outer");
  const inner = document.getElementById("pz-inner");
  const scaleEl = document.getElementById("pz-scale");
  const btnFit = document.getElementById("pz-fit");
  const btnReset = document.getElementById("pz-reset");
  const btnZoomIn = document.getElementById("pz-zoom-in");
  const btnZoomOut = document.getElementById("pz-zoom-out");
  const searchInput = document.getElementById("person-search");
  const searchResults = document.getElementById("search-results");
  const canEdit = Boolean(window.SHJ_CAN_EDIT);

  const modalBg = document.getElementById("person-modal-bg");
  const modalContent = document.getElementById("person-modal-content");
  const modalClose = document.getElementById("person-close");
  const formBg = document.getElementById("form-modal-bg");
  const formContent = document.getElementById("form-modal-content");
  const formClose = document.getElementById("form-close");

  const lightboxBg = document.getElementById("image-lightbox-bg");
  const lightboxImage = document.getElementById("image-lightbox-img");
  const lightboxCaption = document.getElementById("image-lightbox-caption");
  const lightboxClose = document.getElementById("image-lightbox-close");
  const lightboxOpenOriginal = document.getElementById("image-lightbox-open-original");

  if(!outer || !inner) return;

  let scale = 1;
  let tx = 40;
  let ty = 40;
  const minScale = 0.25;
  const maxScale = 3;
  const pointers = new Map();
  let panStart = null;
  let pinchStart = null;
  let spaceHeld = false;
  let suppressClickUntil = 0;
  let currentPerson = null;

  function clamp(value, min, max){ return Math.max(min, Math.min(max, value)); }
  function applyTransform(){ inner.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`; if(scaleEl) scaleEl.textContent = `${Math.round(scale * 100)}%`; }
  function setGrabbing(active){ outer.classList.toggle("grabbing", active); }
  function outerPoint(clientX, clientY){ const rect = outer.getBoundingClientRect(); return {x: clientX - rect.left, y: clientY - rect.top}; }
  function zoomAt(nextScale, clientX, clientY){
    const point = outerPoint(clientX, clientY);
    const contentX = (point.x - tx) / scale;
    const contentY = (point.y - ty) / scale;
    scale = clamp(nextScale, minScale, maxScale);
    tx = point.x - contentX * scale;
    ty = point.y - contentY * scale;
    applyTransform();
  }
  function fitToView(){
    const tree = inner.querySelector(".tree"); if(!tree) return;
    const oldTransform = inner.style.transform;
    inner.style.transform = "translate(0px, 0px) scale(1)";
    const natural = tree.getBoundingClientRect();
    inner.style.transform = oldTransform;
    const pad = outer.clientWidth < 600 ? 24 : 70;
    const sx = (outer.clientWidth - pad) / Math.max(1, natural.width);
    const sy = (outer.clientHeight - pad) / Math.max(1, natural.height);
    scale = clamp(Math.min(sx, sy), minScale, maxScale);
    tx = (outer.clientWidth - natural.width * scale) / 2;
    ty = (outer.clientHeight - natural.height * scale) / 2;
    applyTransform();
  }
  function resetView(){ scale = 1; tx = 40; ty = 40; applyTransform(); }
  function distance(a,b){ return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY); }
  function midpoint(a,b){ return {clientX:(a.clientX + b.clientX)/2, clientY:(a.clientY + b.clientY)/2}; }

  outer.addEventListener("pointerdown", (event) => {
    pointers.set(event.pointerId, event);
    try{ outer.setPointerCapture(event.pointerId); }catch(_e){}
    if(pointers.size === 1){
      const canPan = event.pointerType === "touch" || event.pointerType === "pen" || spaceHeld || event.button === 1 || event.button === 2;
      if(canPan){ panStart = {clientX:event.clientX, clientY:event.clientY, tx, ty}; setGrabbing(true); event.preventDefault(); }
    } else if(pointers.size === 2){
      const [a,b] = [...pointers.values()]; const mid = midpoint(a,b);
      pinchStart = {distance:distance(a,b), scale, tx, ty, mid}; panStart = null; setGrabbing(true); event.preventDefault();
    }
  }, {passive:false});

  outer.addEventListener("pointermove", (event) => {
    if(!pointers.has(event.pointerId)) return;
    pointers.set(event.pointerId, event);
    if(pointers.size === 2 && pinchStart){
      const [a,b] = [...pointers.values()]; const nextMid = midpoint(a,b);
      const ratio = distance(a,b) / Math.max(1, pinchStart.distance);
      const nextScale = clamp(pinchStart.scale * ratio, minScale, maxScale);
      const startPoint = outerPoint(pinchStart.mid.clientX, pinchStart.mid.clientY);
      const contentX = (startPoint.x - pinchStart.tx) / pinchStart.scale;
      const contentY = (startPoint.y - pinchStart.ty) / pinchStart.scale;
      const currentPoint = outerPoint(nextMid.clientX, nextMid.clientY);
      scale = nextScale; tx = currentPoint.x - contentX * scale; ty = currentPoint.y - contentY * scale;
      suppressClickUntil = Date.now() + 280; applyTransform(); event.preventDefault(); return;
    }
    if(panStart){
      const dx = event.clientX - panStart.clientX; const dy = event.clientY - panStart.clientY;
      if(Math.abs(dx) + Math.abs(dy) > 4) suppressClickUntil = Date.now() + 280;
      tx = panStart.tx + dx; ty = panStart.ty + dy; applyTransform(); event.preventDefault();
    }
  }, {passive:false});
  function pointerEnd(event){
    pointers.delete(event.pointerId);
    if(event.pointerId != null && outer.hasPointerCapture && outer.hasPointerCapture(event.pointerId)){ try{ outer.releasePointerCapture(event.pointerId); }catch(_e){} }
    if(pointers.size < 2) pinchStart = null;
    if(pointers.size === 0){ panStart = null; setGrabbing(false); }
  }
  outer.addEventListener("pointerup", pointerEnd); outer.addEventListener("pointercancel", pointerEnd); outer.addEventListener("contextmenu", event => event.preventDefault());
  outer.addEventListener("wheel", (event) => { if(!(event.ctrlKey || event.metaKey)) return; event.preventDefault(); zoomAt(scale + (event.deltaY > 0 ? -0.12 : 0.12), event.clientX, event.clientY); }, {passive:false});
  document.addEventListener("keydown", event => { if(event.code === "Space") spaceHeld = true; });
  document.addEventListener("keyup", event => { if(event.code === "Space") spaceHeld = false; });
  btnFit && btnFit.addEventListener("click", fitToView); btnReset && btnReset.addEventListener("click", resetView);
  btnZoomIn && btnZoomIn.addEventListener("click", () => { const rect = outer.getBoundingClientRect(); zoomAt(scale + 0.12, rect.left + outer.clientWidth/2, rect.top + outer.clientHeight/2); });
  btnZoomOut && btnZoomOut.addEventListener("click", () => { const rect = outer.getBoundingClientRect(); zoomAt(scale - 0.12, rect.left + outer.clientWidth/2, rect.top + outer.clientHeight/2); });
  window.addEventListener("load", () => setTimeout(fitToView, 80)); window.addEventListener("resize", () => setTimeout(fitToView, 120)); applyTransform();

  function esc(value){ return String(value ?? "").replace(/[&<>'"]/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#039;","\"":"&quot;"}[ch])); }
  function attr(value){ return esc(value).replace(/`/g, "&#096;"); }
  function yearsText(person){ const b = person.birth_year || (person.birth_date ? String(person.birth_date).slice(0,4) : ""); const d = person.death_year || (person.death_date ? String(person.death_date).slice(0,4) : ""); return `${b}${b || d ? "–" : ""}${d}`; }
  function csrfToken(){ const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/); return match ? decodeURIComponent(match[1]) : ""; }

  function openModal(html){ if(!modalBg || !modalContent) return; modalContent.innerHTML = html; modalBg.classList.add("open"); modalBg.setAttribute("aria-hidden", "false"); if(modalClose) modalClose.focus(); document.addEventListener("keydown", closeOnEsc); }
  function closeModal(){ if(!modalBg || !modalContent) return; modalBg.classList.remove("open"); modalBg.setAttribute("aria-hidden", "true"); modalContent.innerHTML = ""; document.removeEventListener("keydown", closeOnEsc); }
  function openForm(html){ if(!formBg || !formContent) return; formContent.innerHTML = html; formBg.classList.add("open"); formBg.setAttribute("aria-hidden", "false"); if(formClose) formClose.focus(); document.addEventListener("keydown", closeOnEsc); }
  function closeForm(){ if(!formBg || !formContent) return; formBg.classList.remove("open"); formBg.setAttribute("aria-hidden", "true"); formContent.innerHTML = ""; document.removeEventListener("keydown", closeOnEsc); }
  function closeOnEsc(event){ if(event.key === "Escape"){ if(lightboxBg && lightboxBg.classList.contains("open")) closeLightbox(); else if(formBg && formBg.classList.contains("open")) closeForm(); else closeModal(); } }
  modalClose && modalClose.addEventListener("click", closeModal); modalBg && modalBg.addEventListener("click", event => { if(event.target === modalBg) closeModal(); });
  formClose && formClose.addEventListener("click", closeForm); formBg && formBg.addEventListener("click", event => { if(event.target === formBg) closeForm(); });

  function openLightbox(src, caption){ if(!lightboxBg || !lightboxImage) return; lightboxImage.src = src; lightboxImage.alt = caption || "Katta rasm"; if(lightboxCaption) lightboxCaption.textContent = caption || ""; if(lightboxOpenOriginal) lightboxOpenOriginal.href = src; lightboxBg.classList.add("open"); lightboxBg.setAttribute("aria-hidden", "false"); if(lightboxClose) lightboxClose.focus(); document.addEventListener("keydown", closeOnEsc); }
  function closeLightbox(){ if(!lightboxBg || !lightboxImage) return; lightboxBg.classList.remove("open"); lightboxBg.setAttribute("aria-hidden", "true"); lightboxImage.removeAttribute("src"); if(lightboxCaption) lightboxCaption.textContent = ""; if(lightboxOpenOriginal) lightboxOpenOriginal.removeAttribute("href"); if(!modalBg?.classList.contains("open") && !formBg?.classList.contains("open")) document.removeEventListener("keydown", closeOnEsc); }
  lightboxClose && lightboxClose.addEventListener("click", closeLightbox); lightboxBg && lightboxBg.addEventListener("click", event => { if(event.target === lightboxBg) closeLightbox(); });

  async function loadPerson(id){
    openModal('<div class="spinner" aria-label="Yuklanmoqda"></div>');
    try{ const response = await fetch(`/api/people/${encodeURIComponent(id)}/`); if(!response.ok) throw new Error("Request failed"); currentPerson = await response.json(); modalContent.innerHTML = renderPerson(currentPerson); }
    catch(error){ console.error(error); modalContent.innerHTML = '<p class="message error">Ma’lumotni olishda xatolik yuz berdi.</p>'; }
  }
  document.addEventListener("click", event => { const imageButton = event.target.closest("[data-image-full]"); if(!imageButton) return; event.preventDefault(); event.stopPropagation(); openLightbox(imageButton.dataset.imageFull, imageButton.dataset.imageCaption || ""); });
  document.addEventListener("click", event => { const personNode = event.target.closest(".person[data-id]"); if(!personNode) return; if(Date.now() < suppressClickUntil){ event.preventDefault(); return; } loadPerson(personNode.dataset.id); });
  document.addEventListener("click", event => { const chipNode = event.target.closest("[data-person]"); if(!chipNode) return; if(chipNode.classList.contains("search-item")) searchResults.hidden = true; loadPerson(chipNode.dataset.person); });

  function chip(person){ if(!person) return ""; const years = yearsText(person); return `<button type="button" class="chip chip-person" data-person="${attr(person.id)}" title="Profilni ochish">${esc(person.name)}${years ? " " + esc(years) : ""}</button>`; }
  function imageButton(src, caption, className, alt){ if(!src) return ""; return `<button class="photo-button ${className || ""}" type="button" data-image-full="${attr(src)}" data-image-caption="${attr(caption || alt || "")}" title="Rasmni kattalashtirib ko‘rish"><img src="${attr(src)}" alt="${attr(alt || caption || "Rasm")}" loading="lazy"><span class="photo-zoom-hint">Kattalashtirish</span></button>`; }
  function renderPerson(p){
    const gender = p.gender === "M" ? "Erkak" : p.gender === "F" ? "Ayol" : "Noma’lum";
    const mainPhoto = imageButton(p.primary_photo_url, p.full_name, "profile-photo-button", p.full_name);
    const photos = (p.photos || []).map(photo => `<figure>${imageButton(photo.image_url, photo.caption || p.full_name, "gallery-photo-button", photo.caption || p.full_name)}${photo.caption ? `<figcaption class="muted">${esc(photo.caption)}</figcaption>` : ""}</figure>`).join("");
    const addresses = (p.addresses || []).map(address => { const line = [address.country, address.region, address.district, address.city, address.street, address.house].filter(Boolean).map(esc).join(", "); return `<li>${line}${address.postal_code ? " (" + esc(address.postal_code) + ")" : ""}${address.description ? " — <span class='muted'>" + esc(address.description) + "</span>" : ""}</li>`; }).join("");
    const spouses = (p.spouses || []).map(chip).join(" ");
    const marriages = (p.marriages || []).map(m => `<li>${(m.spouses || []).map(chip).join(" ")} <span class="muted">${[m.start_date, m.end_date ? "— " + m.end_date : "", m.location_text].filter(Boolean).map(esc).join(" ")}</span></li>`).join("");
    const parents = (p.parents || []).map(item => `<li>${chip(item.parent)}${item.other_parent ? " + " + chip(item.other_parent) : ""} <span class="muted">${item.via === "marriage" ? "nikoh orqali" : "yolg‘iz ota/ona"}</span></li>`).join("");
    const children = (p.children || []).map(item => `<li>${chip(item.child)}${item.other_parent ? " + " + chip(item.other_parent) : ""} <span class="muted">${item.via === "marriage" ? "nikoh orqali" : "yolg‘iz ota/ona"}</span></li>`).join("");
    const actions = canEdit ? `<div class="profile-actions"><button class="action-btn primary" data-action="edit-person">Tahrirlash</button><button class="action-btn" data-action="add-child">Farzand bog‘lash</button><button class="action-btn" data-action="add-spouse">Turmush o‘rtoq qo‘shish</button></div>` : "";
    return `<h2 id="person-title">${esc(p.full_name)}</h2><div class="muted">${esc(yearsText(p))}</div>${actions}<div class="profile-head">${mainPhoto || '<div class="profile-photo-placeholder">Rasm yo‘q</div>'}<div class="profile-facts"><span class="chip">${esc(gender)}</span>${p.age != null ? `<span class="chip">Yoshi: ${esc(p.age)}</span>` : ""}${p.occupation ? `<span class="chip">${esc(p.occupation)}</span>` : ""}${p.birth_place ? `<span class="chip">Tug‘ilgan joy: ${esc(p.birth_place)}</span>` : ""}${p.death_place ? `<span class="chip">Vafot joyi: ${esc(p.death_place)}</span>` : ""}</div></div>${p.biography ? `<h3>Biografiya</h3><p class="bio-text">${esc(p.biography)}</p>` : ""}${spouses ? `<h3>Turmush o‘rtog‘i</h3><p>${spouses}</p>` : ""}${marriages ? `<h3>Nikohlar</h3><ul>${marriages}</ul>` : ""}${parents ? `<h3>Ota-onalari</h3><ul>${parents}</ul>` : ""}${children ? `<h3>Farzandlari</h3><ul>${children}</ul>` : ""}${addresses ? `<h3>Manzillar</h3><ul>${addresses}</ul>` : ""}${photos ? `<h3>Galereya</h3><div class="gallery">${photos}</div>` : ""}`;
  }

  function personForm(p){
    p = p || {};
    const title = p.id ? "Shaxsni tahrirlash" : "Yangi shaxs qo‘shish";
    return `<h2 id="form-title">${title}</h2><form id="person-form" class="form-grid" enctype="multipart/form-data" data-id="${attr(p.id || "")}"><div class="field"><label>Ism</label><input name="first_name" required value="${attr(p.full_name ? "" : (p.first_name || ""))}" placeholder="Ism"></div><div class="field"><label>Familiya</label><input name="last_name" value="${attr(p.last_name || "")}" placeholder="Familiya"></div><div class="field"><label>Otasining ismi</label><input name="middle_name" value="${attr(p.middle_name || "")}" placeholder="Otasining ismi"></div><div class="field"><label>Jinsi</label><select name="gender"><option value="U">Noma’lum</option><option value="M" ${p.gender === "M" ? "selected" : ""}>Erkak</option><option value="F" ${p.gender === "F" ? "selected" : ""}>Ayol</option></select></div><div class="field"><label>Tug‘ilgan sana</label><input type="date" name="birth_date" value="${attr(p.birth_date || "")}"></div><div class="field"><label>Vafot sanasi</label><input type="date" name="death_date" value="${attr(p.death_date || "")}"></div><div class="field"><label>Tug‘ilgan joy</label><input name="birth_place" value="${attr(p.birth_place || "")}"></div><div class="field"><label>Kasbi</label><input name="occupation" value="${attr(p.occupation || "")}"></div><div class="field full"><label>To‘liq ism qo‘lda</label><input name="full_name_custom" value="${attr(p.full_name_custom || "")}" placeholder="Ixtiyoriy"></div><div class="field full"><label>Biografiya</label><textarea name="biography">${esc(p.biography || "")}</textarea></div><div class="field full"><label>Asosiy rasm</label><input type="file" name="primary_photo" accept="image/*"></div><div class="field full"><div id="form-message"></div></div><div class="form-actions field full"><button type="button" data-close-form>Bekor qilish</button><button type="submit">Saqlash</button></div></form>`;
  }
  function relationForm(type){
    const isSpouse = type === "spouse";
    return `<h2 id="form-title">${isSpouse ? "Turmush o‘rtoq qo‘shish" : "Farzand bog‘lash"}</h2><form id="relation-form" class="form-grid" data-type="${type}"><div class="field full"><label>${isSpouse ? "Turmush o‘rtoq" : "Farzand"} ID</label><input name="target" required placeholder="Qidiruvdan shaxs ID ni tanlash o‘rniga admin orqali tanlash ham mumkin"></div><div class="field"><label>Sana</label><input type="date" name="start_date"></div><div class="field"><label>Joy</label><input name="location_text"></div><div class="field full"><label>Izoh</label><textarea name="notes"></textarea></div><div class="field full"><div id="form-message"></div></div><div class="form-actions field full"><button type="button" data-close-form>Bekor qilish</button><button type="submit">Saqlash</button></div></form><p class="muted">Eslatma: ID ni qidiruv natijasidagi shaxs profilidan olish mumkin. Bunday bog‘lanishlar faqat boshqaruv rejimida saqlanadi.</p>`;
  }
  document.getElementById("add-person-btn")?.addEventListener("click", () => openForm(personForm()));
  document.addEventListener("click", event => { if(event.target.closest("[data-close-form]")) closeForm(); const action = event.target.closest("[data-action]")?.dataset.action; if(!action || !currentPerson) return; if(action === "edit-person") openForm(personForm(currentPerson)); if(action === "add-child") openForm(relationForm("child")); if(action === "add-spouse") openForm(relationForm("spouse")); });
  document.addEventListener("submit", async event => {
    if(event.target.id === "person-form"){
      event.preventDefault();
      const form = event.target; const msg = form.querySelector("#form-message"); const id = form.dataset.id; const data = new FormData(form);
      for(const [key,value] of [...data.entries()]){ if(value === "") data.delete(key); }
      try{ const response = await fetch(id ? `/api/people/${encodeURIComponent(id)}/update/` : "/api/people/create/", {method:"POST", body:data, headers:{"X-CSRFToken":csrfToken()}}); if(!response.ok){ const text = await response.text(); throw new Error(text); } msg.innerHTML = '<div class="message ok">Saqlandi. Sahifa yangilanmoqda...</div>'; setTimeout(() => location.reload(), 700); }
      catch(error){ msg.innerHTML = `<div class="message error">Xato: ${esc(error.message).slice(0,500)}</div>`; }
    }
    if(event.target.id === "relation-form" && currentPerson){
      event.preventDefault();
      const form = event.target; const msg = form.querySelector("#form-message"); const type = form.dataset.type; const target = form.target.value.trim();
      const payload = type === "spouse" ? {spouse1: currentPerson.id, spouse2: target, start_date: form.start_date.value || null, location_text: form.location_text.value, notes: form.notes.value} : {parent: currentPerson.id, child: target, notes: form.notes.value};
      const url = type === "spouse" ? "/api/marriages/create/" : "/api/parent-child/create/";
      try{ const response = await fetch(url, {method:"POST", headers:{"Content-Type":"application/json", "X-CSRFToken":csrfToken()}, body:JSON.stringify(payload)}); if(!response.ok){ const text = await response.text(); throw new Error(text); } msg.innerHTML = '<div class="message ok">Bog‘lanish saqlandi. Sahifa yangilanmoqda...</div>'; setTimeout(() => location.reload(), 700); }
      catch(error){ msg.innerHTML = `<div class="message error">Xato: ${esc(error.message).slice(0,500)}</div>`; }
    }
  });

  let searchTimer = null;
  async function performSearch(){
    const query = searchInput.value.trim();
    if(!query){ searchResults.hidden = true; searchResults.innerHTML = ""; return; }
    try{ const response = await fetch(`/api/people/?q=${encodeURIComponent(query)}`); if(!response.ok) throw new Error("Search failed"); const data = await response.json(); searchResults.hidden = false; searchResults.innerHTML = data.length ? data.map(person => `<button class="search-item" type="button" data-person="${attr(person.id)}">${person.primary_photo_url ? `<img src="${attr(person.primary_photo_url)}" alt="">` : `<span class="search-avatar-fallback">${person.gender === "M" ? "E" : person.gender === "F" ? "A" : "?"}</span>`}<span><span class="search-item-name">${esc(person.full_name)}</span><br><span class="search-item-meta">${esc(yearsText(person))}${canEdit ? " · ID: " + esc(person.id) : ""}</span></span></button>`).join("") : '<div class="search-item-meta search-empty">Natija topilmadi.</div>'; }
    catch(error){ console.error(error); searchResults.hidden = false; searchResults.innerHTML = '<div class="search-item-meta search-empty">Qidirishda xatolik.</div>'; }
  }
  if(searchInput && searchResults){ searchInput.addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(performSearch, 250); }); searchInput.addEventListener("keydown", event => { if(event.key === "Escape"){ searchResults.hidden = true; searchResults.innerHTML = ""; } }); document.addEventListener("click", event => { if(!event.target.closest(".search-box")) searchResults.hidden = true; }); }

  const fullscreenButtons = Array.from(document.querySelectorAll("[data-tree-fullscreen]"));
  const treeCard = document.querySelector(".tree-card");
  const fullscreenTarget = document.getElementById("tree-map") || treeCard;
  const fullscreenHost = document.documentElement;

  function getFullscreenElement(){
    return document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement || null;
  }

  function canNativeFullscreen(){
    return !!(fullscreenHost && (fullscreenHost.requestFullscreen || fullscreenHost.webkitRequestFullscreen || fullscreenHost.msRequestFullscreen));
  }

  function syncFullscreenClasses(){
    const nativeActive = !!getFullscreenElement();
    document.body.classList.toggle("tree-fullscreen-native", nativeActive);
    if(!nativeActive) document.body.classList.remove("tree-fullscreen-native");
    return nativeActive || document.body.classList.contains("tree-fullscreen-fallback");
  }

  function updateFullscreenText(){
    const active = syncFullscreenClasses();
    fullscreenButtons.forEach((btn) => {
      btn.textContent = active ? "✕ Chiqish" : (btn.classList.contains("toolbar-fullscreen") ? "⛶ Xaritani kattalashtirish" : "⛶ To‘liq ekran");
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
    if(active) setTimeout(fitToView, 120);
  }

  async function enterFullscreen(){
    if(!fullscreenTarget) return;
    if(canNativeFullscreen()){
      /* Butun hujjat fullscreen bo‘ladi. Shunda profil modal, form modal va lightbox
         ham fullscreen top-layer ichida qoladi; ular xarita ostida yashirinib qolmaydi. */
      if(fullscreenHost.requestFullscreen) await fullscreenHost.requestFullscreen();
      else if(fullscreenHost.webkitRequestFullscreen) fullscreenHost.webkitRequestFullscreen();
      else if(fullscreenHost.msRequestFullscreen) fullscreenHost.msRequestFullscreen();
      document.body.classList.add("tree-fullscreen-native");
    }else{
      document.body.classList.add("tree-fullscreen-fallback");
    }
  }

  async function exitFullscreen(){
    if(getFullscreenElement()){
      if(document.exitFullscreen) await document.exitFullscreen();
      else if(document.webkitExitFullscreen) document.webkitExitFullscreen();
      else if(document.msExitFullscreen) document.msExitFullscreen();
    }
    document.body.classList.remove("tree-fullscreen-native", "tree-fullscreen-fallback");
  }

  if(fullscreenButtons.length && fullscreenTarget){
    fullscreenButtons.forEach((button) => {
      button.addEventListener("click", async () => {
        try{
          if(getFullscreenElement() || document.body.classList.contains("tree-fullscreen-fallback")){ await exitFullscreen(); }
          else{ await enterFullscreen(); }
        }catch(e){
          console.warn("Fullscreen ishlamadi, fallback rejim yoqildi", e);
          document.body.classList.remove("tree-fullscreen-native");
          document.body.classList.toggle("tree-fullscreen-fallback");
        }
        updateFullscreenText();
      });
    });
    ["fullscreenchange", "webkitfullscreenchange", "MSFullscreenChange"].forEach((eventName) => document.addEventListener(eventName, updateFullscreenText));
    document.addEventListener("keydown", (event) => {
      if(event.key === "Escape" && document.body.classList.contains("tree-fullscreen-fallback")){
        document.body.classList.remove("tree-fullscreen-fallback");
        updateFullscreenText();
      }
    });
    updateFullscreenText();
  }
})();
