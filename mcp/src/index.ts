#!/usr/bin/env node

/**
 * Playwright MCP Server for web search and content extraction.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { chromium, Browser, Page } from "playwright";
import * as cheerio from "cheerio";
import { z } from "zod";

// Tool schemas
const SearchToolSchema = z.object({
  query: z.string().describe("Search query"),
  engine: z.enum(["google", "duckduckgo", "bing"]).default("duckduckgo"),
  maxResults: z.number().default(10),
});

const ExtractContentSchema = z.object({
  url: z.string().url().describe("URL to extract content from"),
  selector: z.string().optional().describe("CSS selector for specific content"),
});

const NavigateSchema = z.object({
  url: z.string().url().describe("URL to navigate to"),
  actions: z.array(z.object({
    type: z.enum(["click", "type", "wait"]),
    selector: z.string().optional(),
    value: z.string().optional(),
  })).optional(),
});

const ScreenshotSchema = z.object({
  url: z.string().url().describe("URL to screenshot"),
  fullPage: z.boolean().default(false),
});

class PlaywrightMCPServer {
  private server: Server;
  private browser: Browser | null = null;

  constructor() {
    this.server = new Server(
      {
        name: "salutations-playwright-mcp",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => console.error("[MCP Error]", error);
    process.on("SIGINT", async () => {
      await this.cleanup();
      process.exit(0);
    });
  }

  private setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "web_search",
          description: "Search the web using various search engines",
          inputSchema: {
            type: "object",
            properties: {
              query: { type: "string", description: "Search query" },
              engine: { 
                type: "string", 
                enum: ["google", "duckduckgo", "bing"],
                default: "duckduckgo",
                description: "Search engine to use"
              },
              maxResults: { 
                type: "number", 
                default: 10,
                description: "Maximum number of results"
              },
            },
            required: ["query"],
          },
        },
        {
          name: "extract_content",
          description: "Extract content from a web page",
          inputSchema: {
            type: "object",
            properties: {
              url: { type: "string", description: "URL to extract from" },
              selector: { 
                type: "string", 
                description: "Optional CSS selector for specific content" 
              },
            },
            required: ["url"],
          },
        },
        {
          name: "navigate",
          description: "Navigate to a URL and perform actions",
          inputSchema: {
            type: "object",
            properties: {
              url: { type: "string", description: "URL to navigate to" },
              actions: {
                type: "array",
                description: "Actions to perform on the page",
                items: {
                  type: "object",
                  properties: {
                    type: { type: "string", enum: ["click", "type", "wait"] },
                    selector: { type: "string" },
                    value: { type: "string" },
                  },
                },
              },
            },
            required: ["url"],
          },
        },
        {
          name: "screenshot",
          description: "Take a screenshot of a web page",
          inputSchema: {
            type: "object",
            properties: {
              url: { type: "string", description: "URL to screenshot" },
              fullPage: { 
                type: "boolean", 
                default: false,
                description: "Capture full page"
              },
            },
            required: ["url"],
          },
        },
      ] as Tool[],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case "web_search":
            return await this.handleWebSearch(args);
          case "extract_content":
            return await this.handleExtractContent(args);
          case "navigate":
            return await this.handleNavigate(args);
          case "screenshot":
            return await this.handleScreenshot(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
        };
      }
    });
  }

  private async ensureBrowser(): Promise<Browser> {
    if (!this.browser) {
      this.browser = await chromium.launch({ 
        headless: process.env.PLAYWRIGHT_HEADLESS !== "false" 
      });
    }
    return this.browser;
  }

  private async handleWebSearch(args: any) {
    const { query, engine, maxResults } = SearchToolSchema.parse(args);
    const browser = await this.ensureBrowser();
    const page = await browser.newPage();

    try {
      let searchUrl: string;
      let resultSelector: string;

      switch (engine) {
        case "google":
          searchUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
          resultSelector = "div.g";
          break;
        case "bing":
          searchUrl = `https://www.bing.com/search?q=${encodeURIComponent(query)}`;
          resultSelector = "li.b_algo";
          break;
        case "duckduckgo":
        default:
          searchUrl = `https://duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
          resultSelector = "div.result";
          break;
      }

      await page.goto(searchUrl, { waitUntil: "networkidle" });
      const content = await page.content();
      const $ = cheerio.load(content);

      const results: any[] = [];
      $(resultSelector).slice(0, maxResults).each((i, elem) => {
        const $elem = $(elem);
        const title = $elem.find("h2, h3, a.result__a").first().text().trim();
        const link = $elem.find("a").first().attr("href");
        const snippet = $elem.find("div.result__snippet, div.b_caption p").first().text().trim();

        if (title && link) {
          results.push({ title, link, snippet });
        }
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({ query, engine, results }, null, 2),
          },
        ],
      };
    } finally {
      await page.close();
    }
  }

  private async handleExtractContent(args: any) {
    const { url, selector } = ExtractContentSchema.parse(args);
    const browser = await this.ensureBrowser();
    const page = await browser.newPage();

    try {
      await page.goto(url, { waitUntil: "networkidle" });
      
      let content: string;
      if (selector) {
        content = await page.locator(selector).textContent() || "";
      } else {
        // Extract main content
        content = await page.evaluate(() => {
          // Remove scripts, styles, etc.
          const clone = document.body.cloneNode(true) as HTMLElement;
          clone.querySelectorAll("script, style, nav, footer, header").forEach(el => el.remove());
          return clone.innerText;
        });
      }

      const title = await page.title();

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({ url, title, content: content.trim() }, null, 2),
          },
        ],
      };
    } finally {
      await page.close();
    }
  }

  private async handleNavigate(args: any) {
    const { url, actions } = NavigateSchema.parse(args);
    const browser = await this.ensureBrowser();
    const page = await browser.newPage();

    try {
      await page.goto(url, { waitUntil: "networkidle" });

      if (actions) {
        for (const action of actions) {
          switch (action.type) {
            case "click":
              if (action.selector) {
                await page.click(action.selector);
              }
              break;
            case "type":
              if (action.selector && action.value) {
                await page.fill(action.selector, action.value);
              }
              break;
            case "wait":
              await page.waitForTimeout(parseInt(action.value || "1000"));
              break;
          }
        }
      }

      const content = await page.content();
      const title = await page.title();

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({ url, title, success: true }, null, 2),
          },
        ],
      };
    } finally {
      await page.close();
    }
  }

  private async handleScreenshot(args: any) {
    const { url, fullPage } = ScreenshotSchema.parse(args);
    const browser = await this.ensureBrowser();
    const page = await browser.newPage();

    try {
      await page.goto(url, { waitUntil: "networkidle" });
      const screenshot = await page.screenshot({ 
        fullPage,
        type: "png",
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({ 
              url, 
              screenshot: screenshot.toString("base64"),
              fullPage 
            }, null, 2),
          },
        ],
      };
    } finally {
      await page.close();
    }
  }

  private async cleanup() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Playwright MCP server running on stdio");
  }
}

// Start server
const server = new PlaywrightMCPServer();
server.run().catch(console.error);
