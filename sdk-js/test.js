import { MyceliumClient } from './index.js';

async function runTest() {
    console.log("🍄 Starting US Neural JS SDK Test...\n");
    const client = new MyceliumClient();

    // 1. Define our JS Tools
    const tools = [
        {
            name: "ForexAgent",
            description: "Convert currency and get exchange rates",
            execute: async (q) => "EUR/USD is 1.09 today."
        },
        {
            name: "WeatherBot",
            description: "Get local climate info and temperature",
            execute: async (q) => "It's 22°C and sunny."
        }
    ];

    // 2. Register them to the local mesh
    console.log("Registering JS tools to Mycelium...");
    for (const tool of tools) {
        await client.registerTool(tool.name.toLowerCase(), tool.name, tool.description);
    }
    
    // 3. Test Semantic Routing via JS
    const query = "how many euros will I get for my dollars?";
    console.log(`\nUser Intent: '${query}'`);
    
    const startTime = performance.now();
    const response = await client.routeAndExecute(query, tools);
    const latency = performance.now() - startTime;

    if (response.toolName) {
        console.log(`✅ Routed to: ${response.toolName} (Confidence: ${(response.confidence * 100).toFixed(1)}%)`);
        console.log(`⚡ Latency: ${latency.toFixed(2)} ms`);
        console.log(`📤 Tool Output: ${response.result}`);
    } else {
        console.log(`❌ Failed: ${response.error}`);
    }
}

runTest();