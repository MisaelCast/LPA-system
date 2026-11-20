<template>
  <section class="hero" aria-labelledby="hero-supervisor-title">
    <div class="hero-inner">
      <div class="hero-copy">
        <h1 id="hero-supervisor-title" class="hero-title">
          La calidad se audita<br />
          en cada capa<span class="hero-title-dot">.</span>
        </h1>

        <p class="hero-lede">
          LPA System conecta las auditorías de las tres capas con la evidencia,
          el responsable y el cierre de cada hallazgo.
        </p>

        <ul class="hero-badges" aria-label="Estado de la plataforma">
          <li class="hero-badge hero-badge--live">
            <span class="badge-dot" aria-hidden="true"></span>
            En operación
          </li>
          <li class="hero-badge hero-badge--layers">
            <span class="badge-icon" aria-hidden="true">
              <svg viewBox="0 0 16 16">
                <path d="M8 2.1 14 5 8 7.9 2 5 8 2.1Z" />
                <path d="m2 8 6 2.9L14 8" />
                <path d="m2 11 6 2.9L14 11" />
              </svg>
            </span>
            3 capas de auditoría
          </li>
          <li class="hero-badge hero-badge--trace">
            <span class="badge-icon" aria-hidden="true">
              <svg viewBox="0 0 16 16">
                <path d="M8 1.9 13 3.7v3.7c0 3.1-2 5.3-5 6.7-3-1.4-5-3.6-5-6.7V3.7L8 1.9Z" />
                <path d="m5.9 7.9 1.4 1.4 2.9-3" />
              </svg>
            </span>
            Evidencia trazable
          </li>
        </ul>

        <div class="hero-folio">
          <span class="folio-mark">LPA</span>
          <span class="folio-divider" aria-hidden="true"></span>
          <span class="folio-label">Layer Process Audit</span>
          <span class="folio-sep" aria-hidden="true">·</span>
          <span class="folio-meta">Ensamble Final y Pulido</span>
        </div>
      </div>

      <figure class="lpa-map">
        <div class="map-body">
          <div class="strata">
            <div class="stratum stratum--3">
              <span class="stratum-code">L3</span>
              <div class="stratum-copy">
                <p class="stratum-title">Gerente</p>
                <p class="stratum-desc">Audita la eficacia del sistema</p>
              </div>
              <span class="stratum-state stratum-state--system">
                <span class="state-dot" aria-hidden="true"></span>
                Sistema
              </span>
            </div>

            <div class="stratum stratum--2">
              <span class="stratum-code">L2</span>
              <div class="stratum-copy">
                <p class="stratum-title">Supervisor</p>
                <p class="stratum-desc">Audita la ejecución y el seguimiento</p>
              </div>
              <span class="stratum-state stratum-state--execution">
                <span class="state-dot" aria-hidden="true"></span>
                Ejecución
              </span>
            </div>

            <div class="stratum stratum--1">
              <span class="stratum-code">L1</span>
              <div class="stratum-copy">
                <p class="stratum-title">Auditor</p>
                <p class="stratum-desc">Audita el proceso en piso</p>
              </div>
              <span class="stratum-state stratum-state--process">
                <span class="state-dot" aria-hidden="true"></span>
                Proceso
              </span>
            </div>
          </div>

          <svg
            class="map-loop"
            viewBox="0 0 64 100"
            preserveAspectRatio="none"
            aria-hidden="true"
            focusable="false"
          >
            <defs>
              <linearGradient
                id="hero-cycle-gradient"
                x1="0"
                y1="1"
                x2="0"
                y2="0"
              >
                <stop offset="0" stop-color="#ffc27a" />
                <stop offset="0.5" stop-color="#9db6ff" />
                <stop offset="1" stop-color="#67e8bd" />
              </linearGradient>
            </defs>
            <path
              class="loop-track"
              d="M2 84 H26 C58 84 58 16 26 16 H2"
            />
            <path
              class="loop-color"
              d="M2 84 H26 C58 84 58 16 26 16 H2"
            />
            <path
              class="loop-branch"
              d="M0 50 H60"
            />
            <path
              class="loop-light"
              d="M2 84 H26 C58 84 58 16 26 16 H2"
            />
            <path class="loop-arrow" d="M9 12 L3.4 16 L9 20" />
            <circle class="loop-node loop-node--mid" cx="60" cy="50" r="1.9" />
            <circle class="loop-node loop-node--start" cx="2" cy="84" r="2.2" />
            <circle class="loop-node loop-node--end" cx="2" cy="16" r="2.2" />
          </svg>
        </div>

        <figcaption class="map-caption">
          <span>Tres capas auditan. Una misma evidencia las conecta.</span>
          <span class="map-cycle">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M13.1 7.4a5.2 5.2 0 1 1-1.5-3.2" />
              <path d="M13.2 2.3v3.1H10" />
            </svg>
            Ciclo de mejora
          </span>
        </figcaption>
      </figure>
    </div>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  container-type: inline-size;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  background:
    radial-gradient(
      95% 130% at 4% 108%,
      rgba(64, 220, 176, 0.17),
      transparent 56%
    ),
    radial-gradient(
      80% 120% at 94% -12%,
      rgba(104, 139, 255, 0.22),
      transparent 58%
    ),
    linear-gradient(126deg, #07101d 0%, #091524 47%, #0b1a2b 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.07);
  color: #eaf1fb;
}

.hero::before {
  content: '';
  position: absolute;
  inset: -35% -8%;
  z-index: -1;
  pointer-events: none;
  background: conic-gradient(
    from 215deg at 76% 22%,
    transparent 0deg,
    rgba(126, 240, 200, 0.1) 34deg,
    transparent 86deg,
    rgba(130, 160, 255, 0.13) 152deg,
    transparent 220deg
  );
  filter: blur(42px);
  opacity: 0.85;
}

.hero::after {
  content: '';
  position: absolute;
  top: -35%;
  left: 52%;
  width: 44%;
  height: 170%;
  z-index: -1;
  pointer-events: none;
  background: linear-gradient(
    180deg,
    transparent 12%,
    rgba(255, 255, 255, 0.045) 50%,
    transparent 88%
  );
  filter: blur(26px);
  transform: rotate(22deg);
}

.hero-inner {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  align-items: center;
  gap: clamp(2rem, 5cqw, 4.5rem);
  min-height: 500px;
  padding: clamp(1.4rem, 4.2cqw, 3.3rem);
}

.hero-copy {
  min-width: 0;
  max-width: 38rem;
  animation: hero-rise 0.72s var(--ease) 0.04s both;
}

.hero-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.2rem, 4.8cqw, 4.05rem);
  font-weight: 600;
  line-height: 1.01;
  letter-spacing: -0.038em;
  color: #f6f9ff;
  text-wrap: balance;
}

.hero-title-dot {
  color: #67e8bd;
}

.hero-lede {
  max-width: 31rem;
  margin-top: 1.35rem;
  font-size: clamp(0.88rem, 1.2cqw, 1.04rem);
  line-height: 1.62;
  color: #aebdd0;
  text-wrap: pretty;
}

.hero-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 1.65rem 0 0;
  padding: 0;
  list-style: none;
}

.hero-badge {
  --badge-accent: #67e8bd;
  display: inline-flex;
  align-items: center;
  gap: 0.44rem;
  padding: 0.4rem 0.72rem 0.4rem 0.64rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.045);
  color: #cedaea;
  font-size: 0.72rem;
  font-weight: 500;
  line-height: 1.3;
  letter-spacing: 0.004em;
  white-space: nowrap;
}

.hero-badge--layers {
  --badge-accent: #9db6ff;
}

.hero-badge--trace {
  --badge-accent: #ffc27a;
}

.badge-dot {
  position: relative;
  width: 0.42rem;
  height: 0.42rem;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--badge-accent);
  box-shadow: 0 0 0 3px rgba(103, 232, 189, 0.11);
}

.badge-dot::after {
  content: '';
  position: absolute;
  inset: -0.24rem;
  border-radius: 50%;
  border: 1px solid rgba(103, 232, 189, 0.5);
  animation: badge-pulse 3.4s ease-out infinite;
}

.badge-icon {
  width: 0.86rem;
  height: 0.86rem;
  flex-shrink: 0;
  color: var(--badge-accent);
}

.badge-icon svg {
  width: 100%;
  height: 100%;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.35;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.hero-folio {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  width: 100%;
  margin-top: 2.35rem;
  padding-top: 0.85rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  color: #7f92aa;
  font-size: 0.7rem;
  letter-spacing: 0.015em;
}

.folio-mark {
  font-family: var(--font-display);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #d3dfef;
}

.folio-divider {
  width: 1px;
  height: 0.7rem;
  background: rgba(255, 255, 255, 0.16);
}

.folio-label {
  color: #9badc3;
}

.folio-sep {
  color: #5f7188;
}

.folio-meta {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.lpa-map {
  min-width: 0;
  margin: 0;
  animation: hero-rise 0.82s var(--ease) 0.16s both;
}

.map-body {
  position: relative;
  padding-right: 4.2rem;
}

.strata {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.stratum {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.88rem;
  padding: 0.95rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  background: linear-gradient(
    106deg,
    rgba(255, 255, 255, 0.075) 0%,
    rgba(255, 255, 255, 0.024) 56%,
    rgba(255, 255, 255, 0.012) 100%
  );
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.07);
}

.stratum--3 {
  margin-left: 10%;
}

.stratum--2 {
  margin-left: 5%;
}

.stratum-code {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.1rem;
  height: 1.65rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.025);
  color: #d8e4f3;
  font-family: var(--font-code);
  font-size: 0.66rem;
  letter-spacing: 0.08em;
}

.stratum-copy {
  min-width: 0;
}

.stratum-title {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: -0.012em;
  color: #f0f5fd;
}

.stratum-desc {
  margin-top: 0.2rem;
  color: #93a5bb;
  font-size: 0.76rem;
  line-height: 1.4;
  text-wrap: pretty;
}

.stratum-state {
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
  flex-shrink: 0;
  color: var(--state-color);
  font-size: 0.64rem;
  font-weight: 600;
  letter-spacing: 0.07em;
  line-height: 1.3;
  text-transform: uppercase;
  white-space: nowrap;
}

.stratum-state--system {
  --state-color: #67e8bd;
}

.stratum-state--execution {
  --state-color: #9db6ff;
}

.stratum-state--process {
  --state-color: #ffc27a;
}

.state-dot {
  width: 0.35rem;
  height: 0.35rem;
  flex-shrink: 0;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 0.45rem currentColor;
}

.map-loop {
  position: absolute;
  top: -0.1rem;
  right: 0.2rem;
  width: 4rem;
  height: 100%;
  overflow: visible;
  pointer-events: none;
}

.loop-track {
  fill: none;
  stroke: rgba(255, 255, 255, 0.24);
  stroke-width: 1;
  stroke-dasharray: 2 5;
  vector-effect: non-scaling-stroke;
}

.loop-color {
  fill: none;
  stroke: url(#hero-cycle-gradient);
  stroke-width: 1.35;
  stroke-linecap: round;
  opacity: 0.42;
  vector-effect: non-scaling-stroke;
  filter: drop-shadow(0 0 0.35rem rgba(157, 182, 255, 0.32));
}

.loop-branch {
  fill: none;
  stroke: rgba(157, 182, 255, 0.28);
  stroke-width: 1;
  stroke-dasharray: 2 5;
  vector-effect: non-scaling-stroke;
}

.loop-light {
  fill: none;
  stroke: url(#hero-cycle-gradient);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-dasharray: 22 78;
  vector-effect: non-scaling-stroke;
  filter: drop-shadow(0 0 0.3rem rgba(157, 182, 255, 0.7));
  animation: loop-flow 6.8s linear infinite;
}

.loop-arrow {
  fill: none;
  stroke: #67e8bd;
  stroke-width: 1.4;
  stroke-linecap: round;
  stroke-linejoin: round;
  vector-effect: non-scaling-stroke;
}

.loop-node {
  stroke: none;
}

.loop-node--start {
  fill: #ffc27a;
  filter: drop-shadow(0 0 0.3rem rgba(255, 194, 122, 0.8));
}

.loop-node--mid {
  fill: #9db6ff;
  filter: drop-shadow(0 0 0.3rem rgba(157, 182, 255, 0.8));
}

.loop-node--end {
  fill: #67e8bd;
  filter: drop-shadow(0 0 0.3rem rgba(103, 232, 189, 0.8));
}

.map-caption {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 0.9rem;
  color: #7f92aa;
  font-size: 0.7rem;
  line-height: 1.4;
}

.map-cycle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  flex-shrink: 0;
  color: #9eb2ca;
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  white-space: nowrap;
}

.map-cycle svg {
  width: 0.78rem;
  height: 0.78rem;
  fill: none;
  stroke: #67e8bd;
  stroke-width: 1.35;
  stroke-linecap: round;
  stroke-linejoin: round;
}

@keyframes hero-rise {
  from {
    opacity: 0;
    transform: translateY(13px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes badge-pulse {
  0% {
    opacity: 0.7;
    transform: scale(0.65);
  }
  55%,
  100% {
    opacity: 0;
    transform: scale(1.5);
  }
}

@keyframes loop-flow {
  to {
    stroke-dashoffset: -214;
  }
}

@container (max-width: 880px) {
  .hero-inner {
    grid-template-columns: minmax(0, 1fr);
    min-height: 0;
    gap: 2.35rem;
    padding: 2.2rem 2rem;
  }

  .hero-copy {
    max-width: 40rem;
  }

  .lpa-map {
    width: 100%;
    max-width: 34rem;
    margin: 0 auto;
  }
}

@container (max-width: 560px) {
  .hero-inner {
    padding: 1.65rem 1.25rem 1.5rem;
    gap: 1.9rem;
  }

  .hero-lede {
    margin-top: 1.1rem;
  }

  .hero-badges {
    margin-top: 1.35rem;
  }

  .hero-folio {
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 1.8rem;
  }

  .stratum {
    grid-template-columns: auto minmax(0, 1fr);
    row-gap: 0.38rem;
    padding: 0.72rem 0.8rem;
  }

  .stratum--3,
  .stratum--2 {
    margin-left: 0;
  }

  .stratum-state {
    grid-column: 2;
    justify-self: start;
  }

  .map-body {
    padding-right: 3.1rem;
  }

  .map-loop {
    right: 0.1rem;
    width: 3rem;
  }

  .map-caption {
    align-items: flex-start;
    flex-direction: column;
    gap: 0.45rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-copy,
  .lpa-map {
    animation: none;
  }

  .badge-dot::after {
    animation: none;
    opacity: 0;
  }

  .loop-light {
    animation: none;
    opacity: 0.35;
  }
}
</style>
