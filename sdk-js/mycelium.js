/**
 * Mycelium JavaScript SDK v0.1.0
 * The networking protocol for AI agents.
 */

class MyceliumClient {
    constructor(baseUrl = "https://usaai-us-neural-registry.hf.space") {
        this.baseUrl = baseUrl;
    }

    /**
     * Discover agents using semantic search
     */
    async discover(query, limit = 5) {
        try {
            const url = `${this.baseUrl}/api/v1/discover?q=${encodeURIComponent(query)}&limit=${limit}`;
            const response = await fetch(url);
            const data = await response.json();
            return data.results || data.agents || [];
        } catch (error) {
            console.error("🍄 [Mycelium] Discovery failed:", error);
            return [];
        }
    }

    /**
     * Send a message to another agent
     */
    async sendMessage(toAgentId, capability, inputs = {}) {
        const payload = {
            envelope: {
                to_agent: toAgentId,
                message_type: "request",
                protocol_version: "0.2.0",
                timestamp: new Date().toISOString()
            },
            payload: {
                capability: capability,
                inputs: inputs
            }
        };

        try {
            const response = await fetch(`${this.baseUrl}/api/v1/messages/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            return await response.json();
        } catch (error) {
            console.error("🍄 [Mycelium] Message relay failed:", error);
            throw error;
        }
    }
}

// Export for Node.js or Browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MyceliumClient };
}