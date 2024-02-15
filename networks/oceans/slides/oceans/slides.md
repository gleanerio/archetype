---
theme: seriph
background: https://raw.githubusercontent.com/gleanerio/archetype/master/docs/images/ocean1v2crop.png
class: text-center
highlighter: shikiji
lineNumbers: false
info: |
  ## Slidev Starter Template
  Presentation slides for developers.

  Learn more at [Sli.dev](https://sli.dev)
drawings:
  persist: false
transition: slide-left
title: Structured Data Approaches 
mdc: true
---

# 

ODIS Ocean InfoHub Web Architecture Overview

<div class="pt-12">
  <span @click="$slidev.nav.next" class="px-2 py-1 rounded cursor-pointer" hover="bg-white bg-opacity-10">
    Press Space for next page <carbon:arrow-right class="inline"/>
  </span>
</div>

<div class="abs-br m-6 flex gap-2">
  <button @click="$slidev.nav.openInEditor()" title="Open in Editor" class="text-xl slidev-icon-btn opacity-50 !border-none !hover:text-white">
    <carbon:edit />
  </button>
  <a href="https://github.com/gleanerio/archetype/tree/master/networks/oceans" target="_blank" alt="GitHub" title="Open in GitHub"
    class="text-xl slidev-icon-btn opacity-50 !border-none !hover:text-white">
    <carbon-logo-github />
  </a>
</div>

<!--
The last comment block of each slide will be treated as slide notes. It will be visible and editable in Presenter Mode along with the slide. [Read more in the docs](https://sli.dev/guide/syntax.html#notes)
-->

---
transition: fade-out
---

# Overview

* Foundational Principles
  * web architecture
  * semantics
* KG generation
* SHACL Validation
* Provenance 
* Release graphs concept
* Query Result Products
* System System Integration

---
layout: two-cols
transition: fade-out
---


<template v-slot:default>

# Principles

Web Architecture for Discovery and Access

This is the "classic" approach often put forth as the canonical method for discovery.  
This approach expresses the use of sitemap.xml and optionally robots.txt as 
documents published to provide guidance for machine indexing.  

<img src="/images/discovery.svg" width="300" class=" rounded shadow" />

* The Robots Exclusion Protocol  (robots.txt) https://www.rfc-editor.org/rfc/rfc9309 and 
* Sitemap.xml https://www.sitemaps.org/protocol.html. 


</template>

<template v-slot:right>


 _OIH Implementation_

<img src="/images/odiscat.svg" width="300" class=" rounded shadow" />

The OIH approach used ODIS Catalogue as a community register for resources which 
are then exported to an operational list for indexing.

This is because OIH is a curated list of resources and not a crawl.

</template>


---
layout: two-cols
transition: fade-out
---

<template v-slot:default>

# Schema

schema.org

SOSO

GeoSPARQL

</template>

<template v-slot:right>

# Thematic Types

- Dataset
- Courses
- Experts and Institutions
- Vessels

</template>


---
transition: fade-out
---
#  OIH Knowledge Graph



---
transition: fade-out
---
# Validation
   
stuff here


---
transition: fade-out
---
# Provenance 
   
stuff here


---
transition: fade-out
---
# Release Graphs

describe the release and publishing approaches being implemented

---
transition: fade-out
---
# Product files

describe the query driven product files

---
transition: fade-out
---
# System System Integration

WIS2 et al and the connection with the product files

* ROA
* standards driven

---
transition: fade-out
---
# Conclusion and final thoughts
   
stuff here
