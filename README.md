# Sjursen Digital Monorepo

Welcome to the official monorepo for **Sjursen Digital**, a professional software development and digital consulting company registered in Norway. This repository serves as the central hub for our open-source tools, commercial SaaS products, and custom digital infrastructure.

## Our Core Products

### 🛠️ Obsero
**Obsero** (from Latin *observare* — to observe, protect, and watch over) is an ultra-lightweight, self-hosted safety, compliance, and asset telemetry platform. 

It is designed to solve the physical-digital loop for workshops, makerspaces, vocational schools, and construction sites where tracking equipment, verifying user certifications, and logging safety events are critical.

- **Mobile-First / PWA**: Built optimized for smartphones with hardware-accelerated camera QR-code scanning.
- **Self-Hosted & Private**: Packaged as a single lightweight Docker container running an embedded SQLite database. Extremely low overhead, running perfectly on anything from a Synology NAS to a $4/month VPS.
- **Safety & Certification**: Restrict machinery usage (e.g., CNC routers, electric saws) to certified personnel by scanning QR codes, logging runtime diagnostics, safety checklists, and telemetry datapoints.
- **Physical-Digital Loop**: Integrated with durable, weatherproof pre-printed QR sticker sheets from Sjursen Digital for instant asset binding.

---

## Repository Structure

```text
sjursen-digital/
├── assets/
│   └── logo/             # Brand identity vectors (continuous ribbon SD mark)
├── services/             # Backend services & APIs
└── applications/         # Frontend web applications & PWAs
```

## Branding & Assets

Our visual identity centers around a modern, geometric continuous ribbon forming an **S** and a **D** in a single, balanced stroke:

- **Primary Logo**: Located at `assets/logo/sjursen-digital.svg`
- **Lockup Logo (Icon + Wordmark)**: Located at `assets/logo/sjursen-digital-lockup.svg`

---

*Engineered by Noah Sebastian Sjursen · Bergen, Norway*  
*Bestått meget godt (Excellent) — Norwegian Trade Certificate in IT Development*
