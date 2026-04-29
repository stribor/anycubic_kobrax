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
    return 8;
  }

  getGridOptions() {
    return {
      rows: "auto",
      columns: 12,
      min_columns: 4,
    };
  }

  static getStubConfig() {
    return {
      name: "Anycubic Kobra X",
      grid_options: {
        columns: 12,
        rows: "auto",
      },
    };
  }

  static getConfigForm() {
    return {
      schema: [
        {
          name: "name",
          selector: {
            text: {},
          },
        },
        {
          name: "image",
          selector: {
            text: {},
          },
        },
      ],
      computeLabel: (schema) => {
        switch (schema.name) {
          case "name":
            return "Name";
          case "image":
            return "Image URL";
          default:
            return schema.name;
        }
      },
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
    const elapsed = this._formatDuration(this._seconds(get("total_time")), false);
    const imageUrl = this._config.image || "/anycubic_kobrax_brand_static/icon.png";
    const previewUrl = this._previewImageUrl(get("preview_image"));
    const lightState = get("light");
    const lightIsOn = lightState?.state === "on";
    const lightTitle = lightState
      ? `Turn ${lightIsOn ? "off" : "on"} printer light`
      : "Printer light entity not found";

    this.shadowRoot.innerHTML = `
      <style>
        *, *::before, *::after {
          box-sizing: border-box;
        }

        :host {
          container-type: inline-size;
          display: block;
          font-family: var(--ha-font-family-body, inherit);
          min-width: 0;
        }

        ha-card {
          background: var(
            --ha-card-background,
            var(--card-background-color, #fff)
          );
          border: var(--ha-card-border-width, 1px) solid
            var(--ha-card-border-color, var(--divider-color, transparent));
          border-radius: var(--ha-card-border-radius, 8px);
          box-shadow: var(--ha-card-box-shadow, none);
          color: var(--primary-text-color);
          display: block;
          overflow: hidden;
          padding: 16px;
          width: 100%;
        }

        .top {
          align-items: center;
          display: grid;
          grid-template-columns: 32px minmax(0, 1fr) 32px;
          gap: 12px;
          margin-bottom: 14px;
        }

        .title {
          align-items: center;
          display: flex;
          font-family: var(--ha-font-family-heading, inherit);
          font-size: 1.25rem;
          font-weight: 500;
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
          background: var(--accent-color);
          border-radius: 50%;
          display: inline-block;
          flex: 0 0 auto;
          height: 12px;
          margin-right: 12px;
          width: 12px;
        }

        .icon {
          align-items: center;
          color: var(--state-icon-color, var(--secondary-text-color));
          display: inline-flex;
          height: 32px;
          justify-content: center;
          opacity: 0.95;
          padding: 0;
          width: 32px;
        }

        button.icon {
          background: none;
          border: 0;
          cursor: pointer;
          position: relative;
          transition:
            background-color 120ms ease,
            color 120ms ease,
            transform 120ms ease;
        }

        button.icon[disabled] {
          cursor: default;
          opacity: 0.45;
        }

        button.icon:not([disabled]):hover {
          background: var(--state-hover-color, rgba(128, 128, 128, 0.16));
          border-radius: 50%;
        }

        button.icon:not([disabled]):focus-visible {
          border-radius: 50%;
          outline: 2px solid var(--accent-color);
          outline-offset: 3px;
        }

        button.icon:not([disabled]):active {
          transform: scale(0.94);
        }

        @media (prefers-reduced-motion: reduce) {
          button.icon {
            transition: none;
          }
        }

        .icon.active {
          color: var(--state-light-active-color, var(--accent-color));
        }

        .icon svg {
          height: 28px;
          width: 28px;
        }

        .main {
          align-items: center;
          display: grid;
          gap: 16px;
          grid-template-columns: minmax(0, 1fr);
        }

        .printer {
          align-items: center;
          display: flex;
          gap: 14px;
          justify-content: center;
          min-height: 150px;
        }

        .printer-image {
          display: block;
          filter: drop-shadow(0 18px 24px rgba(0, 0, 0, 0.24));
          height: auto;
          max-height: 90px;
          max-width: ${previewUrl ? "35%" : "50%"};
          object-fit: contain;
        }

        .preview-image {
          background: var(--secondary-background-color);
          border: var(--ha-card-border-width, 1px) solid
            var(--ha-card-border-color, var(--divider-color, transparent));
          border-radius: 8px;
          display: block;
          height: auto;
          max-height: 180px;
          max-width: 100%;
          object-fit: contain;
          overflow: hidden;
          width: min(62%, 220px);
        }

        .progress {
          font-size: 2.6rem;
          font-weight: 500;
          line-height: 1;
          margin-bottom: 14px;
          text-align: center;
        }

        .stats {
          display: grid;
          font-size: 1rem;
          gap: 6px 16px;
          grid-template-columns: auto 1fr;
          line-height: 1.1;
        }

        .label {
          color: var(--primary-text-color);
          font-weight: 500;
        }

        .value {
          color: var(--secondary-text-color, var(--primary-text-color));
          font-weight: 400;
          overflow-wrap: anywhere;
          text-align: right;
        }

        .slots {
          display: grid;
          gap: 8px;
          grid-template-columns: repeat(4, minmax(42px, 1fr));
          margin: 18px auto 0;
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
          background: var(--slot-color, var(--disabled-color));
          border-radius: 50%;
          display: flex;
          height: 54px;
          height: clamp(46px, 17cqw, 64px);
          justify-content: center;
          margin-bottom: 7px;
          position: relative;
          width: 54px;
          width: clamp(46px, 17cqw, 64px);
        }

        .spool::after {
          background: var(
            --ha-card-background,
            var(--card-background-color, #fff)
          );
          border-radius: 50%;
          content: "";
          height: 53%;
          position: absolute;
          width: 53%;
        }

        .slot-number {
          color: var(--primary-text-color);
          font-size: 1rem;
          font-size: clamp(14px, 4cqw, 17px);
          font-weight: 800;
          position: relative;
          z-index: 1;
        }

        .filament {
          color: var(--secondary-text-color, var(--primary-text-color));
          font-size: 0.95rem;
          font-size: clamp(13px, 3.8cqw, 16px);
          font-weight: 500;
          line-height: 1.1;
          max-width: 100%;
          overflow: hidden;
          text-align: center;
          text-overflow: ellipsis;
          text-transform: uppercase;
          white-space: nowrap;
        }

        .empty .spool {
          --slot-color: var(--disabled-color);
        }

        @container (min-width: 620px) {
          ha-card {
            padding: 28px;
          }

          .top {
            grid-template-columns: 40px minmax(0, 1fr) 40px;
            gap: 14px;
            margin-bottom: 20px;
          }

          .title {
            font-size: 1.55rem;
          }

          .main {
            gap: 28px;
            grid-template-columns: minmax(190px, 1fr) minmax(230px, 0.9fr);
          }

          .printer {
            min-height: 240px;
          }

          .printer-image {
            max-height: 132px;
            max-width: ${previewUrl ? "36%" : "50%"};
          }

          .preview-image {
            max-height: 265px;
            width: min(62%, 300px);
          }

          .progress {
            font-size: 3.2rem;
            margin-bottom: 24px;
          }

          .stats {
            font-size: 1.1rem;
            gap: 8px 22px;
          }

          .slots {
            gap: 14px;
            grid-template-columns: repeat(4, minmax(66px, 1fr));
            margin-top: 30px;
          }

          .spool {
            height: 76px;
            margin-bottom: 9px;
            width: 76px;
          }

          .spool::after {
            height: 39px;
            width: 39px;
          }

          .slot-number {
            font-size: 1rem;
          }

          .filament {
            font-size: 1rem;
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
          <button
            type="button"
            class="icon light-toggle ${lightIsOn ? "active" : ""}"
            title="${this._escapeAttribute(lightTitle)}"
            ${lightState ? "" : "disabled"}
            aria-label="${this._escapeAttribute(lightTitle)}"
          >${this._lightIcon()}</button>
        </header>

        <div class="main">
          <div class="printer">
            <img class="printer-image" src="${this._escapeAttribute(imageUrl)}" alt="" />
            ${previewUrl ? `
              <img
                class="preview-image"
                src="${this._escapeAttribute(previewUrl)}"
                alt="Current print preview"
              />
            ` : ""}
          </div>
          <div class="summary">
            <div class="progress">${this._escape(this._formatPercent(progress))}</div>
            <div class="stats">
              <div class="label">Status</div><div class="value">${this._escape(status)}</div>
              <div class="label">ETA</div><div class="value">${this._escape(eta)}</div>
              <div class="label">Elapsed</div><div class="value">${this._escape(elapsed)}</div>
              <div class="label">Hotend</div><div class="value">${this._escape(this._formatTemp(get("nozzle_temperature")))}</div>
              <div class="label">Bed</div><div class="value">${this._escape(this._formatTemp(get("bed_temperature")))}</div>
              <div class="label">Fan</div><div class="value">${this._escape(this._formatPercent(this._number(get("fan_speed"))))}</div>
              <div class="label">Remaining</div><div class="value">${this._escape(this._formatDuration(remaining, false))}</div>
            </div>
          </div>
        </div>

        <div class="slots">${slotCards.join("")}</div>
      </ha-card>
    `;

    const lightButton = this.shadowRoot.querySelector(".light-toggle");
    if (lightButton && lightState) {
      lightButton.addEventListener("click", () => this._toggleLight(lightState));
    }
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
      "light",
      "last_will",
      "printer_name",
      "print_state",
      "progress",
      "remaining_time",
      "total_time",
      "nozzle_temperature",
      "bed_temperature",
      "fan_speed",
      "preview_image",
    ];
    for (let slot = 1; slot <= 4; slot += 1) {
      keys.push(`slot_${slot}_type`, `slot_${slot}_color`);
    }
    return Object.fromEntries(keys.map((key) => [key, this._findByKey(matches, key)]));
  }

  _findByKey(states, key) {
    if (key === "light") {
      return states.find((state) => state.entity_id?.startsWith("light."));
    }
    const normalizedKey = key.replaceAll("_", "");
    return states.find((state) => {
      const entityId = state.entity_id?.split(".").pop()?.replaceAll("_", "") || "";
      const name = state.attributes?.friendly_name?.toLowerCase().replaceAll(/\s+/g, "") || "";
      return entityId.endsWith(normalizedKey) || name.endsWith(normalizedKey);
    });
  }

  _toggleLight(lightState) {
    if (!lightState) {
      return;
    }
    this._hass.callService(
      "light",
      lightState.state === "on" ? "turn_off" : "turn_on",
      {
        entity_id: lightState.entity_id,
      },
    );
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
    return "var(--disabled-color)";
  }

  _previewImageUrl(state) {
    if (!state || state.state === "unavailable" || state.state === "unknown") {
      return "";
    }
    return state.attributes?.entity_picture || "";
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

  _formatDuration(seconds, showSeconds = true) {
    if (seconds === null) {
      return "--";
    }
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (!showSeconds) {
      if (hours > 0) {
        return `${hours}h ${minutes}min`;
      }
      if (minutes > 0) {
        return `${minutes}min`;
      }
      return "<1min";
    }
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

class AnycubicKobraXAxisCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = undefined;
    this._distance = 1;
  }

  setConfig(config) {
    this._config = config || {};
    const distances = this._distances();
    this._distance = Number(this._config.default_distance) || distances[0];
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
      rows: "auto",
      columns: 12,
      min_columns: 4,
    };
  }

  static getStubConfig() {
    return {
      name: "Axis Move",
      distances: [1, 15, 50],
      default_distance: 1,
      grid_options: {
        columns: 12,
        rows: "auto",
      },
    };
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "name", selector: { text: {} } },
        { name: "config_entry_id", selector: { text: {} } },
        {
          name: "default_distance",
          selector: {
            number: {
              mode: "box",
              min: 0.1,
              max: 100,
              step: 0.1,
              unit_of_measurement: "mm",
            },
          },
        },
      ],
      computeLabel: (schema) => {
        switch (schema.name) {
          case "name":
            return "Name";
          case "config_entry_id":
            return "Config entry ID";
          case "default_distance":
            return "Default distance";
          default:
            return schema.name;
        }
      },
      computeHelper: (schema) => {
        if (schema.name === "config_entry_id") {
          return "Only needed when multiple Anycubic Kobra X printers are loaded.";
        }
        return undefined;
      },
    };
  }

  _render() {
    if (!this._hass) {
      return;
    }

    const distances = this._distances();
    if (!distances.includes(this._distance)) {
      this._distance = distances[0];
    }
    const title = this._config.name || "Axis Move";

    this.shadowRoot.innerHTML = `
      <style>
        *, *::before, *::after {
          box-sizing: border-box;
        }

        :host {
          container-type: inline-size;
          display: block;
          font-family: var(--ha-font-family-body, inherit);
          min-width: 0;
        }

        ha-card {
          background: var(
            --ha-card-background,
            var(--card-background-color, #fff)
          );
          border: var(--ha-card-border-width, 1px) solid
            var(--ha-card-border-color, var(--divider-color, transparent));
          border-radius: var(--ha-card-border-radius, 8px);
          box-shadow: var(--ha-card-box-shadow, none);
          color: var(--primary-text-color);
          display: block;
          overflow: hidden;
          padding: 16px;
          width: 100%;
        }

        .title {
          font-family: var(--ha-font-family-heading, inherit);
          font-size: 1.25rem;
          font-weight: 500;
          line-height: 1.2;
          margin: 0 0 16px;
        }

        .distance-tabs {
          background: var(--secondary-background-color);
          border-radius: 10px;
          display: grid;
          gap: 2px;
          grid-template-columns: repeat(${distances.length}, minmax(0, 1fr));
          margin-bottom: 22px;
          overflow: hidden;
          padding: 2px;
        }

        .distance {
          background: transparent;
          border: 0;
          border-radius: 8px;
          color: var(--secondary-text-color);
          cursor: pointer;
          font: inherit;
          font-size: 1rem;
          font-weight: 500;
          min-height: 42px;
          transition:
            background-color 120ms ease,
            color 120ms ease,
            transform 120ms ease;
        }

        .distance.active {
          background: var(--accent-color);
          color: var(--text-primary-color, #fff);
        }

        .controls {
          align-items: center;
          display: grid;
          gap: 18px;
          grid-template-columns: minmax(82px, 0.7fr) minmax(176px, 1.3fr) minmax(70px, 0.55fr);
          justify-items: center;
        }

        .side-actions {
          display: grid;
          gap: 14px;
          justify-items: center;
        }

        .round-button,
        .move-button,
        .z-button {
          align-items: center;
          background: var(--secondary-background-color);
          border: var(--ha-card-border-width, 1px) solid
            var(--ha-card-border-color, var(--divider-color, transparent));
          color: var(--primary-text-color);
          cursor: pointer;
          display: inline-flex;
          font: inherit;
          justify-content: center;
          min-width: 0;
          transition:
            background-color 120ms ease,
            border-color 120ms ease,
            box-shadow 120ms ease,
            transform 120ms ease;
          user-select: none;
        }

        .distance:not(.active):hover,
        .round-button:hover,
        .move-button:hover,
        .z-button:hover {
          background: var(--state-hover-color, rgba(128, 128, 128, 0.16));
          border-color: var(--accent-color);
        }

        .distance:focus-visible,
        .round-button:focus-visible,
        .move-button:focus-visible,
        .z-button:focus-visible {
          outline: 2px solid var(--accent-color);
          outline-offset: 3px;
          z-index: 1;
        }

        .distance:active,
        .round-button:active,
        .move-button:active,
        .z-button:active {
          transform: scale(0.96);
        }

        .distance.active:hover {
          filter: brightness(1.05);
        }

        @media (prefers-reduced-motion: reduce) {
          .distance,
          .round-button,
          .move-button,
          .z-button {
            transition: none;
          }
        }

        .round-button {
          border-radius: 50%;
          height: 64px;
          width: 64px;
        }

        .round-button ha-icon,
        .home-icon {
          color: var(--accent-color);
        }

        .xy-pad {
          aspect-ratio: 1;
          display: grid;
          grid-template-areas:
            ". up ."
            "left home right"
            ". down .";
          grid-template-columns: repeat(3, minmax(44px, 1fr));
          grid-template-rows: repeat(3, minmax(44px, 1fr));
          max-width: 230px;
          width: 100%;
        }

        .move-button {
          border-radius: 0;
          min-height: 54px;
          position: relative;
        }

        .move-button.up {
          border-radius: 999px 999px 14px 14px;
          grid-area: up;
        }

        .move-button.right {
          border-radius: 14px 999px 999px 14px;
          grid-area: right;
        }

        .move-button.down {
          border-radius: 14px 14px 999px 999px;
          grid-area: down;
        }

        .move-button.left {
          border-radius: 999px 14px 14px 999px;
          grid-area: left;
        }

        .home-xy {
          border-radius: 50%;
          grid-area: home;
          min-height: 54px;
        }

        .direction {
          color: var(--secondary-text-color);
          font-weight: 500;
        }

        .z-stack {
          display: grid;
          max-width: 84px;
          overflow: hidden;
          width: 100%;
        }

        .z-button {
          border-radius: 0;
          min-height: 64px;
        }

        .z-button:first-child {
          border-radius: 12px 12px 0 0;
        }

        .z-button:last-child {
          border-radius: 0 0 12px 12px;
        }

        .warning {
          background: var(--secondary-background-color);
          background: color-mix(in srgb, var(--warning-color, #ff9800) 16%, transparent);
          border-radius: 8px;
          color: var(--warning-color, #ff9800);
          font-size: 0.95rem;
          line-height: 1.25;
          margin-top: 22px;
          padding: 14px 16px;
        }

        @container (max-width: 520px) {
          .controls {
            gap: 16px;
            grid-template-columns: 64px minmax(0, 1fr) 72px;
          }

          .side-actions {
            grid-column: auto;
          }

          .z-stack {
            max-width: 84px;
          }

          .z-button {
            min-height: 52px;
          }

          .z-button:first-child {
            border-radius: 12px 12px 0 0;
          }

          .z-button:last-child {
            border-radius: 0 0 12px 12px;
          }
        }
      </style>

      <ha-card>
        <h2 class="title">${this._escape(title)}</h2>
        <div class="distance-tabs">
          ${distances.map((distance) => `
            <button
              type="button"
              class="distance ${distance === this._distance ? "active" : ""}"
              data-distance="${distance}"
            >${this._escape(this._formatDistance(distance))}</button>
          `).join("")}
        </div>

        <div class="controls">
          <div class="side-actions">
            <button type="button" class="round-button" data-home="xyz" title="Home all axes">
              <ha-icon icon="mdi:home"></ha-icon>
            </button>
            <button type="button" class="round-button" data-motors-off title="Turn off axis motors">
              <ha-icon icon="mdi:gesture-tap"></ha-icon>
            </button>
          </div>

          <div class="xy-pad" aria-label="Move X and Y axes">
            <button type="button" class="move-button up" data-move="y:${this._distance}">
              <span class="direction">▲<br>Y+</span>
            </button>
            <button type="button" class="move-button left" data-move="x:${-this._distance}">
              <span class="direction">◄ X-</span>
            </button>
            <button type="button" class="move-button home-xy" data-home="xy" title="Home X/Y">
              <ha-icon class="home-icon" icon="mdi:home"></ha-icon>
            </button>
            <button type="button" class="move-button right" data-move="x:${this._distance}">
              <span class="direction">X+ ►</span>
            </button>
            <button type="button" class="move-button down" data-move="y:${-this._distance}">
              <span class="direction">Y-<br>▼</span>
            </button>
          </div>

          <div class="z-stack" aria-label="Move Z axis">
            <button type="button" class="z-button" data-move="z:${this._distance}">
              <span class="direction">▲<br>Z+</span>
            </button>
            <button type="button" class="z-button" data-home="z" title="Home Z">
              <ha-icon class="home-icon" icon="mdi:home"></ha-icon>
            </button>
            <button type="button" class="z-button" data-move="z:${-this._distance}">
              <span class="direction">Z-<br>▼</span>
            </button>
          </div>
        </div>

        <div class="warning">
          Operate near the printer and keep the nozzle clear of the bed and frame before moving axes.
        </div>
      </ha-card>
    `;

    this.shadowRoot.querySelectorAll("[data-distance]").forEach((button) => {
      button.addEventListener("click", () => {
        this._distance = Number(button.dataset.distance);
        this._render();
      });
    });
    this.shadowRoot.querySelectorAll("[data-move]").forEach((button) => {
      button.addEventListener("click", () => this._move(button.dataset.move));
    });
    this.shadowRoot.querySelectorAll("[data-home]").forEach((button) => {
      button.addEventListener("click", () => this._home(button.dataset.home));
    });
    const motorsOff = this.shadowRoot.querySelector("[data-motors-off]");
    if (motorsOff) {
      motorsOff.addEventListener("click", () => this._motorsOff());
    }
  }

  _distances() {
    const configured = Array.isArray(this._config.distances)
      ? this._config.distances
      : [1, 15, 50];
    const distances = configured
      .map((value) => Number(value))
      .filter((value) => Number.isFinite(value) && value > 0);
    return distances.length ? distances : [1, 15, 50];
  }

  _serviceData(extra = {}) {
    return {
      ...(this._config.config_entry_id
        ? { config_entry_id: this._config.config_entry_id }
        : {}),
      ...extra,
    };
  }

  _move(move) {
    if (!move) {
      return;
    }
    const [axis, rawDistance] = move.split(":");
    const distance = Number(rawDistance);
    if (!["x", "y", "z"].includes(axis) || !Number.isFinite(distance)) {
      return;
    }
    this._hass.callService(
      "anycubic_kobrax",
      "move_axis",
      this._serviceData({ [axis]: distance }),
    );
  }

  _home(axis) {
    if (!axis) {
      return;
    }
    this._hass.callService(
      "anycubic_kobrax",
      "home_axis",
      this._serviceData({ axis }),
    );
  }

  _motorsOff() {
    this._hass.callService(
      "anycubic_kobrax",
      "motors_off",
      this._serviceData(),
    );
  }

  _formatDistance(distance) {
    return `${Number.isInteger(distance) ? distance : distance.toFixed(1)}mm`;
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
}

if (!customElements.get("anycubic-kobrax-axis-card")) {
  customElements.define("anycubic-kobrax-axis-card", AnycubicKobraXAxisCard);
}

if (!window.customCards.some((card) => card.type === "anycubic-kobrax-axis-card")) {
  window.customCards.push({
    type: "anycubic-kobrax-axis-card",
    name: "Anycubic Kobra X Axis Move",
    description: "Move and home printer axes with Home Assistant services.",
  });
}
