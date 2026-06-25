---
title: "Over"
slug: "over"
description: "Thomas Cremers schrijft korte stukken, herinneringen en observaties op Zemelaar — een plek voor kaf, korrels en losse gedachten."
---

<img src="/thomas-cremers.jpg" alt="Thomas Cremers" loading="lazy" style="width:100%;height:auto;display:block;border-radius:4px;">

<h2 class="over-section-title">Wist je dat</h2>

<ul class="over-list">
<li>ik een hekel aan de kleur blauw heb en over het algemeen in het groen gekleed ga.</li>
<li>ik vrijwilligerswerk doe en daar trotser op ben dan zou moeten.</li>
<li>ik bij de geheime groep hoor die weet waarom de vogeltjes 's ochtends fluiten.</li>
<li>ik me voordoe als werelds, maar er eigenlijk bang voor ben.</li>
<li>ik me als sexier identificeer dan ik eigenlijk ben.</li>
<li>ik schrijf omdat sommige dingen pas bestaan wanneer ze zijn opgeschreven.</li>
<li>ik gelukkig word bij elke nieuwe inschrijving op mijn mailinglijst.</li>
</ul>

<form id="over-signup" class="signup-form" action="https://buttondown.com/api/emails/embed-subscribe/zemelaar" method="post">
  <input class="signup-input" type="email" name="email" placeholder="jouw@email.nl" required>
  <button class="signup-button" type="submit">Inschrijven</button>
  <p class="signup-feedback" aria-live="polite"></p>
</form>
<script>
(function() {
  var form = document.getElementById('over-signup');
  if (!form) return;
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    var btn = form.querySelector('button');
    var feedback = form.querySelector('.signup-feedback');
    btn.disabled = true;
    btn.textContent = '…';
    var data = new FormData();
    data.append('email', form.querySelector('[name="email"]').value);
    fetch(form.action, { method: 'POST', mode: 'no-cors', body: data })
      .then(function() {
        form.innerHTML = '<p class="signup-feedback signup-feedback--ok">Ingeschreven! Je hoort van ons bij een nieuw stuk.</p>';
      })
      .catch(function() {
        feedback.textContent = 'Er ging iets mis. Probeer het opnieuw.';
        btn.disabled = false;
        btn.textContent = 'Inschrijven';
      });
  });
})();
</script>

Naast Zemelaar maak ik fotografie en ander werk op:

- [artistiekportret.nl](https://artistiekportret.nl/)
- [thomascremers.nl](https://thomascremers.nl/)
- [zone.photos](https://zone.photos/)
