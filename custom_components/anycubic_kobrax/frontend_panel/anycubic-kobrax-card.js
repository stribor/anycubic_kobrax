const ANYCUBIC_MATCH_TEXT = ["Anycubic", "Kobra X"];
const ANYCUBIC_DEFAULT_STATS = [
  "status",
  "eta",
  "elapsed",
  "hotend",
  "bed",
  "fan",
  "layer",
  "filament",
  "remaining",
];
const ANYCUBIC_STAT_LABELS = {
  status: "Status",
  eta: "ETA",
  elapsed: "Elapsed",
  hotend: "Hotend",
  bed: "Bed",
  fan: "Fan",
  layer: "Layer",
  filament: "Filament",
  remaining: "Remaining",
};
const ANYCUBIC_IDLE_STATUS_TEXT = [
  "free",
  "idle",
  "ready",
  "standby",
  "complete",
  "completed",
  "finish",
  "finished",
];
const ANYCUBIC_DIAGNOSTIC_STATUS_TEXT = ["online", "pushstarted", "pushstopped", "received"];

function anycubicEntityMatches(states) {
  const explicit = states.filter((state) => {
    const entityId = state.entity_id || "";
    const name = state.attributes?.friendly_name || "";
    return (
      entityId.includes("anycubic_kobra_x") ||
      ANYCUBIC_MATCH_TEXT.some((text) => name.includes(text))
    );
  });
  if (explicit.length > 0) {
    return explicit;
  }

  const printerNameState = states.find((state) => {
    const objectId = state.entity_id?.split(".").pop()?.replaceAll("_", "") || "";
    const name = state.attributes?.friendly_name?.toLowerCase().replaceAll(/\s+/g, "") || "";
    return objectId.endsWith("printername") || name.endsWith("printername");
  });
  const objectId = printerNameState?.entity_id?.split(".").pop();
  const prefix = objectId?.replace(/_?printer_name$/, "");
  return prefix
    ? states.filter((state) => state.entity_id?.split(".").pop()?.startsWith(prefix))
    : [];
}

function anycubicCameraCardDefaults(hass) {
  const states = Object.values(hass?.states || {});
  const matches = anycubicEntityMatches(states);
  const camera = matches.find((state) => state.entity_id?.startsWith("camera."));
  const light = matches.find((state) => state.entity_id?.startsWith("light."));
  return {
    ...(camera ? { camera_entity: camera.entity_id } : {}),
    ...(light ? { light_entity: light.entity_id } : {}),
  };
}

class AnycubicKobraXCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = undefined;
    this._cameraBusy = false;
    this._cameraImage = undefined;
    this._cameraViewerEnabled = false;
    this._lastRenderSignature = "";
  }

  setConfig(config) {
    this._config = config || {};
    this._lastRenderSignature = "";
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return this._config.layout === "compact" ? 3 : 8;
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
        {
          name: "layout",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: "full", label: "Full" },
                { value: "compact", label: "Compact" },
              ],
            },
          },
        },
        {
          name: "progress_style",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: "number", label: "Large number" },
                { value: "bar", label: "Progress bar" },
                { value: "hidden", label: "Hidden" },
              ],
            },
          },
        },
        {
          name: "hide_progress_when_idle",
          selector: {
            boolean: {},
          },
        },
        {
          name: "hide_preview_when_idle",
          selector: {
            boolean: {},
          },
        },
        {
          name: "media_view",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: "preview", label: "Preview image" },
                { value: "camera", label: "Camera stream" },
                { value: "none", label: "None" },
              ],
            },
          },
        },
        { name: "camera_entity", selector: { entity: { domain: "camera" } } },
        {
          name: "visible_stats",
          selector: {
            select: {
              multiple: true,
              mode: "list",
              reorder: true,
              options: Object.entries(ANYCUBIC_STAT_LABELS).map(([value, label]) => ({
                value,
                label,
              })),
            },
          },
        },
        {
          name: "stats_columns",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: 1, label: "1 column" },
                { value: 2, label: "2 columns" },
              ],
            },
          },
        },
        {
          name: "show_slots",
          selector: {
            boolean: {},
          },
        },
        {
          name: "show_header",
          selector: {
            boolean: {},
          },
        },
      ],
      computeLabel: (schema) => {
        switch (schema.name) {
          case "name":
            return "Name";
          case "image":
            return "Image URL";
          case "layout":
            return "Layout";
          case "progress_style":
            return "Progress style";
          case "hide_progress_when_idle":
            return "Hide progress when idle";
          case "hide_preview_when_idle":
            return "Hide preview when idle";
          case "media_view":
            return "Media view";
          case "camera_entity":
            return "Camera entity";
          case "visible_stats":
            return "Visible stats";
          case "stats_columns":
            return "Stats columns";
          case "show_slots":
            return "Show filament slots";
          case "show_header":
            return "Show header";
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
    const layout = this._config.layout === "compact" ? "compact" : "full";
    const remaining = this._seconds(get("remaining_time"));
    const progress = this._number(get("progress"), 0);
    const title = this._config.name || this._string(get("printer_name")) || "Anycubic printer";
    const rawStatus = this._displayStatus(get("print_state"), get("last_will"));
    const status = this._formatStatus(rawStatus);
    const elapsed = this._formatDuration(this._seconds(get("total_time")), false);
    const imageUrl = this._config.image || "/anycubic_kobrax_brand_static/icon.png";
    const isIdle = this._isIdle(rawStatus, progress, remaining);
    const isPrinting = !isIdle;
    const isPaused = this._isPaused(rawStatus);
    const eta = isPrinting && remaining !== null
      ? this._formatClock(Date.now() + remaining * 1000)
      : "--";
    const mediaView = ["preview", "camera", "none"].includes(this._config.media_view)
      ? this._config.media_view
      : "preview";
    const cameraState = this._entityFromConfig("camera_entity") || entities.camera;
    const previewUrl = mediaView === "preview" && this._config.hide_preview_when_idle && isIdle
      ? ""
      : mediaView === "preview"
      ? this._previewImageUrl(get("preview_image"))
      : "";
    const showCamera = mediaView === "camera" && cameraState && !this._isUnavailable(cameraState);
    const cameraIsStreaming = showCamera && cameraState.state === "streaming";
    if (!cameraIsStreaming) {
      this._cameraViewerEnabled = false;
    }
    const showCameraStream = cameraIsStreaming && this._cameraViewerEnabled;
    const cameraTitle = !showCamera
      ? "Camera unavailable"
      : cameraIsStreaming && !this._cameraViewerEnabled
      ? "Show stream on this device"
      : cameraIsStreaming
      ? "Stop camera stream"
      : "Start camera stream";
    const progressStyle = ["number", "bar", "hidden"].includes(this._config.progress_style)
      ? this._config.progress_style
      : "number";
    const hideProgress = progressStyle === "hidden" || (this._config.hide_progress_when_idle !== false && isIdle);
    const visibleStats = this._visibleStats(isPrinting);
    const statsColumns = Number(this._config.stats_columns) === 2 ? 2 : 1;
    const showSlots = layout !== "compact" && this._config.show_slots !== false;
    const slotCards = showSlots ? [1, 2, 3, 4].map((slot) => this._renderSlot(slot, get)) : [];
    const showHeader = this._config.show_header !== false;
    const hasMedia = Boolean(previewUrl || showCamera);
    const statValues = {
      status,
      eta,
      elapsed,
      hotend: this._formatTemp(get("nozzle_temperature")),
      bed: this._formatTemp(get("bed_temperature")),
      fan: this._formatPercent(this._number(get("fan_speed"))),
      layer: this._formatLayer(get("layer"), get("total_layer")),
      filament: this._formatFilament(get("filament_used") || get("supplies_usage")),
      remaining: this._formatDuration(remaining, false),
    };
    const statsHtml = visibleStats
      .map((key) => this._renderStat(key, statValues[key]))
      .join("");
    const progressHtml = hideProgress
      ? ""
      : progressStyle === "bar"
      ? this._renderProgressBar(progress)
      : `<div class="progress-number">${this._escape(this._formatPercent(progress))}</div>`;
    const pauseButton = isPaused ? get("resume_print") : get("pause_print");
    const stopButton = get("stop_print");
    const printControlsHtml = isPrinting && !hideProgress
      ? this._renderPrintControls(pauseButton, stopButton, isPaused)
      : "";
    const compactMeta = isIdle
      ? status
      : `${this._formatPercent(progress)} / ${this._formatDuration(remaining, false)}`;
    const lightState = get("light");
    const lightUnavailable = !lightState || this._isUnavailable(lightState);
    const lightIsOn = lightState?.state === "on";
    const lightTitle = lightUnavailable
      ? "Printer light unavailable"
      : lightState
      ? `Turn ${lightIsOn ? "off" : "on"} printer light`
      : "Printer light entity not found";
    const renderSignature = this._renderSignature({
      cameraBusy: this._cameraBusy,
      cameraEntity: cameraState?.entity_id || "",
      cameraIsStreaming,
      cameraViewerEnabled: this._cameraViewerEnabled,
      compactMeta,
      eta,
      hasMedia,
      hideProgress,
      imageUrl,
      isIdle,
      isPaused,
      layout,
      lightEntity: lightState?.entity_id || "",
      lightIsOn,
      lightUnavailable,
      mediaView,
      previewUrl,
      progress: this._formatPercent(progress),
      printControlsHtml,
      progressStyle,
      rawStatus,
      remaining: this._formatDuration(remaining, false),
      showCamera: Boolean(showCamera),
      showHeader,
      showSlots,
      slotCards,
      statValues,
      statsColumns,
      title,
      visibleStats,
    });
    if (renderSignature === this._lastRenderSignature && this.shadowRoot.querySelector("ha-card")) {
      this._updateStreamingView();
      this._updateCameraButton(cameraState);
      this._updateLightButton(lightState);
      return;
    }
    this._lastRenderSignature = renderSignature;
    const reusableCameraImage = this._cameraImage;
    if (reusableCameraImage?.isConnected) {
      reusableCameraImage.remove();
    }
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
          grid-template-columns: minmax(0, 1fr) auto;
          gap: 12px;
          margin-bottom: 14px;
        }

        .title {
          align-items: center;
          display: flex;
          font-family: var(--ha-font-family-heading, inherit);
          font-size: 1.25rem;
          font-weight: 500;
          justify-content: flex-start;
          line-height: 1.1;
          min-width: 0;
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

        .header-actions {
          align-items: center;
          display: flex;
          gap: 4px;
          justify-content: flex-end;
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
          min-height: ${layout === "compact" ? "96px" : "150px"};
          position: relative;
        }

        .printer-image {
          display: block;
          filter: drop-shadow(0 18px 24px rgba(0, 0, 0, 0.24));
          height: auto;
          max-height: ${layout === "compact" ? "86px" : "90px"};
          max-width: ${hasMedia ? "35%" : "50%"};
          object-fit: contain;
        }

        .media {
          align-items: center;
          background: var(--secondary-background-color);
          border: var(--ha-card-border-width, 1px) solid
            var(--ha-card-border-color, var(--divider-color, transparent));
          border-radius: 8px;
          display: flex;
          justify-content: center;
          overflow: hidden;
          width: min(62%, 220px);
        }

        .preview-image {
          display: block;
          height: auto;
          max-height: 180px;
          max-width: 100%;
          object-fit: contain;
          width: 100%;
        }

        .media hui-image {
          aspect-ratio: 16 / 9;
          display: block;
          width: 100%;
        }

        .camera-slot {
          aspect-ratio: 16 / 9;
          position: relative;
          width: 100%;
        }

        .camera-slot hui-image {
          display: block;
          height: 100%;
          width: 100%;
        }

        .camera-warmup {
          align-items: center;
          background: color-mix(in srgb, var(--secondary-background-color) 88%, transparent);
          color: var(--secondary-text-color);
          display: grid;
          inset: 0;
          justify-items: center;
          padding: 14px;
          position: absolute;
          text-align: center;
        }

        .camera-placeholder {
          align-items: center;
          aspect-ratio: 16 / 9;
          color: var(--secondary-text-color);
          display: grid;
          gap: 8px;
          justify-items: center;
          padding: 14px;
          text-align: center;
          width: 100%;
        }

        .camera-placeholder ha-icon {
          height: 34px;
          width: 34px;
        }

        .progress-number {
          font-size: 2.6rem;
          font-weight: 500;
          line-height: 1;
          margin-bottom: 14px;
          text-align: center;
        }

        .progress-bar-wrap {
          margin-bottom: 14px;
        }

        .progress-section {
          align-items: center;
          display: flex;
          gap: 10px;
          margin-bottom: 14px;
        }

        .progress-section .progress-number,
        .progress-section .progress-bar-wrap {
          flex: 1 1 auto;
          margin-bottom: 0;
          min-width: 0;
        }

        .print-actions {
          align-items: center;
          display: flex;
          flex: 0 0 auto;
          gap: 4px;
        }

        .progress-bar-top {
          align-items: center;
          color: var(--secondary-text-color, var(--primary-text-color));
          display: flex;
          font-size: 0.95rem;
          justify-content: space-between;
          line-height: 1.2;
          margin-bottom: 7px;
        }

        .progress-track {
          background: var(--secondary-background-color);
          border-radius: 999px;
          height: 10px;
          overflow: hidden;
          width: 100%;
        }

        .progress-fill {
          background: var(--accent-color);
          border-radius: inherit;
          height: 100%;
          transition: width 160ms ease;
          width: var(--progress-value);
        }

        .stats {
          display: grid;
          font-size: 1rem;
          gap: 6px 16px;
          grid-template-columns: repeat(${statsColumns}, minmax(0, 1fr));
          line-height: 1.1;
        }

        .stat {
          display: grid;
          gap: 8px;
          grid-template-columns: auto minmax(0, 1fr);
          min-width: 0;
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

        ha-card.compact {
          padding: 12px;
        }

        .compact .top {
          margin-bottom: 8px;
        }

        .compact .main {
          gap: 10px;
        }

        .compact .printer {
          min-height: 96px;
        }

        .compact .media {
          max-height: 110px;
          width: min(62%, 180px);
        }

        .compact .summary {
          min-width: 0;
        }

        .compact .progress-bar-wrap {
          margin-bottom: 0;
        }

        .compact-meta {
          color: var(--secondary-text-color, var(--primary-text-color));
          font-size: 0.95rem;
          line-height: 1.2;
          margin-top: 8px;
          overflow: hidden;
          text-align: center;
          text-overflow: ellipsis;
          white-space: nowrap;
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
          background:
            radial-gradient(circle at center,
              var(--ha-card-background, var(--card-background-color, #fff)) 0 18%,
              color-mix(in srgb, var(--slot-color, var(--disabled-color)) 72%, #fff) 19% 29%,
              var(--slot-color, var(--disabled-color)) 30% 100%);
          border: 3px solid color-mix(in srgb, var(--slot-color, var(--disabled-color)) 78%, #fff);
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
          border: 2px solid color-mix(in srgb, var(--slot-color, var(--disabled-color)) 80%, #000);
          border-radius: 50%;
          content: "";
          height: 35%;
          position: absolute;
          width: 35%;
        }

        .feeding .spool::before {
          background: var(--accent-color);
          border: 2px solid var(--ha-card-background, var(--card-background-color, #fff));
          border-radius: 999px;
          box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent-color) 40%, transparent);
          content: "";
          height: 18px;
          left: 0;
          position: absolute;
          top: 0;
          transform: translate(-18%, -18%);
          width: 18px;
          z-index: 2;
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
          --slot-color: color-mix(in srgb, var(--disabled-color) 54%, var(--primary-text-color));
          background:
            radial-gradient(circle at center,
              var(--ha-card-background, var(--card-background-color, #fff)) 0 17%,
              color-mix(in srgb, var(--slot-color) 70%, #fff) 18% 24%,
              var(--slot-color) 25% 100%);
          border-color: transparent;
          opacity: 0.7;
        }

        @container (min-width: 620px) {
          ha-card {
            padding: 28px;
          }

          .top {
            grid-template-columns: minmax(0, 1fr) auto;
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
            min-height: ${layout === "compact" ? "110px" : "240px"};
          }

          .printer-image {
            max-height: ${layout === "compact" ? "104px" : "132px"};
            max-width: ${hasMedia ? "36%" : "50%"};
          }

          .media {
            max-height: 265px;
            width: min(62%, 300px);
          }

          .progress-number {
            font-size: 3.2rem;
            margin-bottom: 24px;
          }

          .stats {
            font-size: 1.1rem;
            gap: 8px 22px;
          }

          ha-card.compact {
            padding: 16px;
          }

          .compact .main {
            grid-template-columns: minmax(120px, 1fr) minmax(160px, 1fr);
          }

          .compact .top {
            margin-bottom: 10px;
          }

          .compact .media {
            max-height: 130px;
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
            height: 26px;
            width: 26px;
          }

          .filament {
            font-size: 1rem;
          }
        }
      </style>
      <ha-card class="${layout}">
        ${showHeader ? `
          <header class="top">
            <div class="title">
              <span class="dot"></span>
              <span class="title-text">${this._escape(title)}</span>
            </div>
            <div class="header-actions">
              ${mediaView === "camera" ? `
                <button
                  type="button"
                  class="icon camera-toggle ${cameraIsStreaming ? "active" : ""}"
                  title="${this._escapeAttribute(cameraTitle)}"
                  ${!showCamera || this._cameraBusy ? "disabled" : ""}
                  aria-label="${this._escapeAttribute(cameraTitle)}"
                >
                  <ha-icon icon="${cameraIsStreaming && this._cameraViewerEnabled ? "mdi:stop" : cameraIsStreaming ? "mdi:eye" : "mdi:play"}"></ha-icon>
                </button>
              ` : ""}
              <button
                type="button"
                class="icon light-toggle ${lightIsOn ? "active" : ""}"
                title="${this._escapeAttribute(lightTitle)}"
                ${lightUnavailable ? "disabled" : ""}
                aria-label="${this._escapeAttribute(lightTitle)}"
              >${this._lightIcon()}</button>
            </div>
          </header>
        ` : ""}

        <div class="main">
          <div class="printer">
            <img class="printer-image" src="${this._escapeAttribute(imageUrl)}" alt="" />
            ${previewUrl ? `
              <div class="media">
                <img
                  class="preview-image"
                  src="${this._escapeAttribute(previewUrl)}"
                  alt="Current print preview"
                />
              </div>
            ` : ""}
            ${showCamera ? `
              <div class="media camera-media">
                ${showCameraStream ? `
                  <div class="camera-slot">
                    <hui-image></hui-image>
                    ${this._cameraBusy ? `<div class="camera-warmup">Starting stream</div>` : ""}
                  </div>
                ` : `
                  <div class="camera-placeholder">
                    <ha-icon icon="mdi:video-outline"></ha-icon>
                    <div>${this._escape(this._cameraBusy ? "Starting stream" : cameraIsStreaming ? "Stream active" : "Camera stopped")}</div>
                  </div>
                `}
              </div>
            ` : ""}
          </div>
          <div class="summary">
            ${progressHtml ? `
              <div class="progress-section">
                ${progressHtml}
                ${printControlsHtml}
              </div>
            ` : ""}
            ${layout === "compact" ? `
              <div class="compact-meta">${this._escape(compactMeta)}</div>
            ` : ""}
            ${layout !== "compact" && statsHtml ? `
              <div class="stats">${statsHtml}</div>
            ` : ""}
          </div>
        </div>

        ${slotCards.length ? `<div class="slots">${slotCards.join("")}</div>` : ""}
      </ha-card>
    `;

    const lightButton = this.shadowRoot.querySelector(".light-toggle");
    if (lightButton && !lightUnavailable) {
      lightButton.addEventListener("click", () => this._toggleLight(this._matchedEntity("light_entity", "light")));
    }

    const cameraButton = this.shadowRoot.querySelector(".camera-toggle");
    if (cameraButton && showCamera && !this._cameraBusy) {
      cameraButton.addEventListener("click", () => this._toggleCamera(this._matchedEntity("camera_entity", "camera")));
    }

    const cameraImage = this.shadowRoot.querySelector(".camera-slot hui-image");
    if (cameraImage && cameraState) {
      this._cameraImage = cameraImage;
      this._configureImage(cameraImage, cameraState);
    }

    this.shadowRoot.querySelectorAll("[data-print-action]").forEach((button) => {
      button.addEventListener("click", () => {
        this._pressPrintButton(button.dataset.printAction, button.dataset.confirm);
      });
    });
  }

  _entityFromConfig(key) {
    const entityId = this._config.entities?.[key] || this._config[key];
    return entityId ? this._hass.states[entityId] : undefined;
  }

  _matchedEntity(configKey, matchKey) {
    const states = Object.values(this._hass?.states || {});
    const entities = this._findPrinterEntities(states);
    return this._entityFromConfig(configKey) || entities[matchKey];
  }

  _renderSignature(parts) {
    return JSON.stringify(parts);
  }

  _updateStreamingView() {
    if (this._config.media_view !== "camera") {
      return false;
    }
    if (!this._cameraViewerEnabled) {
      return false;
    }
    const image = this.shadowRoot.querySelector(".camera-slot hui-image");
    if (!image) {
      return false;
    }
    const cameraState = this._matchedEntity("camera_entity", "camera");
    if (!cameraState || cameraState.state !== "streaming") {
      return false;
    }
    this._configureImage(image, cameraState);
    this._updateCameraButton(cameraState);
    this._updateLightButton(this._matchedEntity("light_entity", "light"));
    if (!this._cameraBusy) {
      this.shadowRoot.querySelector(".camera-warmup")?.remove();
    }
    return true;
  }

  _updateCameraButton(cameraState) {
    const button = this.shadowRoot.querySelector(".camera-toggle");
    if (!button) {
      return;
    }
    const cameraUnavailable = !cameraState || this._isUnavailable(cameraState);
    const cameraIsStreaming = cameraState?.state === "streaming";
    if (!cameraIsStreaming) {
      this._cameraViewerEnabled = false;
    }
    const title = cameraUnavailable
      ? "Camera unavailable"
      : cameraIsStreaming && !this._cameraViewerEnabled
      ? "Show stream on this device"
      : cameraIsStreaming
      ? "Stop camera stream"
      : "Start camera stream";
    button.classList.toggle("active", cameraIsStreaming);
    button.disabled = cameraUnavailable || this._cameraBusy;
    button.title = title;
    button.setAttribute("aria-label", title);
    const icon = button.querySelector("ha-icon");
    if (icon) {
      icon.setAttribute("icon", cameraIsStreaming && this._cameraViewerEnabled ? "mdi:stop" : cameraIsStreaming ? "mdi:eye" : "mdi:play");
    }
  }

  _updateLightButton(lightState) {
    const button = this.shadowRoot.querySelector(".light-toggle");
    if (!button) {
      return;
    }
    const lightUnavailable = !lightState || this._isUnavailable(lightState);
    const lightIsOn = lightState?.state === "on";
    const title = lightUnavailable
      ? "Printer light unavailable"
      : `Turn ${lightIsOn ? "off" : "on"} printer light`;
    button.classList.toggle("active", lightIsOn);
    button.disabled = lightUnavailable;
    button.title = title;
    button.setAttribute("aria-label", title);
  }

  _findPrinterEntities(states) {
    const matches = anycubicEntityMatches(states);
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
      "camera",
      "pause_print",
      "resume_print",
      "stop_print",
      "layer",
      "total_layer",
      "filament_used",
      "supplies_usage",
      "preview_image",
      "loaded_slot",
    ];
    for (let slot = 1; slot <= 4; slot += 1) {
      keys.push(`slot_${slot}_type`, `slot_${slot}_status`, `slot_${slot}_color`);
    }
    return Object.fromEntries(keys.map((key) => [key, this._findByKey(matches, key)]));
  }

  _findByKey(states, key) {
    if (key === "light") {
      return states.find((state) => state.entity_id?.startsWith("light."));
    }
    if (key === "camera") {
      return states.find((state) => state.entity_id?.startsWith("camera."));
    }
    if (["pause_print", "resume_print", "stop_print"].includes(key)) {
      const normalizedKey = key.replaceAll("_", "");
      return states.find((state) => {
        const entityId = state.entity_id?.split(".").pop()?.replaceAll("_", "") || "";
        const name = state.attributes?.friendly_name?.toLowerCase().replaceAll(/\s+/g, "") || "";
        return state.entity_id?.startsWith("button.") && (
          entityId.endsWith(normalizedKey) || name.endsWith(normalizedKey)
        );
      });
    }
    const normalizedKey = key.replaceAll("_", "");
    return states.find((state) => {
      const entityId = state.entity_id?.split(".").pop()?.replaceAll("_", "") || "";
      const name = state.attributes?.friendly_name?.toLowerCase().replaceAll(/\s+/g, "") || "";
      return entityId.endsWith(normalizedKey) || name.endsWith(normalizedKey);
    });
  }

  _toggleLight(lightState) {
    if (!lightState || this._isUnavailable(lightState)) {
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

  async _toggleCamera(cameraState) {
    if (!cameraState || this._isUnavailable(cameraState)) {
      return;
    }
    if (cameraState.state === "streaming" && !this._cameraViewerEnabled) {
      this._cameraViewerEnabled = true;
      this._render();
      return;
    }
    this._cameraBusy = true;
    if (cameraState.state !== "streaming") {
      this._cameraViewerEnabled = true;
    }
    this._render();
    try {
      await this._hass.callService(
        "camera",
        cameraState.state === "streaming" ? "turn_off" : "turn_on",
        { entity_id: cameraState.entity_id },
      );
    } finally {
      window.setTimeout(() => {
        this._cameraBusy = false;
        if (cameraState.state === "streaming") {
          this._cameraViewerEnabled = false;
        }
        this._render();
      }, cameraState.state === "streaming" ? 0 : 5000);
    }
  }

  _renderPrintControls(pauseButton, stopButton, isPaused) {
    const pauseUnavailable = !pauseButton || this._isUnavailable(pauseButton);
    const stopUnavailable = !stopButton || this._isUnavailable(stopButton);
    const pauseTitle = pauseUnavailable
      ? `${isPaused ? "Resume" : "Pause"} button unavailable`
      : `${isPaused ? "Resume" : "Pause"} print`;
    const stopTitle = stopUnavailable ? "Stop button unavailable" : "Stop print";
    return `
      <div class="print-actions">
        <button
          type="button"
          class="icon print-action"
          title="${this._escapeAttribute(pauseTitle)}"
          aria-label="${this._escapeAttribute(pauseTitle)}"
          data-print-action="${this._escapeAttribute(pauseButton?.entity_id || "")}"
          ${pauseUnavailable ? "disabled" : ""}
        >
          <ha-icon icon="${isPaused ? "mdi:play" : "mdi:pause"}"></ha-icon>
        </button>
        <button
          type="button"
          class="icon print-action"
          title="${this._escapeAttribute(stopTitle)}"
          aria-label="${this._escapeAttribute(stopTitle)}"
          data-print-action="${this._escapeAttribute(stopButton?.entity_id || "")}"
          data-confirm="Stop the active print?"
          ${stopUnavailable ? "disabled" : ""}
        >
          <ha-icon icon="mdi:stop"></ha-icon>
        </button>
      </div>
    `;
  }

  _pressPrintButton(entityId, confirmMessage) {
    if (!entityId) {
      return;
    }
    if (confirmMessage && !window.confirm(confirmMessage)) {
      return;
    }
    this._hass.callService("button", "press", { entity_id: entityId });
  }

  _visibleStats(isPrinting) {
    if (!Array.isArray(this._config.visible_stats)) {
      return isPrinting
        ? ANYCUBIC_DEFAULT_STATS
        : ANYCUBIC_DEFAULT_STATS.filter((key) => !["eta", "remaining"].includes(key));
    }
    return this._config.visible_stats.filter(
      (key) => ANYCUBIC_STAT_LABELS[key] && (isPrinting || !["eta", "remaining"].includes(key)),
    );
  }

  _renderStat(key, value) {
    return `
      <div class="stat">
        <div class="label">${this._escape(ANYCUBIC_STAT_LABELS[key])}</div>
        <div class="value">${this._escape(value)}</div>
      </div>
    `;
  }

  _renderProgressBar(progress) {
    const safeProgress = Math.min(100, Math.max(0, progress ?? 0));
    return `
      <div class="progress-bar-wrap">
        <div class="progress-bar-top">
          <span>Progress</span>
          <span>${this._escape(this._formatPercent(progress))}</span>
        </div>
        <div class="progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(safeProgress)}">
          <div class="progress-fill" style="--progress-value: ${safeProgress}%"></div>
        </div>
      </div>
    `;
  }

  _renderSlot(slot, get) {
    const typeState = get(`slot_${slot}_type`);
    const statusState = get(`slot_${slot}_status`);
    const colorState = get(`slot_${slot}_color`);
    const loadedSlot = this._number(get("loaded_slot"));
    const material = this._string(typeState);
    const status = this._number(statusState);
    const mounted = material && status !== 4;
    const feeding = loadedSlot === slot - 1;
    const label = mounted ? material : "Not mounted";
    const color = this._slotColor(colorState);
    return `
      <div class="slot ${mounted ? "" : "empty"} ${feeding ? "feeding" : ""}">
        <div class="spool" style="--slot-color: ${this._escapeAttribute(color)}"></div>
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
    if (!state || this._isUnavailable(state)) {
      return "";
    }
    return state.attributes?.entity_picture || "";
  }

  _configureImage(image, cameraState) {
    image.hass = this._hass;
    image.stateObj = cameraState;
    image.cameraImage = cameraState.entity_id;
    image.cameraView = this._config.camera_view || "live";
    image.aspectRatio = "16:9";
    image.showState = false;
    image.showName = false;
  }

  _formatLayer(layerState, totalLayerState) {
    const layer = this._number(layerState);
    const totalLayer = this._number(totalLayerState);
    if (layer === null && totalLayer === null) {
      return "--";
    }
    return `${layer ?? "--"} / ${totalLayer ?? "--"}`;
  }

  _formatFilament(state) {
    const value = this._number(state);
    if (value === null) {
      return "--";
    }
    return `${Number(value.toFixed(2))} ${state?.attributes?.unit_of_measurement || ""}`.trim();
  }

  _string(state) {
    if (!state || this._isUnavailable(state) || state.state === "") {
      return "";
    }
    return String(state.state);
  }

  _isUnavailable(state) {
    return state.state === "unknown" || state.state === "unavailable";
  }

  _isIdle(status, progress, remaining) {
    const normalized = String(status || "").toLowerCase().replaceAll(/[\s_-]+/g, "");
    if (ANYCUBIC_IDLE_STATUS_TEXT.some((text) => normalized.includes(text))) {
      return true;
    }
    return progress >= 100 && remaining === 0;
  }

  _isPaused(status) {
    return String(status || "").toLowerCase().replaceAll(/[\s_-]+/g, "") === "paused";
  }

  _displayStatus(printState, lastWillState) {
    const printStatus = this._string(printState);
    if (this._isDiagnosticStatus(printStatus)) {
      return "free";
    }
    if (printStatus && !this._isDiagnosticStatus(printStatus)) {
      return printStatus;
    }
    const lastWill = this._state(lastWillState);
    return this._isDiagnosticStatus(lastWill) ? "free" : lastWill;
  }

  _isDiagnosticStatus(status) {
    const normalized = String(status || "").toLowerCase().replaceAll(/[\s_-]+/g, "");
    return ANYCUBIC_DIAGNOSTIC_STATUS_TEXT.includes(normalized);
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
    const locale = this._hass?.locale;
    const options = {
      hour: "2-digit",
      minute: "2-digit",
    };
    if (locale?.time_format === "24") {
      options.hour12 = false;
    } else if (locale?.time_format === "12") {
      options.hour12 = true;
    }
    return new Intl.DateTimeFormat(locale?.language, options).format(new Date(timestamp));
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
    name: "Anycubic Printer",
    description: "Printer progress, temperatures, timing, and filament slots.",
  });
}

class AnycubicKobraXCameraCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = undefined;
    this._busy = false;
    this._streamWarmupUntil = 0;
    this._viewerEnabled = false;
  }

  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._updateStreamingView()) {
      this._updateLightButton();
      return;
    }
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

  static getStubConfig(hass) {
    return {
      name: "Camera",
      ...anycubicCameraCardDefaults(hass),
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
        { name: "camera_entity", selector: { entity: { domain: "camera" } } },
        { name: "light_entity", selector: { entity: { domain: "light" } } },
      ],
      computeLabel: (schema) => {
        switch (schema.name) {
          case "name":
            return "Name";
          case "camera_entity":
            return "Camera entity";
          case "light_entity":
            return "Light entity";
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
    const matches = this._findPrinterEntities(states);
    const cameraState = this._entityFromConfig("camera_entity") || matches.camera;
    const lightState = this._entityFromConfig("light_entity") || matches.light;
    const cameraUnavailable = !cameraState || this._isUnavailable(cameraState);
    const lightUnavailable = !lightState || this._isUnavailable(lightState);
    const isStreaming = cameraState?.state === "streaming";
    if (!isStreaming) {
      this._viewerEnabled = false;
    }
    const showStream = isStreaming && this._viewerEnabled;
    const isWarming = this._busy || Date.now() < this._streamWarmupUntil;
    const lightIsOn = lightState?.state === "on";
    const title = this._config.name || "Camera";
    const streamTitle = cameraUnavailable
      ? "Camera unavailable"
      : isWarming
      ? "Starting stream"
      : isStreaming && !this._viewerEnabled
      ? "Show stream on this device"
      : isStreaming
      ? "Stop camera stream"
      : "Start camera stream";
    const lightTitle = lightUnavailable
      ? "Printer light unavailable"
      : `Turn ${lightIsOn ? "off" : "on"} printer light`;

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

        .header {
          align-items: center;
          display: flex;
          gap: 12px;
          justify-content: space-between;
          margin-bottom: 14px;
        }

        .title {
          font-family: var(--ha-font-family-heading, inherit);
          font-size: 1.25rem;
          font-weight: 500;
          line-height: 1.2;
          margin: 0;
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .state {
          color: var(--secondary-text-color);
          flex: 0 0 auto;
          font-size: 0.95rem;
          line-height: 1.2;
        }

        .header-actions {
          align-items: center;
          display: flex;
          flex: 0 0 auto;
          gap: 4px;
          justify-content: flex-end;
        }

        .viewer {
          align-items: center;
          aspect-ratio: 16 / 9;
          background: var(--secondary-background-color);
          border: var(--ha-card-border-width, 1px) solid
            var(--ha-card-border-color, var(--divider-color, transparent));
          border-radius: 8px;
          display: flex;
          justify-content: center;
          overflow: hidden;
          position: relative;
          width: 100%;
        }

        .viewer hui-image {
          display: block;
          height: 100%;
          width: 100%;
        }

        .warmup {
          align-items: center;
          background: color-mix(in srgb, var(--secondary-background-color) 88%, transparent);
          color: var(--secondary-text-color);
          display: grid;
          inset: 0;
          justify-items: center;
          padding: 18px;
          position: absolute;
          text-align: center;
          z-index: 1;
        }

        .placeholder {
          align-items: center;
          color: var(--secondary-text-color);
          display: grid;
          gap: 10px;
          justify-items: center;
          padding: 18px;
          text-align: center;
        }

        .placeholder ha-icon {
          color: var(--state-icon-color, var(--secondary-text-color));
          height: 44px;
          width: 44px;
        }

        button.icon {
          align-items: center;
          background: none;
          border: 0;
          color: var(--state-icon-color, var(--secondary-text-color));
          cursor: pointer;
          display: inline-flex;
          height: 32px;
          justify-content: center;
          opacity: 0.95;
          padding: 0;
          position: relative;
          transition:
            background-color 120ms ease,
            color 120ms ease,
            transform 120ms ease;
          width: 32px;
        }

        button.icon.active {
          color: var(--state-light-active-color, var(--accent-color));
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

        button.icon[disabled] {
          cursor: default;
          opacity: 0.45;
        }

        ha-icon {
          height: 22px;
          width: 22px;
        }

        @media (prefers-reduced-motion: reduce) {
          button.icon {
            transition: none;
          }
        }

        @container (min-width: 620px) {
          ha-card {
            padding: 24px;
          }

          .header {
            margin-bottom: 18px;
          }

          .title {
            font-size: 1.45rem;
          }

        }
      </style>

      <ha-card>
        <header class="header">
          <h2 class="title">${this._escape(title)}</h2>
          <div class="header-actions">
            <div class="state">${this._escape(this._formatState(cameraState))}</div>
            <button
              type="button"
              class="icon stream ${isStreaming && this._viewerEnabled ? "active" : ""}"
              title="${this._escapeAttribute(streamTitle)}"
              aria-label="${this._escapeAttribute(streamTitle)}"
              ${cameraUnavailable || isWarming ? "disabled" : ""}
            >
              <ha-icon icon="${isStreaming && this._viewerEnabled ? "mdi:stop" : isStreaming ? "mdi:eye" : "mdi:play"}"></ha-icon>
            </button>
            <button
              type="button"
              class="icon light ${lightIsOn ? "active" : ""}"
              title="${this._escapeAttribute(lightTitle)}"
              aria-label="${this._escapeAttribute(lightTitle)}"
              ${lightUnavailable ? "disabled" : ""}
            >
              <ha-icon icon="${lightIsOn ? "mdi:lightbulb-on" : "mdi:lightbulb-outline"}"></ha-icon>
            </button>
          </div>
        </header>

        <div class="viewer">
          ${cameraState && showStream ? "<hui-image></hui-image>" : `
            <div class="placeholder">
              <ha-icon icon="mdi:video-outline"></ha-icon>
              <div>${this._escape(cameraUnavailable ? "Camera unavailable" : isWarming ? "Starting stream" : isStreaming ? "Stream active" : "Stream stopped")}</div>
            </div>
          `}
          ${cameraState && showStream && isWarming ? `
            <div class="warmup">Starting stream</div>
          ` : ""}
        </div>

      </ha-card>
    `;

    const image = this.shadowRoot.querySelector("hui-image");
    if (image && cameraState) {
      this._configureImage(image, cameraState);
    }

    const streamButton = this.shadowRoot.querySelector(".stream");
    if (streamButton && !cameraUnavailable && !isWarming) {
      streamButton.addEventListener("click", () => this._toggleCamera(cameraState));
    }
    const lightButton = this.shadowRoot.querySelector(".light");
    if (lightButton && !lightUnavailable) {
      lightButton.addEventListener("click", () => this._toggleLight(lightState.entity_id));
    }
  }

  _entityFromConfig(key) {
    const entityId = this._config[key];
    return entityId ? this._hass.states[entityId] : undefined;
  }

  _cameraState() {
    const states = Object.values(this._hass.states);
    const matches = this._findPrinterEntities(states);
    return this._entityFromConfig("camera_entity") || matches.camera;
  }

  _lightState() {
    const states = Object.values(this._hass.states);
    const matches = this._findPrinterEntities(states);
    return this._entityFromConfig("light_entity") || matches.light;
  }

  _updateStreamingView() {
    const image = this.shadowRoot.querySelector("hui-image");
    if (!image) {
      return false;
    }
    if (!this._viewerEnabled) {
      return false;
    }
    const cameraState = this._cameraState();
    if (!cameraState || cameraState.state !== "streaming") {
      return false;
    }
    this._configureImage(image, cameraState);
    const state = this.shadowRoot.querySelector(".state");
    if (state) {
      state.textContent = this._formatState(cameraState);
    }
    const warmup = this.shadowRoot.querySelector(".warmup");
    if (warmup && Date.now() >= this._streamWarmupUntil) {
      warmup.remove();
    }
    return true;
  }

  _updateLightButton() {
    const lightButton = this.shadowRoot.querySelector(".light");
    if (!lightButton) {
      return;
    }
    const lightState = this._lightState();
    const lightUnavailable = !lightState || this._isUnavailable(lightState);
    const lightIsOn = lightState?.state === "on";
    const lightTitle = lightUnavailable
      ? "Printer light unavailable"
      : `Turn ${lightIsOn ? "off" : "on"} printer light`;
    lightButton.classList.toggle("active", lightIsOn);
    lightButton.disabled = lightUnavailable;
    lightButton.title = lightTitle;
    lightButton.setAttribute("aria-label", lightTitle);
    lightButton.innerHTML = `<ha-icon icon="${lightIsOn ? "mdi:lightbulb-on" : "mdi:lightbulb-outline"}"></ha-icon>`;
  }

  _configureImage(image, cameraState) {
    image.hass = this._hass;
    image.stateObj = cameraState;
    image.cameraImage = cameraState.entity_id;
    image.cameraView = this._config.camera_view || "live";
    image.aspectRatio = "16:9";
    image.showState = false;
    image.showName = false;
  }

  _findPrinterEntities(states) {
    const matches = anycubicEntityMatches(states);
    return {
      camera: matches.find((state) => state.entity_id?.startsWith("camera.")),
      light: matches.find((state) => state.entity_id?.startsWith("light.")),
    };
  }

  async _toggleCamera(cameraState) {
    if (!cameraState || this._isUnavailable(cameraState)) {
      return;
    }
    if (cameraState.state === "streaming" && !this._viewerEnabled) {
      this._viewerEnabled = true;
      this._render();
      return;
    }
    this._busy = true;
    if (cameraState.state !== "streaming") {
      this._viewerEnabled = true;
      this._streamWarmupUntil = Date.now() + 7000;
      window.setTimeout(() => {
        this._streamWarmupUntil = 0;
        this._render();
      }, 7000);
    }
    this._render();
    try {
      await this._hass.callService(
        "camera",
        cameraState.state === "streaming" ? "turn_off" : "turn_on",
        { entity_id: cameraState.entity_id },
      );
    } finally {
      this._busy = false;
      if (cameraState.state === "streaming") {
        this._viewerEnabled = false;
        this._streamWarmupUntil = 0;
      }
      this._render();
    }
  }

  _toggleLight(lightEntityId) {
    const lightState = lightEntityId ? this._hass.states[lightEntityId] : this._lightState();
    if (!lightState || this._isUnavailable(lightState)) {
      return;
    }
    this._hass.callService(
      "light",
      lightState.state === "on" ? "turn_off" : "turn_on",
      { entity_id: lightState.entity_id },
    );
  }

  _formatState(state) {
    if (!state) {
      return "Not found";
    }
    if (this._isUnavailable(state)) {
      return "Unavailable";
    }
    return state.state === "streaming" ? "Streaming" : "Stopped";
  }

  _isUnavailable(state) {
    return state.state === "unknown" || state.state === "unavailable";
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
}

if (!customElements.get("anycubic-kobrax-camera-card")) {
  customElements.define("anycubic-kobrax-camera-card", AnycubicKobraXCameraCard);
}

if (!window.customCards.some((card) => card.type === "anycubic-kobrax-camera-card")) {
  window.customCards.push({
    type: "anycubic-kobrax-camera-card",
    name: "Anycubic Camera",
    description: "Start and stop the printer camera stream and control the light.",
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
    const controlsAvailable = this._controlsAvailable();
    const disabled = controlsAvailable ? "" : "disabled";

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
        .round-button:not([disabled]):hover,
        .move-button:not([disabled]):hover,
        .z-button:not([disabled]):hover {
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
        .round-button:not([disabled]):active,
        .move-button:not([disabled]):active,
        .z-button:not([disabled]):active {
          transform: scale(0.96);
        }

        .round-button[disabled],
        .move-button[disabled],
        .z-button[disabled] {
          cursor: default;
          opacity: 0.45;
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
            <button type="button" class="round-button" data-home="xyz" title="Home all axes" ${disabled}>
              <ha-icon icon="mdi:home"></ha-icon>
            </button>
            <button type="button" class="round-button" data-motors-off title="Turn off axis motors" ${disabled}>
              <ha-icon icon="mdi:gesture-tap"></ha-icon>
            </button>
          </div>

          <div class="xy-pad" aria-label="Move X and Y axes">
            <button type="button" class="move-button up" data-move="y:${this._distance}" ${disabled}>
              <span class="direction">▲<br>Y+</span>
            </button>
            <button type="button" class="move-button left" data-move="x:${-this._distance}" ${disabled}>
              <span class="direction">◄ X-</span>
            </button>
            <button type="button" class="move-button home-xy" data-home="xy" title="Home X/Y" ${disabled}>
              <ha-icon class="home-icon" icon="mdi:home"></ha-icon>
            </button>
            <button type="button" class="move-button right" data-move="x:${this._distance}" ${disabled}>
              <span class="direction">X+ ►</span>
            </button>
            <button type="button" class="move-button down" data-move="y:${-this._distance}" ${disabled}>
              <span class="direction">Y-<br>▼</span>
            </button>
          </div>

          <div class="z-stack" aria-label="Move Z axis">
            <button type="button" class="z-button" data-move="z:${this._distance}" ${disabled}>
              <span class="direction">▲<br>Z+</span>
            </button>
            <button type="button" class="z-button" data-home="z" title="Home Z" ${disabled}>
              <ha-icon class="home-icon" icon="mdi:home"></ha-icon>
            </button>
            <button type="button" class="z-button" data-move="z:${-this._distance}" ${disabled}>
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
    if (!this._controlsAvailable() || !move) {
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
    if (!this._controlsAvailable() || !axis) {
      return;
    }
    this._hass.callService(
      "anycubic_kobrax",
      "home_axis",
      this._serviceData({ axis }),
    );
  }

  _motorsOff() {
    if (!this._controlsAvailable()) {
      return;
    }
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

  _controlsAvailable() {
    const states = Object.values(this._hass?.states || {});
    const matches = anycubicEntityMatches(states);
    return matches.length > 0 && matches.some((state) => state.state !== "unavailable");
  }

  _isUnavailable(state) {
    return state.state === "unknown" || state.state === "unavailable";
  }
}

if (!customElements.get("anycubic-kobrax-axis-card")) {
  customElements.define("anycubic-kobrax-axis-card", AnycubicKobraXAxisCard);
}

if (!window.customCards.some((card) => card.type === "anycubic-kobrax-axis-card")) {
  window.customCards.push({
    type: "anycubic-kobrax-axis-card",
    name: "Anycubic Axis Move",
    description: "Move and home printer axes with Home Assistant services.",
  });
}
