import { ItemView, WorkspaceLeaf, Notice, App, TFile } from 'obsidian'; // Added App, TFile
import { OpenAIService, OpenAIMessage } from './OpenAIService';
import ChatBotPlugin from './main';

export const CHAT_VIEW_TYPE = "chatbot-view";

const INITIAL_SYSTEM_MESSAGE: OpenAIMessage = {
  role: 'system',
  content: 'You are a helpful AI assistant integrated into Obsidian. Be concise and helpful. Users may provide context from their notes.'
};

export class ChatView extends ItemView {
  private plugin: ChatBotPlugin;
  private openAIService: OpenAIService;
  private messagesEl: HTMLDivElement;
  private inputEl: HTMLInputElement;
  private sendButtonEl: HTMLButtonElement;
  private clearChatButtonEl: HTMLButtonElement;
  private useNoteContextButtonEl: HTMLButtonElement; // Button for active note context
  private loadingEl: HTMLDivElement | null = null;

  private chatHistory: OpenAIMessage[] = [];

  constructor(leaf: WorkspaceLeaf, plugin: ChatBotPlugin) {
    super(leaf);
    this.plugin = plugin;
    this.openAIService = new OpenAIService(this.plugin.settings.openAiApiKey);
    this.initializeChatHistory();
  }

  private initializeChatHistory(): void {
    this.chatHistory = [INITIAL_SYSTEM_MESSAGE];
  }

  getViewType(): string {
    return CHAT_VIEW_TYPE;
  }

  getDisplayText(): string {
    return "ChatBot";
  }

  async onOpen(): Promise<void> {
    this.openAIService = new OpenAIService(this.plugin.settings.openAiApiKey);
    if (this.chatHistory.length === 0 || (this.chatHistory.length === 1 && this.chatHistory[0].role === 'system')) {
        // If history is empty or only contains the initial system message, re-initialize.
        // This handles cases where the view is re-opened and we want to ensure the base system message is there.
        this.initializeChatHistory();
    }

    const container = this.containerEl.children[1];
    container.empty();

    const chatInterfaceEl = container.createDiv({ cls: "chat-interface" });

    const headerEl = chatInterfaceEl.createDiv({cls: "chat-header"});
    this.useNoteContextButtonEl = headerEl.createEl('button', {
        text: 'Use Active Note',
        cls: 'use-note-context-button'
    });
    this.useNoteContextButtonEl.setAttribute('aria-label', 'Use content of active note as context');
    this.useNoteContextButtonEl.addEventListener('click', this.handleUseActiveNoteContext.bind(this));

    this.clearChatButtonEl = headerEl.createEl('button', {text: 'Clear Chat', cls: 'clear-chat-button'});
    this.clearChatButtonEl.addEventListener('click', this.handleClearChat.bind(this));


    this.messagesEl = chatInterfaceEl.createDiv({ cls: "chat-messages" });
    this.chatHistory.forEach(msg => {
        if (msg.role !== 'system' || msg.content.includes("--- Begin Context from Note:")) {
            // Display user, assistant, error messages, and also system messages that are note contexts
             this.addMessageToView(msg.content, msg.role as 'user' | 'assistant' | 'error' | 'system-display');
        }
    });

    const inputAreaEl = chatInterfaceEl.createDiv({ cls: "chat-input-area" });
    this.inputEl = inputAreaEl.createEl("input", { type: "text", cls: "chat-input" });
    this.inputEl.placeholder = "Type your message...";

    this.sendButtonEl = inputAreaEl.createEl("button", { text: "Send", cls: "chat-send-button" });

    this.sendButtonEl.addEventListener('click', this.handleSendMessage.bind(this));
    this.inputEl.addEventListener('keypress', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        this.handleSendMessage();
      }
    });

    // Focus the input field when the view is opened
    this.inputEl.focus();
  }

  // Public method to be callable from command
  public async handleUseActiveNoteContext(): Promise<void> {
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile) {
      new Notice("No active file to use as context.");
      return;
    }
    if (activeFile.extension !== 'md') {
      new Notice("Can only use Markdown files (.md) as context.");
      return;
    }

    let noteContent = "";
    try {
      noteContent = await this.app.vault.read(activeFile);
    } catch (error) {
      console.error("Error reading active file for context:", error);
      new Notice("Error reading file content. Check console.");
      return;
    }

    // Simple check for very large notes (e.g. > 100k chars, roughly > 25k tokens)
    // This is a very basic check. A more sophisticated approach would involve actual token counting.
    if (noteContent.length > 100000) {
        new Notice(`Note "${activeFile.basename}" may be too large (${(noteContent.length/1000).toFixed(1)}k chars). Consider summarizing or selecting relevant parts. Context still added.`, 10000); // Long notice
    } else if (noteContent.length > 20000) {
        new Notice(`Context from "${activeFile.basename}" added. Note is quite large, this may consume many tokens.`, 7000);
    }


    const contextMessageContent = `--- Begin Context from Note: ${activeFile.basename} ---\n${noteContent}\n--- End Context from Note: ${activeFile.basename} ---`;

    this.chatHistory.push({ role: 'system', content: contextMessageContent });

    const displayMessage = `Context from "${activeFile.basename}" has been added to the conversation for the AI.`;
    this.addMessageToView(displayMessage, 'system-display');
    new Notice(displayMessage);
  }


  private addMessageToView(message: string, sender: 'user' | 'assistant' | 'error' | 'loading' | 'system-display'): HTMLDivElement {
    const messageContainerDiv = this.messagesEl.createDiv({ cls: `message ${sender}-message` });

    const messageContentSpan = messageContainerDiv.createSpan({ cls: 'message-content' });
    if (sender === 'system-display' || sender === 'error' || sender === 'loading') {
        messageContentSpan.textContent = message;
    } else {
        // For user and assistant messages, we might want to render markdown later.
        // For now, textContent is safer. If rendering markdown, ensure sanitization.
        messageContentSpan.textContent = message;
    }

    if (sender === 'assistant') {
      const exportButton = messageContainerDiv.createEl('button', {
        cls: 'export-button',
        text: 'Export Note'
      });
      exportButton.setAttribute('aria-label', 'Export message to new note');
      exportButton.addEventListener('click', () => this.handleExportMessage(message));
    }

    this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    return messageContainerDiv;
  }

  private async handleExportMessage(messageContent: string): Promise<void> {
    const now = new Date();
    const timestamp = now.toISOString().replace(/[:.]/g, '-');
    const shortPreview = messageContent.substring(0, 30).replace(/[^a-zA-Z0-9 ]/g, "").trim().replace(/\s+/g, '_');
    const filename = `ChatExport_${shortPreview || 'note'}_${timestamp}.md`;

    const exportFolder = this.plugin.settings.exportFolder || '';
    const filePath = `${exportFolder}${exportFolder ? '/' : ''}${filename}`;

    const noteTitle = `ChatBot Export - ${now.toLocaleString()}`;
    const noteBody = `${messageContent}\n\n#chatbot #export`;
    const noteContent = `# ${noteTitle}\n\n${noteBody}`;

    try {
      const file = await this.app.vault.create(filePath, noteContent);
      new Notice(`Message exported to: ${file.path}`);
    } catch (error) {
      console.error("Error exporting message to note:", error);
      new Notice(`Error exporting message: ${error.message || 'Check console for details.'}`);
    }
  }

  private handleClearChat(): void {
    this.initializeChatHistory();
    this.messagesEl.empty();
    this.addMessageToView("Chat history cleared.", 'system-display');
    new Notice("Chat history cleared.");
  }

  private removeLoadingIndicator(): void {
    if (this.loadingEl) {
      this.loadingEl.remove();
      this.loadingEl = null;
    }
  }

  private async handleSendMessage(): Promise<void> {
    if (!this.plugin.settings.openAiApiKey || this.plugin.settings.openAiApiKey.trim() === '') {
      this.removeLoadingIndicator();
      this.addMessageToView("Error: OpenAI API Key not configured. Please set it in the ChatBot plugin settings.", 'error');
      new Notice("OpenAI API Key not set. Please configure it in the ChatBot plugin settings.");
      return;
    }
    this.openAIService = new OpenAIService(this.plugin.settings.openAiApiKey);

    const userInputText = this.inputEl.value.trim();
    if (!userInputText) {
      return;
    }

    this.addMessageToView(userInputText, 'user');
    this.inputEl.value = '';
    this.inputEl.focus(); // Keep focus in input after sending

    this.removeLoadingIndicator();
    this.loadingEl = this.addMessageToView("Thinking...", 'loading');

    const currentUserMessageForApi: OpenAIMessage = { role: 'user', content: userInputText };
    const messagesToSend: OpenAIMessage[] = [...this.chatHistory, currentUserMessageForApi];

    try {
      const assistantReply = await this.openAIService.getChatCompletion(messagesToSend);
      this.removeLoadingIndicator();

      if (assistantReply && !assistantReply.toLowerCase().startsWith("error:")) {
        this.addMessageToView(assistantReply, 'assistant');
        this.chatHistory.push(currentUserMessageForApi);
        this.chatHistory.push({ role: 'assistant', content: assistantReply });
      } else {
        this.addMessageToView(assistantReply || 'An unexpected error occurred.', 'error');
      }
    } catch (error) {
        this.removeLoadingIndicator();
        console.error("ChatView: Error calling getChatCompletion", error);
        this.addMessageToView(error instanceof Error ? error.message : String(error), 'error');
    }
  }

  async onClose(): Promise<void> {
    console.log("ChatBot view closed");
  }
}
