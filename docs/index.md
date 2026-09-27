---
layout: default
title: Plastic Signal Weekly
---

<section class="signal-hero">
  <div class="eyebrow"><span class="live-dot"></span> WEEKLY MATERIAL INTELLIGENCE</div>
  <h1>See the shift<br><em>before it scales.</em></h1>
  <p class="hero-copy">A decision brief for people building the next generation of plastic products. Markets, materials, regulation and research—filtered for consequence, not volume.</p>
  <div class="hero-actions">
    <a class="primary-action" href="#latest">Read the latest issue <span>→</span></a>
    <a class="text-action" href="{{ '/feed-en.xml' | relative_url }}">Subscribe via RSS</a>
  </div>
  <div class="edition-stamp"><strong>WEEK 39</strong><span>8 intelligence pillars</span><span>~7 min read</span></div>
</section>

<section class="signal-bar" aria-label="Newsletter promise">
  <span>NO HYPE</span><i></i><span>SOURCE-LED</span><i></i><span>DECISION-READY</span><i></i><span>EVERY MONDAY</span>
</section>

<section class="editorial-intro">
  <div class="section-number">01 / THE BRIEF</div>
  <div>
    <h2>Not more plastics news.<br>Better signals.</h2>
    <p>Every item answers four questions: <strong>What changed?</strong> Why does it matter? What is the practical implication? What should a team examine next?</p>
  </div>
</section>

<section class="pillar-section">
  <div class="section-number">02 / SIGNAL MAP</div>
  <div class="pillar-grid">
    <article><b>01</b><h3>Market &<br>Business</h3><p>Demand, customer value, design and differentiation.</p></article>
    <article><b>02</b><h3>Sustainable<br>Materials</h3><p>PCR economics, bio-based feedstocks and efficiency.</p></article>
    <article><b>03</b><h3>Recycling<br>Technology</h3><p>Mechanical, chemical, dissolution and sorting.</p></article>
    <article><b>04</b><h3>Material<br>Performance</h3><p>Food contact, durability, additives and qualification.</p></article>
    <article><b>05</b><h3>Future<br>Materials</h3><p>AI discovery, smart polymers and renewable carbon.</p></article>
    <article><b>06</b><h3>Supply &<br>Feedstocks</h3><p>Pricing, availability, traceability and supplier moves.</p></article>
    <article><b>07</b><h3>Regulation &<br>Compliance</h3><p>PPWR, ESPR, REACH, PFAS, EPR and standards.</p></article>
    <article><b>08</b><h3>Research &<br>Patents</h3><p>Evidence that can survive the jump from lab to line.</p></article>
  </div>
</section>

<section id="latest" class="latest-section">
  <div class="section-number">03 / LATEST</div>
  <div class="latest-header"><h2>The weekly file</h2><p>Markets to molecules, in one scan.</p></div>
  <div class="issue-list">
    {% assign plastic_posts = site.posts | where: "newsletter", "plastics" %}
    {% for post in plastic_posts limit:12 %}
      <a class="issue-row" href="{{ post.url | relative_url }}">
        <span class="issue-date">{{ post.date | date: "%d %b %Y" }}</span>
        <span class="issue-title">{{ post.title }}</span>
        <span class="issue-arrow">↗</span>
      </a>
    {% else %}
      <div class="issue-empty"><strong>First issue is being assembled.</strong><span>The automation is configured and ready for its first weekly run.</span></div>
    {% endfor %}
  </div>
</section>

<section class="method-section">
  <div class="section-number">04 / METHOD</div>
  <div class="method-copy"><h2>Forty signals in.<br>Five decisions out.</h2></div>
  <ol>
    <li><b>01</b><span><strong>Collect</strong>News, papers, regulatory sources and supplier announcements.</span></li>
    <li><b>02</b><span><strong>Challenge</strong>Separate evidence from claims, pilots from commercial reality.</span></li>
    <li><b>03</b><span><strong>Translate</strong>Connect each signal to cost, performance, compliance or growth.</span></li>
    <li><b>04</b><span><strong>Act</strong>Close with one proportionate next step for the relevant team.</span></li>
  </ol>
</section>

<footer class="signal-footer"><span>PLASTIC SIGNAL WEEKLY</span><span>Built for materials decisions, not attention.</span></footer>
