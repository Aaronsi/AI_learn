/**
 * Example 2: Weather Agent with Streaming
 * Demonstrates streaming responses and real-time event handling
 */

import { SimpleAgent, Tool, AgentEvent } from "../src";

// Mock weather data
const weatherData: Record<string, any> = {
  tokyo: { temp: 22, condition: "sunny", humidity: 60 },
  london: { temp: 15, condition: "cloudy", humidity: 75 },
  "new york": { temp: 18, condition: "rainy", humidity: 80 },
  paris: { temp: 20, condition: "partly cloudy", humidity: 65 },
  sydney: { temp: 25, condition: "sunny", humidity: 55 },
};

// Define weather tools
const weatherTools: Tool[] = [
  {
    name: "get_weather",
    description: "Get current weather information for a city",
    parameters: {
      type: "object",
      properties: {
        city: {
          type: "string",
          description: "The city name (e.g., 'Tokyo', 'London')",
        },
      },
      required: ["city"],
    },
    execute: async (args: any) => {
      const city = args.city.toLowerCase();
      const weather = weatherData[city];

      if (!weather) {
        return {
          output: "",
          error: `Weather data not available for ${args.city}`,
        };
      }

      return {
        output: JSON.stringify({
          city: args.city,
          temperature: weather.temp,
          condition: weather.condition,
          humidity: weather.humidity,
        }),
      };
    },
  },
  {
    name: "get_forecast",
    description: "Get 3-day weather forecast for a city",
    parameters: {
      type: "object",
      properties: {
        city: {
          type: "string",
          description: "The city name",
        },
      },
      required: ["city"],
    },
    execute: async (args: any) => {
      // Mock forecast data
      const forecast = [
        { day: "Today", temp: 22, condition: "sunny" },
        { day: "Tomorrow", temp: 24, condition: "partly cloudy" },
        { day: "Day 3", temp: 21, condition: "rainy" },
      ];

      return {
        output: JSON.stringify({
          city: args.city,
          forecast,
        }),
      };
    },
  },
];

async function main() {
  console.log("🌤️  Weather Agent with Streaming\n");

  // Create the agent
  const agent = new SimpleAgent({
    model: "deepseek-chat",
    systemPrompt:
      "You are a helpful weather assistant. Provide weather information in a friendly and conversational way.",
    temperature: 0.7,
  });

  // Add weather tools
  agent.addTools(weatherTools);

  // Create a session
  const session = agent.createSession();

  console.log("Session created:", session.id);
  console.log("Available tools:", agent.listTools().map((t) => t.name).join(", "));
  console.log();

  // Example 1: Streaming response
  console.log("Example 1: Streaming response");
  console.log("User: What's the weather like in Tokyo?\n");

  let fullResponse = "";
  for await (const event of agent.stream(
    session.id,
    "What's the weather like in Tokyo?"
  )) {
    handleEvent(event);
    if (event.type === "text") {
      fullResponse += event.text;
    }
  }
  console.log("\n");

  // Example 2: Multi-city comparison with streaming
  console.log("Example 2: Multi-city comparison");
  console.log("User: Compare the weather in London and Paris\n");

  for await (const event of agent.stream(
    session.id,
    "Compare the weather in London and Paris"
  )) {
    handleEvent(event);
  }
  console.log("\n");

  // Example 3: Forecast request
  console.log("Example 3: Forecast request");
  console.log("User: What's the forecast for Sydney?\n");

  for await (const event of agent.stream(
    session.id,
    "What's the forecast for Sydney?"
  )) {
    handleEvent(event);
  }
  console.log("\n");

  // Clean up
  await agent.cleanup();
  console.log("✓ Done!");
}

function handleEvent(event: AgentEvent) {
  switch (event.type) {
    case "message_start":
      process.stdout.write("Assistant: ");
      break;

    case "text":
      process.stdout.write(event.text);
      break;

    case "tool_call":
      console.log(`\n  🔧 Using tool: ${event.name}`);
      console.log(`     Arguments: ${JSON.stringify(event.args)}`);
      break;

    case "tool_result":
      if (event.isError) {
        console.log(`  ❌ Error: ${event.result}`);
      } else {
        console.log(`  ✓ Result received`);
      }
      process.stdout.write("Assistant: ");
      break;

    case "message_end":
      // Just continue, text is already printed
      break;

    case "error":
      console.error("\n❌ Error:", event.error.message);
      break;
  }
}

main().catch(console.error);
