import { Component } from "./base.js";

class Code extends Component {
    constructor(language = null) {
        super('code');
        if (language) {
            this.setClassList(`language-${language}`);
        }
    }
    addCode(code) {
        this.element.innerText = code;
    }
    async typeCode(code, delay = 50) {
        for (let i = 0; i < code.length; i++) {
            this.element.innerHTML += code[i];
            Prism.highlightElement(this.element);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
}


class PreCode extends Component {
    constructor(code, dataPrefix = "", language = null) {
        super('pre');
        this.element.setAttribute("data-prefix", dataPrefix);
        this.setClassList(`language-${language}`);
        this.codeComponent = new Code(language);
        this.codeComponent.render({target: this.element});
        this.typeCode = this.typeCode.bind(this);
        this.addCode = this.addCode.bind(this);
    }
    async addCode(code, typeCode=false, delay=50) {
        if (typeCode) {
            await this.typeCode(code, delay);
        }
        else {
            this.codeComponent.addCode(code);
        }
    }
    async typeCode(code, delay=25) {
        await this.codeComponent.typeCode(code, delay);
    }
}


export class MockupCode extends Component {
    constructor(language = null) {
        super('div');
        this.language = language;
        this.codeContainer = new Component('div');
        this.codeContainer.element.classList = "mockup-code-wrapper";
        this.element.classList = "mockup-code-container";
        this.codeContainer.render({target: this.element});
        this.addCodes = this.addCodes.bind(this);
    }

    async addCode(code, typeCode=false, delay=50) {
        const dataPrefix = `${this.codeContainer.element.childNodes.length + 1}`;
        const codeComponent = new PreCode(code, dataPrefix, this.language);
        codeComponent.render({target: this.codeContainer.element});
        if (typeCode) {
            await codeComponent.typeCode(code, delay);
        }
        else {
            codeComponent.addCode(code);
        }
        return this.element;
    }

    async addCodes(codes, typeCode=false, delay=50) {
        for (const code of codes) {
            await this.addCode(code, typeCode, delay);
        }
        return this.element;
    }
}
