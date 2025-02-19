import { MockupCode, SlideDownButton } from './modules/components.js'

const animations = [
  {
    language: 'python',
    code: [
      '# server.py',
      'from aiohttp import web, WSMsgType',
      'import aiohttp_jinja2, jinja2, json, uuid',
      '',
      'clients = {}',
      '',
      '@aiohttp_jinja2.template("index.html")',
      'async def index(request):',
      '    return {}',
      '',
      'async def websocket_handler(request):',
      '    ws = web.WebSocketResponse()',
      '    await ws.prepare(request)',
      '    client_id = str(uuid.uuid4())',
      '    clients[client_id] = ws',
      '    try:',
      '        async for msg in ws:',
      '            if msg.type == WSMsgType.TEXT:',
      '                data = json.loads(msg.data)',
      '                if data["type"] == "message":',
      '                    for cid, client in clients.items():',
      '                        if cid != client_id:',
      '                            await client.send_str(json.dumps({',
      '                                "type": "message", "content": data["content"], "from": client_id',
      '                            }))',
      '    finally:',
      '        clients.pop(client_id, None)',
      '    return ws',
      '',
      'app = web.Application()',
      'aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))',
      'app.add_routes([web.get("/", index), web.get("/ws", websocket_handler)])',
      '',
      'if __name__ == "__main__":',
      '    web.run_app(app, host="127.0.0.1", port=8080)',
    ]
  },
  {
    language: 'javascript',
    code: [
      '// home.js',
      'document.addEventListener("DOMContentLoaded", () => {',
      '  const ws = new WebSocket("ws://127.0.0.1:8080/ws");',
      '',
      '  const addMessage = (msg, sender) => {',
      '    const el = document.createElement("div");',
      '    el.textContent = msg;',
      '    el.className = `p-2 mb-2 rounded-lg ${sender === "you" ? "bg-blue-800 text-right text-neutral-900" : "bg-gray-100 text-left text-gray-700"}`;',
      '    chatBox.appendChild(el);',
      '    chatBox.scrollTop = chatBox.scrollHeight;',
      '  };',
      '',
      '  ws.onmessage = (e) => {',
      '    const { type, content, from } = JSON.parse(e.data);',
      '    if (type === "message") addMessage(content, from);',
      '  };',
      '',
      '  sendButton.addEventListener("click", () => {',
      '    const message = messageInput.value.trim();',
      '    if (message) {',
      '      ws.send(JSON.stringify({ type: "message", content: message }));',
      '      addMessage(message, "you");',
      '      messageInput.value = "";',
      '    }',
      '  });',
      '',
      '  messageInput.addEventListener("keypress", (e) => {',
      '    if (e.key === "Enter") {',
      '      e.preventDefault();',
      '      sendButton.click();',
      '    }',
      '  });',
      '});',
    ]
  },
  {
    language: 'html',
    code: [
      '<!-- index.html -->',
      '<!DOCTYPE html>',
      '<html lang="en">',
      '<head>',
      '    <meta charset="UTF-8">',
      '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
      '    <title>Chat Application</title>',
      '    <script src="https://cdn.tailwindcss.com"></script>',
      '    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@100;300;400;500;700&display=swap">',
      '</head>',
      '<body class="h-screen">',
      '    <div class="main-app">',
      '        <header class="bg-blue-950 text-gray-200 p-4 shadow-md rounded-t-3xl">',
      '            <h1 class="text-2xl roboto-light">Chat Application</h1>',
      '        </header>',
      '        <main class="flex-1 p-4 overflow-auto">',
      '            <div id="chatBox" class="h-full bg-blue-600 p-4 rounded-lg shadow-md space-y-4 overflow-y-auto"></div>',
      '        </main>',
      '        <footer class="bg-gray-800 rounded-b-3xl p-4">',
      '            <div class="flex">',
      '                <input id="messageInput" type="text" placeholder="Type a message..." class="flex-1 p-2 border rounded-l-lg bg-gray-500 text-gray-200 focus:ring-2 focus:ring-blue-500">',
      '                <button id="sendButton" class="p-2 ml-2 bg-blue-950 text-gray-200 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500">Send</button>',
      '            </div>',
      '        </footer>',
      '    </div>',
      '    <script src="/static/js/chat.js?version=1" type="module"></script>',
      '</body>',
      '</html>',
    ]
  }  
];

const aigentsAnimation = {
  language: 'python',
  code: [
    'from aigents import AsyncOpenAIChatter',
    '',
    'setup = "You are a very experienced and successful fantasy novel writer. "',
    '## generate your API key: https://platform.openai.com/api-keys',
    'api_key = "YOUR_OPEN_AI_API_KEY"',
    'temperature = 0.5  # for creativity',
    'chatter = AsyncOpenAIChatter(setup=setup, api_key=api_key)',
    '',
    'response = await chatter.answer(',
    '    "What are the difference between soft magic system "',
    '    "and hard magic system?"',
    ')',
  ]
}

const paymentsApiAnimation = {
  language: 'python',
  code: [
    'import httpx',
    '',
    'async with httpx.AsyncClient() as client: "',
    '  response = await client.post(',
    '    f"{BASE_URL}/auth/token",',
    '    data={"username": USERNAME, "password": PASSWORD},',
    ')',
    'if response.status_code == 200:',
    '    return response.json()["access_token"]',
    'else:',
    '    print("Login failed:", response.json())',
    '    return None',
    ]
}

let currentAnimation = 0;
async function typeCode({animation, id='codeContainer'}) {
  const codeContainerElement = document.getElementById(id);
  codeContainerElement.innerHTML = '';

  const mockupCode = new MockupCode(animation.language);
  mockupCode.render({target: codeContainerElement});

  let lineIndex = 0;

  async function typeLine() {
    if (lineIndex < animation.code.length) {
      await mockupCode.addCode(animation.code[lineIndex], true, 5);
      lineIndex++;

      const mockupCodeContainer = document.querySelector('.mockup-code-container');
      mockupCodeContainer.scrollTop = mockupCodeContainer.scrollHeight;
      
      setTimeout(() => {
        typeLine();
      }, 200 + Math.random() * 100);
    } else {
      setTimeout(nextAnimation, 3000);
    }
  }

  await typeLine();
}

function nextAnimation() {
  currentAnimation = (currentAnimation + 1) % animations.length;
  typeCode({animation: animations[currentAnimation], id: 'codeContainer'});
}

const mockAigentsCodeId = "mock-aigents-code";
const mockpaymentsApiCodeId = "mock-payments-api-code";

const aigentsSectionObserver = new IntersectionObserver(
  (entries) => {
    if (entries[0].isIntersecting) {
      console.debug('aigents section is visible');
      typeCode({animation: aigentsAnimation, id: mockAigentsCodeId});
    }
});

const paymentsApiSectionObserver = new IntersectionObserver(
  (entries) => {
    if (entries[0].isIntersecting) {
      console.debug('aigents section is visible');
      typeCode({animation: paymentsApiAnimation, id: mockpaymentsApiCodeId});
    }
});

window.addEventListener('load', () => {

  typeCode({animation: animations[currentAnimation], id: 'codeContainer'});
  aigentsSectionObserver.observe(document.getElementById(mockAigentsCodeId));
  paymentsApiSectionObserver.observe(document.getElementById(mockpaymentsApiCodeId));

  new SlideDownButton({
    tagOrElement: document.getElementById('arrow-section-about'),
    targetId: 'section-about'
  })
  new SlideDownButton({
    tagOrElement: document.getElementById('arrow-section-cards'),
    targetId: 'section-cards'
  });
  new SlideDownButton({
    tagOrElement: document.getElementById('arrow-section-sample-chat'),
    targetId: 'section-sample-chat'
  });
  new SlideDownButton({
    tagOrElement: document.getElementById('arrow-section-aigents'),
    targetId: 'section-aigents'
  });
  new SlideDownButton({
    tagOrElement: document.getElementById('arrow-section-datasets'),
    targetId: 'section-datasets'
  });
  new SlideDownButton({
    tagOrElement: document.getElementById('arrow-section-contact'),
    targetId: 'section-contact'
  });
  new SlideDownButton({
    tagOrElement: document.getElementById('arrow-payments-api'),
    targetId: 'payments-api'
  });
});



// await typeCode(animations[currentAnimation]);