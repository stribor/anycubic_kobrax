class AnycubicKobraXCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = undefined;
  }

  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 5;
  }

  getGridOptions() {
    return {
      rows: 5,
      columns: 6,
      min_rows: 4,
      min_columns: 3,
    };
  }

  static getStubConfig() {
    return {
      name: "Anycubic Kobra X",
    };
  }

  _render() {
    if (!this._hass) {
      return;
    }

    const states = Object.values(this._hass.states);
    const entities = this._findPrinterEntities(states);
    const get = (key) => this._entityFromConfig(key) || entities[key];
    const slotCards = [1, 2, 3, 4].map((slot) => this._renderSlot(slot, get));
    const remaining = this._seconds(get("remaining_time"));
    const eta = remaining === null ? "--" : this._formatClock(Date.now() + remaining * 1000);
    const progress = this._number(get("progress"), 0);
    const title = this._config.name || this._string(get("printer_name")) || "Anycubic Kobra X";
    const status = this._formatStatus(this._string(get("print_state")) || this._state(get("last_will")));
    const elapsed = this._formatDuration(this._seconds(get("total_time")));
    const imageUrl = this._config.image || "/anycubic_kobrax_brand_static/icon.png";

    this.shadowRoot.innerHTML = `
      <style>
        *, *::before, *::after {
          box-sizing: border-box;
        }

        ha-card {
          background: var(--ha-card-background, #30333d);
          border-radius: var(--ha-card-border-radius, 8px);
          color: var(--primary-text-color, #f3f4f8);
          overflow: hidden;
          padding: 28px;
        }

        .top {
          align-items: center;
          display: grid;
          grid-template-columns: 40px 1fr 40px;
          gap: 14px;
          margin-bottom: 20px;
        }

        .title {
          align-items: center;
          display: flex;
          font-size: 28px;
          font-weight: 760;
          justify-content: center;
          line-height: 1.1;
          min-width: 0;
          text-align: center;
        }

        .title-text {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .dot {
          background: #20c6dd;
          border-radius: 50%;
          display: inline-block;
          flex: 0 0 auto;
          height: 13px;
          margin-right: 13px;
          width: 13px;
        }

        .icon {
          align-items: center;
          color: #f2f3f7;
          display: inline-flex;
          height: 40px;
          justify-content: center;
          opacity: 0.95;
          width: 40px;
        }

        .icon svg {
          height: 30px;
          width: 30px;
        }

        .main {
          align-items: center;
          display: grid;
          gap: 28px;
          grid-template-columns: minmax(190px, 1fr) minmax(230px, 0.9fr);
        }

        .printer {
          align-items: center;
          display: flex;
          justify-content: center;
          min-height: 240px;
        }

        .printer img {
          display: block;
          filter: drop-shadow(0 18px 24px rgba(0, 0, 0, 0.24));
          height: auto;
          max-height: 265px;
          max-width: 100%;
          object-fit: contain;
        }

        .progress {
          font-size: 54px;
          font-weight: 800;
          line-height: 1;
          margin-bottom: 24px;
          text-align: center;
        }

        .stats {
          display: grid;
          font-size: 21px;
          gap: 8px 22px;
          grid-template-columns: auto 1fr;
          line-height: 1.1;
        }

        .label {
          color: #f0f1f6;
          font-weight: 760;
        }

        .value {
          color: #f2f3f7;
          font-weight: 500;
          overflow-wrap: anywhere;
          text-align: right;
        }

        .slots {
          display: grid;
          gap: 14px;
          grid-template-columns: repeat(4, minmax(66px, 1fr));
          margin: 30px auto 0;
          max-width: 520px;
        }

        .slot {
          align-items: center;
          display: flex;
          flex-direction: column;
          min-width: 0;
        }

        .spool {
          align-items: center;
          background: var(--slot-color, #bfc0c2);
          border-radius: 50%;
          display: flex;
          height: 76px;
          justify-content: center;
          margin-bottom: 9px;
          position: relative;
          width: 76px;
        }

        .spool::after {
          background: #f6f7fa;
          border-radius: 50%;
          content: "";
          height: 39px;
          position: absolute;
          width: 39px;
        }

        .slot-number {
          color: #333741;
          font-size: 18px;
          font-weight: 800;
          position: relative;
          z-index: 1;
        }

        .filament {
          color: #f1f2f6;
          font-size: 18px;
          font-weight: 760;
          line-height: 1.1;
          max-width: 100%;
          overflow: hidden;
          text-align: center;
          text-overflow: ellipsis;
          text-transform: uppercase;
          white-space: nowrap;
        }

        .empty .spool {
          --slot-color: #bfc0c2;
        }

        @media (max-width: 560px) {
          ha-card {
            padding: 18px;
          }

          .top {
            grid-template-columns: 32px 1fr 32px;
            margin-bottom: 14px;
          }

          .title {
            font-size: 22px;
          }

          .main {
            gap: 18px;
            grid-template-columns: 1fr;
          }

          .printer {
            min-height: 190px;
          }

          .printer img {
            max-height: 215px;
          }

          .progress {
            font-size: 46px;
            margin-bottom: 18px;
          }

          .stats {
            font-size: 19px;
          }

          .slots {
            grid-template-columns: repeat(2, minmax(96px, 1fr));
          }
        }
      </style>
      <ha-card>
        <header class="top">
          <span class="icon" title="Power">${this._powerIcon()}</span>
          <div class="title">
            <span class="dot"></span>
            <span class="title-text">${this._escape(title)}</span>
          </div>
          <span class="icon" title="Light">${this._lightIcon()}</span>
        </header>

        <div class="main">
          <div class="printer">
            <img src="${this._escapeAttribute(imageUrl)}" alt="" />
          </div>
          <div class="summary">
            <div class="progress">${this._escape(this._formatPercent(progress))}</div>
            <div class="stats">
              <div class="label">Status</div><div class="value">${this._escape(status)}</div>
              <div class="label">ETA</div><div class="value">${this._escape(eta)}</div>
              <div class="label">Elapsed</div><div class="value">${this._escape(elapsed)}</div>
              <div class="label">Hotend</div><div class="value">${this._escape(this._formatTemp(get("nozzle_temperature")))}</div>
              <div class="label">Bed</div><div class="value">${this._escape(this._formatTemp(get("bed_temperature")))}</div>
              <div class="label">Remaining</div><div class="value">${this._escape(this._formatDuration(remaining))}</div>
            </div>
          </div>
        </div>

        <div class="slots">${slotCards.join("")}</div>
      </ha-card>
    `;
  }

  _entityFromConfig(key) {
    const entityId = this._config.entities?.[key];
    return entityId ? this._hass.states[entityId] : undefined;
  }

  _findPrinterEntities(states) {
    const matches = states.filter((state) => {
      const entityId = state.entity_id || "";
      const name = state.attributes?.friendly_name || "";
      return entityId.includes("anycubic_kobra_x") || name.includes("Anycubic Kobra X");
    });
    const keys = [
      "last_will",
      "printer_name",
      "print_state",
      "progress",
      "remaining_time",
      "total_time",
      "nozzle_temperature",
      "bed_temperature",
    ];
    for (let slot = 1; slot <= 4; slot += 1) {
      keys.push(`slot_${slot}_type`, `slot_${slot}_color`);
    }
    return Object.fromEntries(keys.map((key) => [key, this._findByKey(matches, key)]));
  }

  _findByKey(states, key) {
    const normalizedKey = key.replaceAll("_", "");
    return states.find((state) => {
      const entityId = state.entity_id?.split(".").pop()?.replaceAll("_", "") || "";
      const name = state.attributes?.friendly_name?.toLowerCase().replaceAll(/\s+/g, "") || "";
      return entityId.endsWith(normalizedKey) || name.endsWith(normalizedKey);
    });
  }

  _renderSlot(slot, get) {
    const typeState = get(`slot_${slot}_type`);
    const colorState = get(`slot_${slot}_color`);
    const label = this._string(typeState) || "---";
    const color = this._slotColor(colorState);
    const empty = label === "---" || label.toLowerCase() === "unknown" || label.toLowerCase() === "unavailable";
    return `
      <div class="slot ${empty ? "empty" : ""}">
        <div class="spool" style="--slot-color: ${this._escapeAttribute(color)}">
          <span class="slot-number">${slot}</span>
        </div>
        <div class="filament" title="${this._escapeAttribute(label)}">${this._escape(label)}</div>
      </div>
    `;
  }

  _slotColor(state) {
    const rgb = state?.attributes?.rgb;
    if (Array.isArray(rgb) && rgb.length >= 3) {
      return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
    }
    const value = this._string(state);
    if (value?.startsWith("#") || value?.startsWith("rgb")) {
      return value;
    }
    return "#bfc0c2";
  }

  _string(state) {
    if (!state || state.state === "unknown" || state.state === "unavailable" || state.state === "") {
      return "";
    }
    return String(state.state);
  }

  _state(state) {
    return state ? String(state.state) : "";
  }

  _number(state, fallback = null) {
    const value = Number(this._string(state));
    return Number.isFinite(value) ? value : fallback;
  }

  _seconds(state) {
    const value = this._number(state);
    return value === null ? null : Math.max(0, Math.round(value));
  }

  _formatPercent(value) {
    return value === null ? "--" : `${Math.round(value)}%`;
  }

  _formatStatus(status) {
    if (!status) {
      return "--";
    }
    return status
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  _formatTemp(state) {
    const value = this._number(state);
    return value === null ? "--" : `${value.toFixed(2)}°C`;
  }

  _formatDuration(seconds) {
    if (seconds === null) {
      return "--";
    }
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    }
    if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    }
    return `${secs}s`;
  }

  _formatClock(timestamp) {
    return new Intl.DateTimeFormat(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(timestamp));
  }

  _escape(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[char]);
  }

  _escapeAttribute(value) {
    return this._escape(value).replace(/`/g, "&#96;");
  }

  _powerIcon() {
    return `<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M13 3h-2v10h2V3m4.83 2.17-1.42 1.42A7 7 0 1 1 7.59 6.6L6.17 5.17A9 9 0 1 0 17.83 5.17Z"/></svg>`;
  }

  _lightIcon() {
    return `<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9 21h6v-1H9v1m3-20A7 7 0 0 0 8 13.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3.26A7 7 0 0 0 12 1m2.85 11.1-.85.6V16h-4v-3.3l-.85-.6A5 5 0 1 1 14.85 12.1Z"/></svg>`;
  }
}

if (!customElements.get("anycubic-kobrax-card")) {
  customElements.define("anycubic-kobrax-card", AnycubicKobraXCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "anycubic-kobrax-card")) {
  window.customCards.push({
    type: "anycubic-kobrax-card",
    name: "Anycubic Kobra X",
    description: "Printer progress, temperatures, timing, and filament slots.",
  });
}
