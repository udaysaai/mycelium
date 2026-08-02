/**
 * 🍄 US Neural: Mycelium JavaScript SDK
 * Drop-in semantic routing for Node.js and Browser AI apps.
 */

export class MyceliumClient {
    constructor(baseUrl = "http://127.0.0.1:8000/api/v1") {
        this.baseUrl = baseUrl;
    }

    /**
     * Register a tool or agent to the Mycelium Semantic Registry.
     */
    async registerTool(agentId, name, description, tags = []) {
        try {
            const response = await fetch(`${this.baseUrl}/agents/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    agent_id: agentId,
                    name: name,
                    description: description,
                    tags: tags
                })
            });
            return await response.json();
        } catch (error) {
            console.error(`🍄 [Mycelium Error] Registration failed: ${error.message}`);
            return null;
        }
    }

    /**
     * Discover the best tool based on pure user intent.
     */
    async discoverTool(userQuery, minScore = 0.15) {
        try {
            const url = new URL(`${this.baseUrl}/agents/discover`);
            url.searchParams.append("q", userQuery);
            url.searchParams.append("semantic", "true");
            url.searchParams.append("limit", "1");

            const response = await fetch(url);
            const data = await response.json();

            if (data.agents && data.agents.length > 0) {
                const topAgent = data.agents[0];
                if ((topAgent._similarity_score || 0) >= minScore) {
                    return topAgent;
                }
            }
            return null;
        } catch (error) {
            console.error(`🍄 [Mycelium Error] Discovery failed: ${error.message}`);
            return null;
        }
    }

    /**
     * The Magic Function: Matches semantic intent with actual JS functions/tools.
     */
    async routeAndExecute(userQuery, availableTools) {
        const bestToolMeta = await this.discoverTool(userQuery);

        if (!bestToolMeta) {
            return { error: "No suitable tool found for your request." };
        }

        const targetToolName = bestToolMeta.name;
        const confidence = bestToolMeta._similarity_score;

        // Find the matching tool in the JS array
        const tool = availableTools.find(
            (t) => t.name.toLowerCase() === targetToolName.toLowerCase()
        );

        if (tool && typeof tool.execute === 'function') {
            return {
                toolName: targetToolName,
                confidence: confidence,
                result: await tool.execute(userQuery)
            };
        }

        return { error: `Tool '${targetToolName}' discovered but not loaded in memory.` };
    }
}