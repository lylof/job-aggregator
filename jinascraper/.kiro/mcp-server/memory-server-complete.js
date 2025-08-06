#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 🏗️ ARCHITECTURE ROBUSTE - SÉPARATION DES RESPONSABILITÉS

/**
 * Gestionnaire de chemins robuste et portable
 */
class PathManager {
  static findProjectRoot(startPath = process.cwd()) {
    let current = path.resolve(startPath);
    
    while (current !== path.dirname(current)) {
      if (fs.existsSync(path.join(current, '.kiro'))) {
        return current;
      }
      if (fs.existsSync(path.join(current, 'package.json'))) {
        try {
          const pkg = JSON.parse(fs.readFileSync(path.join(current, 'package.json'), 'utf8'));
          if (pkg.name && pkg.name.includes('jinascraper')) {
            return current;
          }
        } catch {}
      }
      current = path.dirname(current);
    }
    
    throw new Error('Project root not found - no .kiro directory found in parent directories');
  }
  
  static getMemoryFile(projectRoot) {
    return path.join(projectRoot, '.kiro', 'memory', 'project-memory.json');
  }
  
  static getSteeringFile(projectRoot) {
    return path.join(projectRoot, '.kiro', 'steering', 'project-memory.md');
  }
}

/**
 * Gestionnaire de système de fichiers avec validation
 */
class FileSystemManager {
  static ensureDirectoryExists(dirPath) {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }
  
  static validateAndRepairStructure(projectRoot) {
    const requiredDirs = [
      path.join(projectRoot, '.kiro'),
      path.join(projectRoot, '.kiro', 'memory'),
      path.join(projectRoot, '.kiro', 'steering')
    ];
    
    requiredDirs.forEach(dir => this.ensureDirectoryExists(dir));
    
    // Détecter et nettoyer les structures récursives
    const recursiveKiro = path.join(projectRoot, '.kiro', '.kiro');
    if (fs.existsSync(recursiveKiro)) {
      console.warn('🚨 Structure récursive détectée, nettoyage...');
      fs.rmSync(recursiveKiro, { recursive: true, force: true });
    }
  }
}

/**
 * Service de mémoire avec logique métier complète
 */
class MemoryService {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
    this.memoryFile = PathManager.getMemoryFile(projectRoot);
    this.steeringFile = PathManager.getSteeringFile(projectRoot);
    
    FileSystemManager.validateAndRepairStructure(projectRoot);
  }
  
  loadMemory() {
    try {
      if (!fs.existsSync(this.memoryFile)) {
        return this.getDefaultMemory();
      }
      const data = JSON.parse(fs.readFileSync(this.memoryFile, 'utf8'));
      return this.validateMemoryStructure(data);
    } catch (error) {
      console.warn(`Erreur lecture mémoire: ${error.message}, utilisation structure par défaut`);
      return this.getDefaultMemory();
    }
  }
  
  saveMemory(memory) {
    const validatedMemory = this.validateMemoryStructure(memory);
    fs.writeFileSync(this.memoryFile, JSON.stringify(validatedMemory, null, 2));
    this.updateSteeringMemory(validatedMemory);
  }
  
  getDefaultMemory() {
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
  
  validateMemoryStructure(memory) {
    const defaultMemory = this.getDefaultMemory();
    const validated = { ...defaultMemory };
    
    Object.keys(defaultMemory).forEach(key => {
      if (memory[key] !== undefined) {
        validated[key] = memory[key];
      }
    });
    
    return validated;
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
    const results = [];
    
    // Recherche dans les conversations
    memory.conversations?.forEach(conv => {
      if (conv.content.toLowerCase().includes(query.toLowerCase())) {
        results.push({ type: 'conversation', data: conv });
      }
    });
    
    // Recherche dans les changements techniques
    memory.technical_changes?.forEach(change => {
      if (change.description.toLowerCase().includes(query.toLowerCase())) {
        results.push({ type: 'technical_change', data: change });
      }
    });
    
    return type ? results.filter(r => r.type === type) : results;
  }
  
  updateSteeringMemory(memory) {
    const summary = this.generateMemorySummary(memory);
    fs.writeFileSync(this.steeringFile, summary);
  }
  
  generateMemorySummary(memory) {
    const now = new Date().toISOString();
    const conversations = memory.conversations || [];
    const technicalChanges = memory.technical_changes || [];
    const metrics = memory.performance_metrics || [];
    
    return `# 🧠 Mémoire Intelligente du Projet JinaScraper

**Dernière mise à jour**: ${now}

## 📊 Statistiques Globales
- **Conversations**: ${conversations.length}
- **Changements Techniques**: ${technicalChanges.length}
- **Changements Auto-détectés**: ${memory.auto_detected_changes?.length || 0}
- **Métriques Performance**: ${metrics.length}

## 🔧 Changements Techniques Récents
${technicalChanges.slice(-3).map(change => 
  `### ${change.type?.toUpperCase()} - ${new Date(change.timestamp).toLocaleDateString()}
- **Description**: ${change.description}
- **Fichiers**: ${change.files_modified?.join(', ') || 'N/A'}
- **Tags**: ${change.tags?.join(', ') || 'N/A'}`
).join('\n\n')}

## 🤖 Surveillance Automatique
- **Statut**: ❌ Inactive
- **Fichiers surveillés**: services/, core/, config/, .kiro/
- **Dernière analyse**: ${now}

`;
  }
}

// 🚀 SERVEUR MCP COMPLET
const memoryService = new MemoryService(PathManager.findProjectRoot());

const server = new Server({
  name: "intelligent-memory-complete",
  version: "3.1.0",
}, {
  capabilities: {
    tools: {},
  },
});

// Configuration complète des outils MCP
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
        description: "Recherche dans la mémoire du projet",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "Terme à rechercher" },
            type: { type: "string", enum: ["conversation", "technical_change"], description: "Type de résultat" }
          },
          required: ["query"]
        }
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
        const memory = memoryService.loadMemory();
        memory.conversations.push({
          date: new Date().toISOString(),
          content: args.what_we_did
        });
        memoryService.saveMemory(memory);
        return {
          content: [{ type: "text", text: `✅ Mémoire sauvegardée : ${args.what_we_did}` }]
        };
      }
      
      case "get_memory": {
        const memory = memoryService.loadMemory();
        const summary = `🧠 **Mémoire Intelligente du Projet JinaScraper**

📊 **Statistiques Globales:**
• Conversations: ${memory.conversations?.length || 0}
• Changements techniques: ${memory.technical_changes?.length || 0}
• Auto-détections: ${memory.auto_detected_changes?.length || 0}
• Métriques performance: ${memory.performance_metrics?.length || 0}

📝 **Conversations récentes:**
${(memory.conversations || []).slice(-3).map(conv => 
  `• ${new Date(conv.date).toLocaleDateString()} : ${conv.content}`
).join('\n')}

🔧 **Changements techniques récents:**
${(memory.technical_changes || []).slice(-3).map(change => 
  `• ${change.type?.toUpperCase()} (${new Date(change.timestamp).toLocaleDateString()}) : ${change.description}`
).join('\n')}

🤖 **Surveillance:** ❌ Inactive`;
        
        return {
          content: [{ type: "text", text: summary }]
        };
      }

      // 🎯 SPECIALIZED SAVES
      case "save_bug_fix": {
        const entry = memoryService.saveBugFix(args.description, args.files || [], args.impact || {});
        return {
          content: [{ type: "text", text: `🐛 Bug fix sauvegardé : ${args.description}\n📁 Fichiers: ${(args.files || []).join(', ') || 'N/A'}` }]
        };
      }

      case "save_feature": {
        const entry = memoryService.saveFeature(args.description, args.files || [], args.complexity || "medium");
        return {
          content: [{ type: "text", text: `✨ Fonctionnalité sauvegardée : ${args.description}\n📁 Fichiers: ${(args.files || []).join(', ') || 'N/A'}` }]
        };
      }

      case "save_config": {
        const entry = memoryService.saveConfig(args.description, args.component, args.files || []);
        return {
          content: [{ type: "text", text: `⚙️ Configuration sauvegardée : ${args.description}\n🔧 Composant: ${args.component}` }]
        };
      }

      case "save_test_result": {
        const entry = memoryService.saveTestResult(args.description, args.results || {});
        return {
          content: [{ type: "text", text: `🧪 Test sauvegardé : ${args.description}` }]
        };
      }

      case "save_performance_metric": {
        const entry = memoryService.savePerformanceMetric(args.component, args.metrics);
        return {
          content: [{ type: "text", text: `📊 Métrique sauvegardée pour ${args.component}` }]
        };
      }

      // 🔍 SEARCH AND ANALYSIS
      case "search_memory": {
        const results = memoryService.searchMemory(args.query, args.type);
        const summary = `🔍 **Résultats de recherche pour "${args.query}"**\n\n${results.length} résultat(s) trouvé(s):\n\n${results.slice(0, 5).map((result, index) => 
          `${index + 1}. **${result.type}**: ${result.data.content || result.data.description}`
        ).join('\n')}`;
        
        return {
          content: [{ type: "text", text: summary }]
        };
      }
      
      default:
        return {
          content: [{ type: "text", text: `❌ Outil inconnu: ${name}` }]
        };
    }
  } catch (error) {
    return {
      content: [{ type: "text", text: `❌ Erreur: ${error.message}` }]
    };
  }
});

async function main() {
  // Mode test : arrêt automatique après vérification
  if (process.argv.includes('--test')) {
    console.log('🧪 MODE TEST - Serveur MCP mémoire complet...');
    
    try {
      const memory = memoryService.loadMemory();
      console.log(`✅ Mémoire chargée : ${memory.conversations?.length || 0} conversations`);
      console.log(`✅ Projet root détecté : ${memoryService.projectRoot}`);
      console.log(`✅ Fichier mémoire : ${memoryService.memoryFile}`);
      
      // Test de sauvegarde
      const testMemory = memoryService.loadMemory();
      testMemory.conversations.push({
        date: new Date().toISOString(),
        content: 'Test serveur MCP complet avec tous les outils'
      });
      memoryService.saveMemory(testMemory);
      console.log('✅ Sauvegarde testée avec succès');
      
      console.log('🎉 Serveur MCP complet fonctionne correctement !');
      console.log('🛠️ Outils disponibles : save_memory, get_memory, save_bug_fix, save_feature, save_config, save_test_result, save_performance_metric, search_memory');
      process.exit(0);
    } catch (error) {
      console.error('❌ Erreur lors du test :', error.message);
      process.exit(1);
    }
  }
  
  // Mode normal : serveur MCP actif
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('🧠 Intelligent Memory System (Complete) démarré !');
  
  // Gestion propre de l'arrêt
  process.on('SIGINT', () => {
    console.error('🛑 Arrêt du serveur MCP mémoire...');
    process.exit(0);
  });
}

main().catch(console.error);