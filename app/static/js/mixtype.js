'use strict';
/*Mixtype v1.0.3(c) 2025 - 2026 Sungwan Jo <sung@wanyne.com> */

class Mixtype {
  constructor(options = {}) {
    options = JSON.parse(JSON.stringify(options));
    this.name = options.name || '';
    this.key = Mixtype.getKey();
    this.prestyles = options.prestyles || [];
    this.styles = options.styles;
    this.updateStyles();
    this.attributePrefix = options.attributePrefix || 'mxty';
    this.keyAttr = `${this.attributePrefix}`;
    this.styleAttr = `${this.attributePrefix}s`;
    this.ignoreTags = options.ignoreTags || [
      'HEAD', 'META', 'LINK', 'SCRIPT', 'STYLE', 'INPUT', 'TEXTAREA', 'SELECT', 'OPTION', 'PRE', 'CODE', 'XML', 'SVG'
    ];
    this.ignoreAttributes = options.ignoreAttributes || ['nomixtype'];
    this.ignoreClasses = options.ignoreClasses || ['material-symbols-outlined'];
    this.observer = null;
  }

  update(options = {}) {
    options = JSON.parse(JSON.stringify(options));
    if (options.name) {
      this.name = options.name;
    }
    if (options.prestyles) {
      this.prestyles = options.prestyles;
    }
    if (options.styles) {
      this.styles = options.styles;
      this.updateStyles();
    }
  }

  updateStyles() {
    for (let i = 0; i < this.styles.length; i++) {
      this.styles[i].matcher = new RegExp(this.styles[i].matcher);
    }
  }

  getType(char) {
    for (const style of this.styles) {
      if (char.match(style.matcher)) {
        return style.key;
      }
    }
    return 'null';
  }

  getTextNodes(element) {
    const textNodes = [];
    for (const node of element.childNodes) {
      if (node.nodeName === '#text') {
        textNodes.push(node);
      } else {
        if (
          node.hasAttribute &&
          !this.ignoreTags.includes(node.nodeName) &&
          !node.hasAttribute(this.keyAttr) &&
          node.getAttributeNames().filter((e) => new Set(this.ignoreAttributes).has(e)).length <= 0 &&
          [...node.classList].filter((e) => new Set(this.ignoreClasses).has(e)).length <= 0
        ) {
          textNodes.push(...this.getTextNodes(node));
        }
      }
    }
    return textNodes;
  }

  replaceNode(node, type, content) {
    const span = document.createElement('span');
    span.setAttribute(this.keyAttr, this.key);
    span.setAttribute(this.styleAttr, type);
    span.textContent = content;
    node.parentNode.insertBefore(span, node);
  }

  apply(element) {
    element.setAttribute(this.keyAttr, this.key);
    element.querySelector(`style[${this.keyAttr}="${this.key}"]`)?.remove();
    element.appendChild(this.getStyleTag());
    this.applyToTextNodes(element);
  }

  applyToTextNodes(element) {
    const textNodes = this.getTextNodes(element);
    for (const node of textNodes) {
      let value = node.nodeValue;
      if (!value.trim()) {
        continue;
      }
      let bufferType = '';
      let buffer = '';
      for (let i = 0; i < value.length; i++) {
        const char = value.charAt(i);
        const type = this.getType(char);
        if (bufferType && bufferType != type) {
          this.replaceNode(node, bufferType, buffer);
          buffer = char;
        } else {
          buffer += char;
        }
        bufferType = type;
      }
      this.replaceNode(node, bufferType, buffer);
      node.parentNode.removeChild(node);
    }
  }

  isInsideIgnoredElement(element, root) {
    let current = element;

    while (current) {
      if (
        this.ignoreTags.includes(current.nodeName) ||
        this.ignoreAttributes.some((attribute) => current.hasAttribute(attribute)) ||
        this.ignoreClasses.some((className) => current.classList.contains(className)) ||
        (current !== root && current.hasAttribute(this.keyAttr))
      ) {
        return true;
      }

      if (current === root) {
        break;
      }
      current = current.parentElement;
    }

    return false;
  }

  observe(element) {
    if (!('MutationObserver' in window)) {
      return;
    }

    this.observer?.disconnect();
    this.observer = new MutationObserver((mutations) => {
      const roots = new Set();

      for (const mutation of mutations) {
        if (mutation.type === 'characterData') {
          if (mutation.target.parentElement) {
            roots.add(mutation.target.parentElement);
          }
          continue;
        }

        for (const node of mutation.addedNodes) {
          if (node.nodeType === Node.TEXT_NODE && node.parentElement) {
            roots.add(node.parentElement);
          } else if (node.nodeType === Node.ELEMENT_NODE) {
            roots.add(node);
          }
        }
      }

      if (!roots.size) {
        return;
      }

      this.observer.disconnect();
      try {
        for (const root of roots) {
          if (root.isConnected && !this.isInsideIgnoredElement(root, element)) {
            this.applyToTextNodes(root);
          }
        }
      } finally {
        this.observer.observe(element, { childList: true, characterData: true, subtree: true });
      }
    });

    this.observer.observe(element, { childList: true, characterData: true, subtree: true });
  }

  getStyleTag() {
    let content = ``;
    for (const line of this.prestyles) {
      content += line;
    }
    content += `[${this.keyAttr}="${this.key}"][${this.styleAttr}] {`;
    content += `vertical-align: baseline;`;
    content += `position: relative;`;
    content += `color: inherit;`;
    content += `cursor: inherit;`;
    content += `text-decoration: none;`;
    content += `line-height: 0;`;
    content += `font-family: inherit;`;
    content += `font-size: 1em;`;
    content += `}`;
    for (const style of this.styles) {
      content += `[${this.keyAttr}="${this.key}"][${this.styleAttr}="${style.key}"] {`;
      if (style.font !== undefined) {
        content += `font-family: ${style.font};`;
      }
      if (style.size !== undefined) {
        content += `font-size: ${style.size}em;`;
      }
      if (style.offset !== undefined) {
        content += `bottom: ${style.offset}em;`;
      }
      if (style.weight !== undefined) {
        content += `font-weight: ${style.weight};`;
      }
      if (style.width !== undefined) {
        content += `font-stretch: ${style.width * 100}%;`;
      }
      content += `}`;
    }
    const element = document.createElement('style');
    element.setAttribute(this.keyAttr, this.key);
    element.textContent = content;
    return element;
  }

  static getKey(n = 6) {
    let res = '';
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    const l = chars.length;
    for (let i = 0; i < n; i++) {
      res += chars.charAt(Math.floor(Math.random() * l));
    }
    return res;
  }
}

const mixtype = new Mixtype({
  name: "WAGUSEN",
  prestyles: [
    "@import url('https://fonts.googleapis.com/css2?family=Host+Grotesk:ital,wght@0,300..800;1,300..800&display=swap');",
    "",
    "@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@100..900&display=swap');",
    ""
  ],
  styles: [
    {
      name: "한글",
      key: "tti9fv",
      matcher: "[ㄱ-ㅎㅏ-ㅣ가-힣ㅥ-ㆎ]",
      font: "\"OnulSamhwagothic\"",
      size: 1,
      offset: 0,
      weight: "inherit"
    },
    {
      name: "로마자와 숫자",
      key: "bcne9k",
      matcher: "[A-Za-zÀ-ÖØ-žſ-ʯЀ-ԯ0-9]",
      font: "\"Host Grotesk\"",
      size: 1.05,
      offset: -0.07,
      weight: "inherit"
    },
    {
      name: "괄호",
      key: "rb8s9g",
      matcher: "[\\(\\)\\{\\}\\[\\]]",
      font: "\"Host Grotesk\"",
      size: 0.96,
      offset: -0.04,
      weight: "inherit"
    },
    {
      name: "나머지",
      key: "k8jyph",
      matcher: "[^a]",
      font: "\"Host Grotesk\"",
      size: 1.05,
      offset: -0.07,
      weight: "inherit"
    }
  ]
});

if (document.body) {
  mixtype.apply(document.body);
  mixtype.observe(document.body);
}
