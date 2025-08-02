#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import chokidar from 'chokidar';
import cron from 'node-cron';
import glob from 'fast-glob';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 🧠 INTELLIGENT MEMORY SYSTEM FOR JINASCRAPER
class IntelligentMemorySystem {
  constructor() {
    this.projectRoot = process.cwd();
    this.memoryFile = path.join(this.projectRoot, '.kiro', 'memory', 'project-memory.json');
    this.steeringMemoryFile = path.join(this.projectRoot, '.kiro', 'steering', 'project-memory.md');
    this.isMonitoring = false;
    this.watcher = null;
    this.patterns = new Map();
    this.technicalContext = new Map();
    
    this.initializeDirectories();
    this.loadPatterns();
  }

  initializeDirectories() {
    const dirs = [
      path.join(this.projectRoot, '.kiro', 'memory'),
      path.join(this.projectRoot, '.kiro', 'steering')
    ];
    dirs.forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  // 📊 CORE MEMORY OPERATIONS
  loadMemory() {
    try {
      if (!fs.existsSync(this.memoryFile)) {
        return {
          conversations: [],
          technical_changes: [],
          patterns: {},
          performance_metrics: [],
          steering_context: {},
          intelligent_reminders: [],
          auto_detected_changes: []
        };
      }
      return JSON.parse(fs.readFileSync(this.memoryFile, 'utf8'));
    } catch {
      return {
        conversations: [],
        technical_changes: [],
        patterns: {},
        performance_metrics: [],
        steering_context: {},
        intelligent_reminders: [],
        auto_detected_changes: []
      };
    }
  }

  saveMemory(memory) {
    fs.writeFileSync(this.memoryFile, JSON.stringify(memory, null, 2));
    this.updateSteeringMemory(memory);
  }

  // 🎯 SPECIALIZED SAVE OPERATIONS
  saveBugFix(description, files = [], impact = {}) {
    const memory = this.loadMemory();
    const entry = {
      timestamp: new Date().toISOString(),
      type: "bug_fix",
      category: "maintenance",
      description,
      files_modified: files,
      impact,
      tags: ["bug", "fix", "critical"],
      auto_detected: false
    };
    memory.technical_changes.push(entry);
    this.analyzeAndLearnPattern(entry);
    this.saveMemory(memory);
    return entry;
  }

  saveFeature(description, files = [], complexity = "medium") {
    const memory = this.loadMemory();
    const entry = {
      timestamp: new Date().toISOString(),
      type: "feature",
      category: "development",
      description,
      files_modified: files,
      complexity,
      tags: ["feature", "enhancement"],
      auto_detected: false
    };
    memory.technical_changes.push(entry);
    this.saveMemory(memory);
    return entry;
  }

  saveConfig(description, component, files = []) {
    const memory = this.loadMemory();
    const entry = {
      timestamp: new Date().toISOString(),
      type: "config",
      category: "configuration",
      description,
      component,
      files_modified: files,
      tags: ["config", "setup"],
      auto_detected: false
    };
    memory.technical_changes.push(entry);
    this.saveMemory(memory);
    return entry;
  }

  saveTestResult(description, results = {}) {
    const memory = this.loadMemory();
    const entry = {
      timestamp: new Date().toISOString(),
      type: "test_result",
      category: "testing",
      description,
      results,
      tags: ["test", "validation"],
      auto_detected: false
    };
    memory.technical_changes.push(entry);
    this.saveMemory(memory);
    return entry;
  }

  savePerformanceMetric(component, metrics = {}) {
    const memory = this.loadMemory();
    const entry = {
      timestamp: new Date().toISOString(),
      type: "performance",
      category: "metrics",
      component,
      metrics,
      tags: ["performance", "optimization"],
      auto_detected: true
    };
    memory.performance_metrics.push(entry);
    this.saveMemory(memory);
    return entry;
  }

  // 🔍 SEARCH AND ANALYSIS
  searchMemory(query, type = null) {
    const memory = this.loadMemory();
    const allEntries = [
      ...memory.conversations,
      ...memory.technical_changes,
      ...memory.auto_detected_changes
    ];

    const results = allEntries.filter(entry => {
      const matchesQuery = entry.description?.toLowerCase().includes(query.toLowerCase()) ||
                          entry.content?.toLowerCase().includes(query.toLowerCase());
      const matchesType = !type || entry.type === type;
      return matchesQuery && matchesType;
    });

    return results.sort((a, b) => new Date(b.timestamp || b.date) - new Date(a.timestamp || a.date));
  }

  // 🤖 AUTO-MONITORING SYSTEM
  startAutoMonitoring() {
    if (this.isMonitoring) return "⚠️ Monitoring déjà actif";

    this.watcher = chokidar.watch([
      'services/**/*.py',
      'core/**/*.py', 
      'config/**/*.py',
      'jinascraper/**/*.py',
      '.kiro/steering/**/*.md',
      '.kiro/specs/**/*.md'
    ], {
      ignored: /(^|[\/\\])\../,
      persistent: true,
      cwd: this.projectRoot
    });

    this.watcher.on('change', (filePath) => {
      this.analyzeFileChange(filePath);
    });

    this.isMonitoring = true;
    
    // Analyse périodique intelligente
    cron.schedule('*/30 * * * *', () => {
      this.generateIntelligentReminders();
    });

    return "✅ Monitoring automatique démarré - Surveillance en temps réel active";
  }

  stopAutoMonitoring() {
    if (this.watcher) {
      this.watcher.close();
      this.watcher = null;
    }
    this.isMonitoring = false;
    return "🛑 Monitoring automatique arrêté";
  }

  async analyzeFileChange(filePath) {
    const memory = this.loadMemory();
    const fullPath = path.join(this.projectRoot, filePath);
    
    try {
      const stats = fs.statSync(fullPath);
      const changeType = this.detectChangeType(filePath);
      const impact = await this.analyzeImpact(filePath);
      
      const autoEntry = {
        timestamp: new Date().toISOString(),
        type: changeType,
        category: "auto_detected",
        file_path: filePath,
        change_size: stats.size,
        impact,
        auto_detected: true,
        tags: this.generateTags(filePath, changeType)
      };

      memory.auto_detected_changes.push(autoEntry);
      this.technicalContext.set(filePath, autoEntry);
      
      // Mise à jour automatique des fichiers steering
      await this.updateSteeringFiles(autoEntry);
      
      this.saveMemory(memory);
    } catch (error) {
      console.error(`Erreur analyse fichier ${filePath}:`, error.message);
    }
  }

  detectChangeType(filePath) {
    if (filePath.includes('test')) return 'test';
    if (filePath.includes('config')) return 'config';
    if (filePath.includes('core')) return 'architecture';
    if (filePath.includes('services')) return 'service';
    if (filePath.includes('.md')) return 'documentation';
    return 'code_change';
  }

  async analyzeImpact(filePath) {
    // Analyse intelligente de l'impact
    const relatedFiles = await this.findRelatedFiles(filePath);
    const complexity = this.calculateComplexity(filePath);
    
    return {
      related_files: relatedFiles,
      complexity_score: complexity,
      risk_level: complexity > 7 ? 'high' : complexity > 4 ? 'medium' : 'low'
    };
  }

  async findRelatedFiles(filePath) {
    // Recherche des fichiers liés par imports/références
    try {
      const content = fs.readFileSync(path.join(this.projectRoot, filePath), 'utf8');
      const imports = content.match(/from\s+[\w.]+\s+import|import\s+[\w.]+/g) || [];
      return imports.slice(0, 5); // Limite à 5 pour éviter le spam
    } catch {
      return [];
    }
  }

  calculateComplexity(filePath) {
    try {
      const content = fs.readFileSync(path.join(this.projectRoot, filePath), 'utf8');
      const lines = content.split('\n').length;
      const functions = (content.match(/def\s+\w+/g) || []).length;
      const classes = (content.match(/class\s+\w+/g) || []).length;
      
      return Math.min(10, Math.floor((lines / 50) + (functions * 0.5) + (classes * 2)));
    } catch {
      return 1;
    }
  }

  generateTags(filePath, changeType) {
    const tags = [changeType];
    if (filePath.includes('stage1')) tags.push('stage1');
    if (filePath.includes('stage2')) tags.push('stage2');
    if (filePath.includes('jina')) tags.push('jina');
    if (filePath.includes('gemini')) tags.push('gemini');
    if (filePath.includes('redis')) tags.push('redis');
    return tags;
  }

  // 📚 STEERING FILES INTEGRATION
  async loadSteeringContext() {
    const steeringFiles = [
      '.kiro/steering/product.md',
      '.kiro/steering/tech.md', 
      '.kiro/steering/structure.md',
      '.kiro/specs/system-architecture-mapping/requirements.md',
      '.kiro/specs/system-architecture-mapping/design.md',
      '.kiro/specs/system-architecture-mapping/tasks.md'
    ];

    const context = {};
    for (const file of steeringFiles) {
      try {
        const fullPath = path.join(this.projectRoot, file);
        if (fs.existsSync(fullPath)) {
          context[path.basename(file, '.md')] = fs.readFileSync(fullPath, 'utf8');
        }
      } catch (error) {
        console.error(`Erreur lecture ${file}:`, error.message);
      }
    }
    return context;
  }

  async updateSteeringFiles(change) {
    const steeringContext = await this.loadSteeringContext();
    const memory = this.loadMemory();
    
    // Mise à jour du fichier project-memory.md
    const memoryContent = this.generateSteeringMemoryContent(memory, change);
    fs.writeFileSync(this.steeringMemoryFile, memoryContent);
  }

  updateSteeringMemory(memory) {
    const content = this.generateSteeringMemoryContent(memory);
    fs.writeFileSync(this.steeringMemoryFile, content);
  }

  generateSteeringMemoryContent(memory, latestChange = null) {
    let content = `# 🧠 Mémoire Intelligente du Projet JinaScraper\n\n`;
    content += `**Dernière mise à jour**: ${new Date().toISOString()}\n\n`;
    
    if (latestChange) {
      content += `## 🔥 Dernier Changement Détecté\n`;
      content += `- **Type**: ${latestChange.type}\n`;
      content += `- **Fichier**: ${latestChange.file_path}\n`;
      content += `- **Impact**: ${latestChange.impact?.risk_level || 'unknown'}\n`;
      content += `- **Tags**: ${latestChange.tags?.join(', ') || 'none'}\n\n`;
    }

    content += `## 📊 Statistiques Globales\n`;
    content += `- **Conversations**: ${memory.conversations?.length || 0}\n`;
    content += `- **Changements Techniques**: ${memory.technical_changes?.length || 0}\n`;
    content += `- **Changements Auto-détectés**: ${memory.auto_detected_changes?.length || 0}\n`;
    content += `- **Métriques Performance**: ${memory.performance_metrics?.length || 0}\n\n`;

    content += `## 🔧 Changements Techniques Récents\n`;
    const recentChanges = memory.technical_changes?.slice(-5) || [];
    recentChanges.forEach(change => {
      content += `### ${change.type.toUpperCase()} - ${new Date(change.timestamp).toLocaleDateString()}\n`;
      content += `- **Description**: ${change.description}\n`;
      content += `- **Fichiers**: ${change.files_modified?.join(', ') || 'N/A'}\n`;
      content += `- **Tags**: ${change.tags?.join(', ') || 'none'}\n\n`;
    });

    content += `## 🤖 Surveillance Automatique\n`;
    content += `- **Statut**: ${this.isMonitoring ? '✅ Active' : '❌ Inactive'}\n`;
    content += `- **Fichiers surveillés**: services/, core/, config/, .kiro/\n`;
    content += `- **Dernière analyse**: ${new Date().toISOString()}\n\n`;

    return content;
  }

  // 🧠 INTELLIGENT PATTERNS & REMINDERS
  analyzeAndLearnPattern(entry) {
    const key = `${entry.type}_${entry.category}`;
    if (!this.patterns.has(key)) {
      this.patterns.set(key, { count: 0, files: new Set(), impacts: [] });
    }
    
    const pattern = this.patterns.get(key);
    pattern.count++;
    entry.files_modified?.forEach(file => pattern.files.add(file));
    if (entry.impact) pattern.impacts.push(entry.impact);
  }

  loadPatterns() {
    const memory = this.loadMemory();
    memory.technical_changes?.forEach(change => {
      this.analyzeAndLearnPattern(change);
    });
  }

  generateIntelligentReminders() {
    const memory = this.loadMemory();
    const reminders = [];

    // Analyse des patterns récurrents
    for (const [patternKey, pattern] of this.patterns) {
      if (pattern.count >= 3) {
        reminders.push({
          type: 'pattern_alert',
          message: `🔔 PATTERN DÉTECTÉ: ${patternKey} s'est produit ${pattern.count} fois`,
          files_at_risk: Array.from(pattern.files),
          recommendation: `Considérez une refactorisation ou amélioration préventive`
        });
      }
    }

    // Analyse des performances
    const recentMetrics = memory.performance_metrics?.slice(-10) || [];
    if (recentMetrics.length >= 2) {
      const latest = recentMetrics[recentMetrics.length - 1];
      const previous = recentMetrics[recentMetrics.length - 2];
      
      if (latest.metrics?.execution_time > previous.metrics?.execution_time) {
        reminders.push({
          type: 'performance_degradation',
          message: `📊 PERFORMANCE: Dégradation détectée sur ${latest.component}`,
          recommendation: `Vérifiez les changements récents sur ce composant`
        });
      }
    }

    memory.intelligent_reminders = reminders;
    this.saveMemory(memory);
    return reminders;
  }

  getContextualReminders(filePath = null) {
    const memory = this.loadMemory();
    let reminders = memory.intelligent_reminders || [];

    if (filePath) {
      // Rappels spécifiques au fichier
      const fileHistory = memory.technical_changes?.filter(change => 
        change.files_modified?.includes(filePath)
      ) || [];

      if (fileHistory.length > 0) {
        reminders.push({
          type: 'file_history',
          message: `💡 HISTORIQUE: Ce fichier a été modifié ${fileHistory.length} fois`,
          last_change: fileHistory[fileHistory.length - 1],
          recommendation: `Dernière modification: ${fileHistory[fileHistory.length - 1].type}`
        });
      }
    }

    return reminders;
  }

  // 📈 SESSION SUMMARY & EXPORT
  generateSessionSummary() {
    const memory = this.loadMemory();
    const today = new Date().toISOString().split('T')[0];
    
    const todayChanges = memory.technical_changes?.filter(change => 
      change.timestamp.startsWith(today)
    ) || [];

    const summary = {
      date: today,
      total_changes: todayChanges.length,
      by_type: {},
      files_modified: new Set(),
      performance_impact: {},
      recommendations: []
    };

    todayChanges.forEach(change => {
      summary.by_type[change.type] = (summary.by_type[change.type] || 0) + 1;
      change.files_modified?.forEach(file => summary.files_modified.add(file));
    });

    summary.files_modified = Array.from(summary.files_modified);
    return summary;
  }

  exportMemoryMarkdown() {
    const memory = this.loadMemory();
    const summary = this.generateSessionSummary();
    
    let markdown = `# 📊 Rapport de Mémoire JinaScraper\n\n`;
    markdown += `**Généré le**: ${new Date().toISOString()}\n\n`;
    
    markdown += `## 📈 Résumé de Session\n`;
    markdown += `- **Changements aujourd'hui**: ${summary.total_changes}\n`;
    markdown += `- **Fichiers modifiés**: ${summary.files_modified.length}\n`;
    markdown += `- **Types de changements**: ${Object.keys(summary.by_type).join(', ')}\n\n`;

    markdown += `## 🔧 Changements Techniques\n`;
    memory.technical_changes?.slice(-10).forEach(change => {
      markdown += `### ${change.type.toUpperCase()} - ${new Date(change.timestamp).toLocaleDateString()}\n`;
      markdown += `${change.description}\n\n`;
    });

    const exportPath = path.join(this.projectRoot, '.kiro', 'memory', 'memory-export.md');
    fs.writeFileSync(exportPath, markdown);
    return exportPath;
  }
}

// 🚀 SERVER SETUP
const memorySystem = new IntelligentMemorySystem();

const server = new Server({
  name: "intelligent-memory",
  version: "2.0.0",
}, {
  capabilities: {
    tools: {},
  },
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      // 💾 BASIC MEMORY OPERATIONS
      {
        name: "save_memory",
        description: "Sauvegarde générale dans la mémoire",
        inputSchema: {
          type: "object",
          properties: {
            what_we_did: { type: "string", description: "Description de l'action" }
          },
          required: ["what_we_did"]
        }
      },
      {
        name: "get_memory", 
        description: "Affiche la mémoire complète du projet",
        inputSchema: { type: "object", properties: {} }
      },

      // 🎯 SPECIALIZED SAVE OPERATIONS
      {
        name: "save_bug_fix",
        description: "Sauvegarde une correction de bug avec contexte technique",
        inputSchema: {
          type: "object",
          properties: {
            description: { type: "string", description: "Description du bug corrigé" },
            files: { type: "array", items: { type: "string" }, description: "Fichiers modifiés" },
            impact: { type: "object", description: "Impact de la correction" }
          },
          required: ["description"]
        }
      },
      {
        name: "save_feature",
        description: "Sauvegarde l'ajout d'une nouvelle fonctionnalité",
        inputSchema: {
          type: "object", 
          properties: {
            description: { type: "string", description: "Description de la fonctionnalité" },
            files: { type: "array", items: { type: "string" }, description: "Fichiers modifiés" },
            complexity: { type: "string", enum: ["low", "medium", "high"], description: "Complexité" }
          },
          required: ["description"]
        }
      },
      {
        name: "save_config",
        description: "Sauvegarde un changement de configuration",
        inputSchema: {
          type: "object",
          properties: {
            description: { type: "string", description: "Description du changement" },
            component: { type: "string", description: "Composant configuré" },
            files: { type: "array", items: { type: "string" }, description: "Fichiers modifiés" }
          },
          required: ["description", "component"]
        }
      },
      {
        name: "save_test_result",
        description: "Sauvegarde le résultat d'un test",
        inputSchema: {
          type: "object",
          properties: {
            description: { type: "string", description: "Description du test" },
            results: { type: "object", description: "Résultats détaillés" }
          },
          required: ["description"]
        }
      },
      {
        name: "save_performance_metric",
        description: "Sauvegarde une métrique de performance",
        inputSchema: {
          type: "object",
          properties: {
            component: { type: "string", description: "Composant mesuré" },
            metrics: { type: "object", description: "Métriques collectées" }
          },
          required: ["component", "metrics"]
        }
      },

      // 🔍 SEARCH AND ANALYSIS
      {
        name: "search_memory",
        description: "Recherche dans l'historique de la mémoire",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "Terme à rechercher" },
            type: { type: "string", description: "Type de changement à filtrer" }
          },
          required: ["query"]
        }
      },

      // 🤖 AUTO-MONITORING
      {
        name: "start_auto_monitoring",
        description: "Démarre la surveillance automatique des fichiers",
        inputSchema: { type: "object", properties: {} }
      },
      {
        name: "stop_auto_monitoring", 
        description: "Arrête la surveillance automatique",
        inputSchema: { type: "object", properties: {} }
      },
      {
        name: "get_technical_context",
        description: "Récupère le contexte technique actuel",
        inputSchema: {
          type: "object",
          properties: {
            file_path: { type: "string", description: "Chemin du fichier (optionnel)" }
          }
        }
      },

      // 📚 STEERING INTEGRATION
      {
        name: "update_steering_files",
        description: "Met à jour les fichiers steering avec la mémoire",
        inputSchema: { type: "object", properties: {} }
      },
      {
        name: "get_steering_context",
        description: "Récupère le contexte des fichiers steering",
        inputSchema: { type: "object", properties: {} }
      },

      // 🧠 INTELLIGENT REMINDERS
      {
        name: "analyze_patterns",
        description: "Analyse les patterns récurrents dans l'historique",
        inputSchema: { type: "object", properties: {} }
      },
      {
        name: "get_intelligent_recommendations",
        description: "Obtient des recommandations basées sur l'historique",
        inputSchema: { type: "object", properties: {} }
      },
      {
        name: "get_contextual_reminders",
        description: "Obtient des rappels contextuels pour un fichier",
        inputSchema: {
          type: "object",
          properties: {
            file_path: { type: "string", description: "Chemin du fichier" }
          }
        }
      },

      // 📊 EXPORT AND SUMMARY
      {
        name: "generate_session_summary",
        description: "Génère un résumé de la session de travail",
        inputSchema: { type: "object", properties: {} }
      },
      {
        name: "export_memory_markdown",
        description: "Exporte la mémoire vers un fichier Markdown",
        inputSchema: { type: "object", properties: {} }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      // 💾 BASIC OPERATIONS
      case "save_memory": {
        const memory = memorySystem.loadMemory();
        memory.conversations.push({
          date: new Date().toISOString(),
          content: args.what_we_did
        });
        memorySystem.saveMemory(memory);
        return {
          content: [{ type: "text", text: `✅ Mémoire sauvegardée : ${args.what_we_did}` }]
        };
      }

      case "get_memory": {
        const memory = memorySystem.loadMemory();
        let response = "🧠 **Mémoire Intelligente du Projet JinaScraper**\n\n";
        
        response += `📊 **Statistiques Globales:**\n`;
        response += `• Conversations: ${memory.conversations?.length || 0}\n`;
        response += `• Changements techniques: ${memory.technical_changes?.length || 0}\n`;
        response += `• Auto-détections: ${memory.auto_detected_changes?.length || 0}\n`;
        response += `• Métriques performance: ${memory.performance_metrics?.length || 0}\n\n`;

        response += `📝 **Conversations récentes:**\n`;
        memory.conversations?.slice(-3).forEach(conv => {
          response += `• ${new Date(conv.date).toLocaleDateString()} : ${conv.content}\n`;
        });

        response += `\n🔧 **Changements techniques récents:**\n`;
        memory.technical_changes?.slice(-3).forEach(change => {
          response += `• ${change.type.toUpperCase()} (${new Date(change.timestamp).toLocaleDateString()}) : ${change.description}\n`;
        });

        response += `\n🤖 **Surveillance:** ${memorySystem.isMonitoring ? '✅ Active' : '❌ Inactive'}`;

        return { content: [{ type: "text", text: response }] };
      }

      // 🎯 SPECIALIZED SAVES
      case "save_bug_fix": {
        const entry = memorySystem.saveBugFix(args.description, args.files || [], args.impact || {});
        return {
          content: [{ type: "text", text: `🐛 Bug fix sauvegardé : ${args.description}\n📁 Fichiers: ${(args.files || []).join(', ') || 'N/A'}` }]
        };
      }

      case "save_feature": {
        const entry = memorySystem.saveFeature(args.description, args.files || [], args.complexity || "medium");
        return {
          content: [{ type: "text", text: `✨ Fonctionnalité sauvegardée : ${args.description}\n📁 Fichiers: ${(args.files || []).join(', ') || 'N/A'}` }]
        };
      }

      case "save_config": {
        const entry = memorySystem.saveConfig(args.description, args.component, args.files || []);
        return {
          content: [{ type: "text", text: `⚙️ Configuration sauvegardée : ${args.description}\n🔧 Composant: ${args.component}` }]
        };
      }

      case "save_test_result": {
        const entry = memorySystem.saveTestResult(args.description, args.results || {});
        return {
          content: [{ type: "text", text: `🧪 Test sauvegardé : ${args.description}` }]
        };
      }

      case "save_performance_metric": {
        const entry = memorySystem.savePerformanceMetric(args.component, args.metrics);
        return {
          content: [{ type: "text", text: `📊 Métrique sauvegardée pour ${args.component}` }]
        };
      }

      // 🔍 SEARCH
      case "search_memory": {
        const results = memorySystem.searchMemory(args.query, args.type);
        let response = `🔍 **Résultats de recherche pour "${args.query}":**\n\n`;
        
        if (results.length === 0) {
          response += "Aucun résultat trouvé.";
        } else {
          results.slice(0, 10).forEach(result => {
            const date = new Date(result.timestamp || result.date).toLocaleDateString();
            const desc = result.description || result.content;
            response += `• ${date} - ${result.type || 'conversation'}: ${desc.substring(0, 100)}...\n`;
          });
        }

        return { content: [{ type: "text", text: response }] };
      }

      // 🤖 AUTO-MONITORING
      case "start_auto_monitoring": {
        const result = memorySystem.startAutoMonitoring();
        return { content: [{ type: "text", text: result }] };
      }

      case "stop_auto_monitoring": {
        const result = memorySystem.stopAutoMonitoring();
        return { content: [{ type: "text", text: result }] };
      }

      case "get_technical_context": {
        let response = "🔧 **Contexte Technique Actuel:**\n\n";
        
        if (args.file_path && memorySystem.technicalContext.has(args.file_path)) {
          const context = memorySystem.technicalContext.get(args.file_path);
          response += `📁 **Fichier:** ${args.file_path}\n`;
          response += `🕒 **Dernière modification:** ${new Date(context.timestamp).toLocaleString()}\n`;
          response += `🏷️ **Type:** ${context.type}\n`;
          response += `⚠️ **Risque:** ${context.impact?.risk_level || 'unknown'}\n`;
        } else {
          response += `📊 **Fichiers surveillés:** ${memorySystem.technicalContext.size}\n`;
          response += `🤖 **Monitoring actif:** ${memorySystem.isMonitoring ? 'Oui' : 'Non'}\n`;
        }

        return { content: [{ type: "text", text: response }] };
      }

      // 📚 STEERING
      case "update_steering_files": {
        await memorySystem.updateSteeringFiles();
        return { content: [{ type: "text", text: "📚 Fichiers steering mis à jour avec la mémoire actuelle" }] };
      }

      case "get_steering_context": {
        const context = await memorySystem.loadSteeringContext();
        let response = "📚 **Contexte Steering:**\n\n";
        
        Object.keys(context).forEach(file => {
          response += `📄 **${file}:** ${context[file].substring(0, 200)}...\n\n`;
        });

        return { content: [{ type: "text", text: response }] };
      }

      // 🧠 INTELLIGENCE
      case "analyze_patterns": {
        const reminders = memorySystem.generateIntelligentReminders();
        let response = "🧠 **Analyse des Patterns:**\n\n";
        
        if (reminders.length === 0) {
          response += "Aucun pattern significatif détecté pour le moment.";
        } else {
          reminders.forEach(reminder => {
            response += `${reminder.message}\n💡 ${reminder.recommendation}\n\n`;
          });
        }

        return { content: [{ type: "text", text: response }] };
      }

      case "get_intelligent_recommendations": {
        const reminders = memorySystem.generateIntelligentReminders();
        let response = "💡 **Recommandations Intelligentes:**\n\n";
        
        reminders.forEach(reminder => {
          response += `🎯 **${reminder.type.toUpperCase()}**\n`;
          response += `${reminder.message}\n`;
          response += `💡 ${reminder.recommendation}\n\n`;
        });

        return { content: [{ type: "text", text: response }] };
      }

      case "get_contextual_reminders": {
        const reminders = memorySystem.getContextualReminders(args.file_path);
        let response = `🔔 **Rappels Contextuels${args.file_path ? ` pour ${args.file_path}` : ''}:**\n\n`;
        
        if (reminders.length === 0) {
          response += "Aucun rappel contextuel pour le moment.";
        } else {
          reminders.forEach(reminder => {
            response += `${reminder.message}\n💡 ${reminder.recommendation}\n\n`;
          });
        }

        return { content: [{ type: "text", text: response }] };
      }

      // 📊 EXPORT
      case "generate_session_summary": {
        const summary = memorySystem.generateSessionSummary();
        let response = `📊 **Résumé de Session - ${summary.date}:**\n\n`;
        response += `• **Total changements:** ${summary.total_changes}\n`;
        response += `• **Fichiers modifiés:** ${summary.files_modified.length}\n`;
        response += `• **Types de changements:** ${Object.entries(summary.by_type).map(([type, count]) => `${type}(${count})`).join(', ')}\n`;

        return { content: [{ type: "text", text: response }] };
      }

      case "export_memory_markdown": {
        const exportPath = memorySystem.exportMemoryMarkdown();
        return { content: [{ type: "text", text: `📄 Mémoire exportée vers: ${exportPath}` }] };
      }

      default:
        return { content: [{ type: "text", text: `❌ Outil inconnu: ${name}` }] };
    }
  } catch (error) {
    return { content: [{ type: "text", text: `❌ Erreur: ${error.message}` }] };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('🧠 Intelligent Memory System démarré - Toutes les fonctionnalités activées !');
}

main().catch(console.error);