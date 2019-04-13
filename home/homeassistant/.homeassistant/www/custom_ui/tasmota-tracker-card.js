class TasmotaTrackerCard extends HTMLElement {

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    if (!config.sensors || !Array.isArray(config.sensors)) {
      throw new Error('Please at least one sensor');
    }

    const root = this.shadowRoot;
    if (root.lastChild) root.removeChild(root.lastChild);

    const cardConfig = Object.assign({}, config);
    if (!cardConfig.title) {
      cardConfig.title = '📣 Tasmota Updates';
    } else {
      cardConfig.title = cardConfig.title;
    }
	if (!cardConfig.name_text || cardConfig.name_text == "") {
      cardConfig.name_text = 'Name';
    }
	if (!cardConfig.current_text || cardConfig.current_text == "") {
      cardConfig.current_text = 'Current';
    }
	if (!cardConfig.available_text || cardConfig.available_text == "") {
      cardConfig.available_text = 'Available';
    }
	if (!cardConfig.update_all_text || cardConfig.update_all_text == "") {
      cardConfig.update_all_text = 'Upgrade All';
    }
	if (!cardConfig.check_text || cardConfig.check_text == "") {
      cardConfig.check_text = 'Check';
    }
	if (!cardConfig.check_script) {
      throw new Error('Please set check_script');
    }
	if (!cardConfig.upgrade_script) {
      throw new Error('Please set upgrade_script');
    }
	if (!cardConfig.current_version) {
      throw new Error('Please set current_version');
    }
    const card = document.createElement('ha-card');
    const content = document.createElement('div');
    const style = document.createElement('style');
    style.textContent = `
          ha-card {
            /* sample css */
          }
          table {
            width: 100%;
            padding: 0 32px 0 32px;
          }
          thead th {
            text-align: left;
          }
          tbody tr:nth-child(odd) {
            background-color: var(--paper-card-background-color);
          }
          tbody tr:nth-child(even) {
            background-color: var(--secondary-background-color);
          }
          .button {
            overflow: auto;
            padding: 16px;
          }
          paper-button {
            float: right;
          }
          tbody td.name a {
            color: var(--primary-text-color);
            text-decoration-line: none;
            font-weight: normal;
          }
          td a {
            color: red;
            font-weight: bold;
          }
          tbody td.separator {
            font-weight: bold;
            padding-top: 10px;
            text-transform: capitalize;
          }
        `;
    content.innerHTML = `
      <div id='content'>
      </div>
      <div class='button'>
        <mwc-button raised id='update_tasmota'>` + cardConfig.update_all_text + `</mwc-button>
        <mwc-button raised id='check_tasmota'>` + cardConfig.check_text + `</mwc-button>
      </div>
    `;
    card.header = cardConfig.title
    card.appendChild(content);
    card.appendChild(style);
    root.appendChild(card);
    this._config = cardConfig;
  }

  _filterCards(attributes) {
    return Object.entries(attributes).filter(elem => (elem[0] != "friendly_name" && elem[0] != "homebridge_hidden" && elem[0] != "domain" && elem[0] != "has_update" && elem[0] != "repo" && elem[0] != "hidden"));
  }

  set hass(hass) {
    const config = this._config;
    const root = this.shadowRoot;
    const card = root.lastChild;

    const current_version = hass.states[config.current_version].state;
    this.myhass = hass;
    this.handlers = this.handlers || [];
    let card_content = '';

    card_content += `
      <table>
      <thead><tr><th>` + config.name_text + `</th><th>` + config.current_text + `</th><th>` + config.available_text + `</th></tr></thead>
      <tbody>
    `;
    config.sensors.forEach(sensor => {
      if (hass.states[sensor]) {
        const sensor_version = hass.states[sensor].state;
        const name = hass.states[sensor].attributes.friendly_name;

        const updated_content = `
        <tr>
          <td class='name'>${name}</td>
          <td>${sensor_version}</td>
          <td>${current_version}</td>
        </tr>
        `;
        card_content += updated_content;

        // attach handlers only once
        if (!this.handlers['tasmota_custom_updater']) {
          card.querySelector('#update_tasmota').addEventListener('click', event => {
            this.myhass.callService('script', config.upgrade_script, {});
          });
          card.querySelector('#check_tasmota').addEventListener('click', event => {
            this.myhass.callService('script', config.check_script, {});
          });
          this.handlers['tasmota_custom_updater'] = true;
        }
        root.lastChild.hass = hass;
      }
    });
    card_content += `</tbody></table>`;
    root.getElementById('content').innerHTML = card_content;

  }
  getCardSize() {
    return 1;
  }
}
customElements.define('tasmota-tracker-card', TasmotaTrackerCard);