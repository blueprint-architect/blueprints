// OpenAIService.ts

export interface OpenAIMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

interface OpenAIChoice {
  message: OpenAIMessage;
  finish_reason?: string;
}

export interface OpenAIChatResponse {
  id?: string;
  object?: string;
  created?: number;
  model?: string;
  choices: OpenAIChoice[];
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export class OpenAIService {
  private apiKey: string;
  private readonly OPENAI_API_URL = "https://api.openai.com/v1/chat/completions";

  constructor(apiKey: string) {
    this.apiKey = apiKey;
    if (!this.apiKey || this.apiKey.trim() === '') {
      console.warn(
        "OpenAIService: API Key is not set or is empty. " +
        "The service will not be functional until a valid API key is provided."
      );
    }
  }

  public async getChatCompletion(messages: OpenAIMessage[], model: string = "gpt-3.5-turbo"): Promise<string | null> {
    if (!this.apiKey || this.apiKey.trim() === '') {
      console.error("OpenAIService: API Key is not configured.");
      return "Error: OpenAI API Key not configured. Please set it in the plugin settings.";
    }

    const requestBody = {
      model: model,
      messages: messages,
    };

    try {
      const response = await fetch(this.OPENAI_API_URL, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: "Failed to parse error JSON." }));
        console.error(
          `OpenAIService: API request failed with status ${response.status}: ${response.statusText}`,
          errorData
        );
        return `Error: API request failed - ${errorData.error?.message || response.statusText || 'Unknown error'}`;
      }

      const responseData: OpenAIChatResponse = await response.json();

      if (responseData.choices && responseData.choices.length > 0 && responseData.choices[0].message) {
        return responseData.choices[0].message.content.trim();
      } else {
        console.error("OpenAIService: Invalid response structure from API", responseData);
        return "Error: Received an invalid response structure from the AI.";
      }
    } catch (error) {
      console.error("OpenAIService: Network or other error during API call", error);
      if (error instanceof TypeError) {
        return `Error: Network error - ${error.message}. This might be due to an invalid API key, network connectivity issues, or CORS policy if running in a misconfigured browser-like environment.`;
      }
      return `Error: An unexpected error occurred while contacting the AI: ${error instanceof Error ? error.message : String(error)}`;
    }
  }
}
