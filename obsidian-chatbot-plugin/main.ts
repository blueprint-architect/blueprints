import { App, Plugin, PluginSettingTab, Setting, WorkspaceLeaf } from 'obsidian';
import { ChatView, CHAT_VIEW_TYPE } from './ChatView';

export interface ChatBotSettings {
  openAiApiKey: string;
  exportFolder?: string; // Optional: folder for exports
  // other settings can be added later
}

const DEFAULT_SETTINGS: ChatBotSettings = {
  openAiApiKey: '',
  exportFolder: '',
};

export default class ChatBotPlugin extends Plugin {
  settings: ChatBotSettings;

  async onload() {
    console.log('Loading Obsidian ChatBot plugin');
    await this.loadSettings();

    this.registerView(
      CHAT_VIEW_TYPE,
      (leaf) => new ChatView(leaf, this)
    );

    this.addRibbonIcon('message-circle', 'ChatBot', () => {
      this.activateView();
    });

    this.addSettingTab(new ChatBotSettingTab(this.app, this));

    this.addCommand({
      id: 'open-chatbot-view',
      name: 'Open ChatBot',
      callback: () => {
        this.activateView();
      }
    });

    this.addCommand({
      id: 'use-active-note-context-command',
      name: 'ChatBot: Use Active Note as Context',
      checkCallback: (checking: boolean) => {
        // Check if the chat view is open and active
        const chatViewLeaf = this.app.workspace.getLeavesOfType(CHAT_VIEW_TYPE)[0];
        if (chatViewLeaf) {
          const chatView = chatViewLeaf.view;
          // Ensure it's an instance of ChatView and the method exists
          if (chatView instanceof ChatView && typeof chatView.handleUseActiveNoteContext === 'function') {
            if (!checking) {
              chatView.handleUseActiveNoteContext();
            }
            return true; // Command is available
          }
        }
        return false; // Command is not available
      }
    });
  }

  onunload() {
    console.log('Unloading Obsidian ChatBot plugin');
    this.app.workspace.detachLeavesOfType(CHAT_VIEW_TYPE);
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  async activateView() {
    const existingLeaves = this.app.workspace.getLeavesOfType(CHAT_VIEW_TYPE);
    if (existingLeaves.length > 0) {
      this.app.workspace.revealLeaf(existingLeaves[0]);
      return;
    }

    let leaf: WorkspaceLeaf | undefined = this.app.workspace.getRightLeaf(false);
    if (!leaf) {
        leaf = this.app.workspace.getLeaf(true);
    }

    if (leaf) {
        await leaf.setViewState({
          type: CHAT_VIEW_TYPE,
          active: true,
        });
        this.app.workspace.revealLeaf(leaf);
    } else {
        console.error("Obsidian ChatBot: Could not get a workspace leaf to activate the view.");
    }
  }
}

class ChatBotSettingTab extends PluginSettingTab {
  plugin: ChatBotPlugin;

  constructor(app: App, plugin: ChatBotPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const {containerEl} = this;
    containerEl.empty();
    containerEl.createEl('h2', {text: 'Obsidian ChatBot Settings'});

    new Setting(containerEl)
      .setName('OpenAI API Key')
      .setDesc('Enter your OpenAI API key to enable the chatbot. Remember to keep your API key confidential.')
      .addText(text => text
        .setPlaceholder('sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        .setValue(this.plugin.settings.openAiApiKey)
        .onChange(async (value) => {
          this.plugin.settings.openAiApiKey = value.trim();
          await this.plugin.saveSettings();
        }));

    // Placeholder for export folder setting - UI can be added later
    new Setting(containerEl)
      .setName('Export Folder Path (Optional)')
      .setDesc('Specify a folder path where exported notes will be saved. If empty, notes are saved in the vault root. Example: ChatBotExports/Summaries')
      .addText(text => text
        .setPlaceholder('e.g., ChatBot/Exports')
        .setValue(this.plugin.settings.exportFolder || '')
        .onChange(async (value) => {
            // Ensure no leading/trailing slashes for consistency, or handle them robustly
            this.plugin.settings.exportFolder = value.trim().replace(/^\/+|\/+$/g, '');
            await this.plugin.saveSettings();
        }));

  }
}
