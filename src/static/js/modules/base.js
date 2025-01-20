//@ts-check
export class Component {
    /**
     * Initializes a new Component.
     * 
     * @param {string|HTMLElement} tagOrElement - The tag name or HTMLElement to create the component.
     * @param {Array<string>|string|null} [classList=null] - Optional class names to apply to the element.
     */
    constructor(tagOrElement, classList = null) {
        if (typeof tagOrElement === 'string') {
            this.element = document.createElement(tagOrElement);
        } else if (tagOrElement instanceof HTMLElement) {
            this.element = tagOrElement;
        } else {
            throw new Error('Invalid argument: must be a string (tag name) or an HTMLElement.');
        }

        if (classList) {
            this.setClassList(classList);
        }
    }

    /**
     * Sets an attribute on the component's element.
     * 
     * @param {string} attr - The attribute name.
     * @param {string} value - The attribute value.
     * @returns {Component} This Component instance for chaining.
     */
    setAttribute(attr, value) {
        this.element.setAttribute(attr, value);
        return this;
    }

    /**
     * Retrieves the value of a named attribute on the component's element.
     * 
     * @param {string} attr - The attribute name.
     * @returns {string|null} The attribute value, or null if the attribute does not exist.
     */
    getAttribute(attr) {
        return this.element.getAttribute(attr);
    }
    /**
     * Sets the id attribute on the component's element.
     * 
     * @param {string} id - The id to set.
     * @returns {Component} This Component instance for chaining.
     */
    setId(id) {
        return this.setAttribute('id', id);
    }

    /**
     * Sets the class names on the component's element.
     * 
     * @param {string|Array<string>} classList - The class names to set. If a string, it is
     * set as the className of the element. If an array, its elements are added to the
     * element's classList.
     * @returns {Component} This Component instance for chaining.
     */
    setClassList(classList) {
        if (Array.isArray(classList)) {
            classList.forEach((classItem) => this.addClass(classItem));
        } else {
            this.element.className = classList;
        }
        return this;
    }

    /**
     * Adds a class to the component's element.
     * 
     * @param {string} classItem - The class name to add.
     * @returns {Component} This Component instance for chaining.
     */
    addClass(classItem) {
        this.element.classList.add(classItem);
        return this;
    }

    /**
     * Removes a class from the component's element.
     * 
     * @param {string} classItem - The class name to remove.
     * @returns {Component} This Component instance for chaining.
     */
    removeClass(classItem) {
        this.element.classList.remove(classItem);
        return this;
    }

    /**
     * Toggles a class on the component's element.
     * 
     * @param {string} classItem - The class name to toggle.
     * @returns {Component} This Component instance for chaining.
     */
    toggleClass(classItem) {
        this.element.classList.toggle(classItem);
        return this;
    }


    /**
     * Sets the innerHTML of the component's element or appends a HTMLElement or a Component.
     * 
     * @param {string|HTMLElement|Component} content - The innerHTML to set, or a HTMLElement or Component.
     * @returns {Component} This Component instance for chaining.
     */
    setContent(content) {
        if (typeof content === 'string') {
            this.element.innerHTML = content;
            return this;
        }
        if (content instanceof HTMLElement) {
            this.element.innerHTML = "";
            this.element.appendChild(content);
        } else if (content instanceof Component) {
            this.element.innerHTML = "";
            content.appendTo(this.element);
        } else {
            throw Error(`'content' must be a string, HTMLElement or Component, but got ${typeof content}.`);
        }
        return this;
    }

    /**
     * Sets the textContent of the component's element.
     * 
     * @param {string} content - The text content to set.
     * @returns {Component} This Component instance for chaining.
     */
    setText(content) {
        this.element.textContent = content;
        return this;
    }

    /**
     * Sets the style of the component's element.
     * 
     * @param {Object<string,string>} styles - The styles to set. Each key is a CSS property name and the value is the property value.
     * @returns {Component} This Component instance for chaining.
     */
    setStyle(styles) {
        Object.assign(this.element.style, styles);
        return this;
    }

    /**
     * Appends the component to the given parent.
     * 
     * @param {HTMLElement|Component} parent - The parent element or component to append to.
     * @returns {Component} This Component instance for chaining.
     */
    appendTo(parent) {
        if (parent instanceof Component) {
            parent.element.appendChild(this.element);
        } else if (parent instanceof HTMLElement) {
            parent.appendChild(this.element);
        }
        return this;
    }

    /**
     * Adds an event listener to the component's element.
     * 
     * @param {string} event - The event name.
     * @param {(event: Event) => void} callback - The callback function
     * @returns {Component} This Component instance for chaining.
     */
    addEventListener(event, callback) {
        this.element.addEventListener(event, (e) => callback(e));
        return this;
    }

    remove() {
        this.element.remove();
        return this;
    }

    /**
     * @typedef {Object} RenderOptions
     * @property {HTMLElement|string|Component|null|Node} [target=document.body] - The parent element to render into.
     * @property {'append'|'before'|'replace'|'beforeSibling'|'afterSibling'} [method='append'] - How to insert the component.
     * @property {HTMLElement|ChildNode|null} [reference=null] - The element to insert before (for 'before' insertion or 'replace' replacement).
     */

    /**
     * Renders the component into another element.
     * @param {RenderOptions} options - Options for rendering the component.
     * @returns {Component|undefined} This Component instance for chaining.
     */
    render(options = {}) {
        let { target = document.body, method = 'append', reference = null } = options;
        if (typeof target === 'string') {
            // Detect if it's an XPath selector
            const isXPath = target.startsWith('/') || target.includes('//') || target.includes('@');

            if (isXPath) {
                // Handle XPath selector
                const xpathResult = document.evaluate(target, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                target = xpathResult.singleNodeValue;
                if (target === null) {
                    throw new Error(`No element found for XPath selector: "${target}"`);
                }
                if (!(target instanceof HTMLElement)) {
                    throw new Error(`Element found for XPath selector is not an HTMLElement: "${target}"`);
                }
            } else {
                // Handle CSS selectors (ID, class, tag)
                target = document.querySelector(target);
                if (target === null) {
                    throw new Error(`No element found for CSS selector: "${target}"`);
                }
            }
        } else if (target instanceof Component) {
            target = target.element;
        }

        if (!(target instanceof HTMLElement)) {
            throw new Error('Target must be a valid HTMLElement, Component, or selector.');
        }
        switch (method) {
            case 'append':
                target.appendChild(this.element);
                break;
            case 'before':
                if (!reference || !(reference instanceof HTMLElement)) {
                    throw new Error('Reference element is required for "before" method.');
                }
                target.insertBefore(this.element, reference);
                break;
            case 'replace':
                if (!reference || !(reference instanceof HTMLElement)) {
                    throw new Error('Reference element is required for "replace" method.');
                }
                target.replaceChild(this.element, reference);
                break;
            case 'beforeSibling':
                if (!target.parentNode) {
                    throw new Error('Target must have a parent to insert as a sibling.');
                }
                target.parentNode.insertBefore(this.element, target);
                break;
            case 'afterSibling':
                if (!target.parentNode) {
                    throw new Error('Target must have a parent to insert as a sibling.');
                }
                target.parentNode.insertBefore(this.element, target.nextSibling);
                break;
            default:
                throw new Error(`Invalid render method: "${method}".`);
        }

        return this; // Allow chaining
    }

}